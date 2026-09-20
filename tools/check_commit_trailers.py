# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — commit trailer verifier

"""Validate commit-message trailers as the ``commit-msg`` hook or over a range.

The hook receives the pending commit-message file path and rejects messages
without exactly one required authorship line and exactly one vendor-neutral
``Seat:`` trailer immediately preceding it, messages carrying the superseded
``Co-Authored-By:`` trailer, and commit subjects containing outward-facing
self-praise terms.

``--audit-range`` applies the same policy to an explicit Git revision range, so
an operator can ask what a set of already-written commits contains. It reports;
it never rewrites history, and a failing audit of old commits is a finding
rather than a demand to rebase.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

REQUIRED_AUTHORSHIP_LINE: Final = (
    "Authored by Anulum Fortis & Arcane Sapience (protoscience@anulum.li)"
)
LEGACY_COAUTHOR_RE: Final = re.compile(r"^\s*Co-Authored-By:", re.IGNORECASE)
SEAT_PREFIX_RE: Final = re.compile(r"^\s*Seat:")
SEAT_TRAILER_RE: Final = re.compile(r"^Seat:\s+([A-Za-z0-9][A-Za-z0-9_-]{0,63})\s*$")
FORBIDDEN_SEAT_PREFIXES: Final = (
    "claude-",
    "codex-",
    "gemini-",
    "grok-",
    "kimi-",
    "openai-",
)
BANNED_SUBJECT_RE: Final = re.compile(
    r"\b(world-class|best-in-class|state-of-the-art|cutting-edge|revolutionary"
    r"|groundbreaking|unrivalled|elite|comprehensive|robust|leveraging)\b",
    re.IGNORECASE,
)
SAFE_RANGE_RE: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@^~{}-]*$")


class GitAuditError(RuntimeError):
    """Raised when the range audit cannot be performed at all."""


def _subject_line(message: str) -> str:
    """Return the first non-empty commit-message line.

    Parameters
    ----------
    message
        Full commit-message text.

    Returns
    -------
    str
        The stripped subject line, or an empty string.
    """
    return next((line.strip() for line in message.splitlines() if line.strip()), "")


def _seat_violations(lines: list[str], authorship_indices: list[int]) -> list[str]:
    """Return validation errors for the ``Seat:`` trailer.

    Parameters
    ----------
    lines
        Commit-message lines.
    authorship_indices
        Indexes of lines equal to the required authorship line.

    Returns
    -------
    list[str]
        Violations; empty when the trailer is valid.
    """
    seat_indices = [i for i, line in enumerate(lines) if SEAT_PREFIX_RE.match(line)]
    if not seat_indices:
        return ["missing `Seat: <seat-id>` trailer"]
    if len(seat_indices) != 1:
        return ["expected exactly one `Seat: <seat-id>` trailer"]
    seat_index = seat_indices[0]
    match = SEAT_TRAILER_RE.match(lines[seat_index].strip())
    if match is None:
        return ["invalid `Seat: <seat-id>` trailer"]
    violations: list[str] = []
    seat_id = match.group(1).lower()
    if seat_id.startswith(FORBIDDEN_SEAT_PREFIXES):
        violations.append("vendor-prefixed `Seat:` trailer is forbidden")
    if len(authorship_indices) == 1:
        authorship_index = authorship_indices[0]
        between = lines[seat_index + 1 : authorship_index]
        if seat_index >= authorship_index or any(line.strip() for line in between):
            violations.append(
                "`Seat:` trailer must immediately precede the authorship line"
            )
    return violations


def message_violations(message: str) -> list[str]:
    """Return commit-message policy violations.

    Parameters
    ----------
    message
        Full commit-message text.

    Returns
    -------
    list[str]
        Empty when the message satisfies the local agent commit policy.
    """
    lines = message.splitlines()
    violations: list[str] = []
    authorship_indices = [
        i for i, line in enumerate(lines) if line.strip() == REQUIRED_AUTHORSHIP_LINE
    ]
    if not authorship_indices:
        violations.append("missing required authorship line")
    elif len(authorship_indices) != 1:
        violations.append("expected exactly one authorship line")
    violations.extend(_seat_violations(lines, authorship_indices))
    if any(LEGACY_COAUTHOR_RE.match(line) for line in lines):
        violations.append("legacy `Co-Authored-By:` trailer is forbidden")
    banned = sorted(
        {m.group(1).lower() for m in BANNED_SUBJECT_RE.finditer(_subject_line(message))}
    )
    if banned:
        violations.append(f"banned public subject term(s): {', '.join(banned)}")
    return violations


def _git(*args: str) -> str:
    """Run one fixed ``git`` argument vector and return its standard output.

    Parameters
    ----------
    *args
        Arguments after the executable. Each is a separate argument vector
        element, so no value is ever interpreted by a shell.

    Returns
    -------
    str
        The command's standard output.

    Raises
    ------
    GitAuditError
        If ``git`` is not on the path or the command exits non-zero.
    """
    executable = shutil.which("git")
    if executable is None:
        raise GitAuditError("git executable not found on PATH")
    completed = subprocess.run(
        [executable, *args],
        capture_output=True,
        check=False,
        shell=False,
        text=True,
    )
    if completed.returncode != 0:
        raise GitAuditError(
            f"`git {' '.join(args)}` failed: {completed.stderr.strip()}"
        )
    return completed.stdout


def range_findings(range_spec: str) -> list[str]:
    """Return one finding per non-compliant commit in a Git revision range.

    Parameters
    ----------
    range_spec
        A Git revision range such as ``origin/main..HEAD``. A value that could
        be read as a command-line option is refused rather than passed on.

    Returns
    -------
    list[str]
        ``"<short sha>: <violations>"`` for each failing commit, in the order
        ``git rev-list`` reports them. Empty when every commit complies.

    Raises
    ------
    GitAuditError
        If the range is not a safe literal, ``git`` is unavailable, or the
        range cannot be resolved.
    """
    if not SAFE_RANGE_RE.match(range_spec):
        raise GitAuditError(f"unsafe revision range: {range_spec!r}")
    revisions = _git("rev-list", range_spec).splitlines()
    shas = [line.strip() for line in revisions if line.strip()]
    findings: list[str] = []
    for sha in shas:
        violations = message_violations(_git("log", "-1", "--format=%B", sha))
        if violations:
            findings.append(f"{sha[:12]}: {'; '.join(violations)}")
    return findings


def _audit_range(range_spec: str) -> int:
    """Audit a revision range and report the outcome on standard output.

    Parameters
    ----------
    range_spec
        The Git revision range to audit.

    Returns
    -------
    int
        ``0`` when every commit complies, ``1`` when any commit does not, and
        ``2`` when the audit could not be performed.
    """
    try:
        findings = range_findings(range_spec)
    except GitAuditError as error:
        print(f"Trailer audit could not run: {error}", file=sys.stderr)
        return 2
    if not findings:
        print(f"Trailer audit passed for {range_spec}.")
        return 0
    print(f"Trailer audit failed for {range_spec}:", file=sys.stderr)
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)
    return 1


def _audit_message_file(message_file: Path) -> int:
    """Validate one pending commit-message file.

    Parameters
    ----------
    message_file
        Path supplied by the ``commit-msg`` hook.

    Returns
    -------
    int
        ``0`` when the message complies, ``1`` when it does not.
    """
    violations = message_violations(message_file.read_text(encoding="utf-8"))
    if not violations:
        return 0
    print("Commit message rejected:", file=sys.stderr)
    for violation in violations:
        print(f"  - {violation}", file=sys.stderr)
    print("Required block:\n  Seat: <seat-id>", file=sys.stderr)
    print(f"  {REQUIRED_AUTHORSHIP_LINE}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    """Run the commit-trailer guard in hook or range-audit mode.

    Parameters
    ----------
    argv
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        ``0`` when validation passes, ``1`` for policy violations, and ``2``
        when the invocation is incomplete or the audit cannot be performed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "message_file",
        nargs="?",
        type=Path,
        help="commit-message file supplied by the commit-msg hook",
    )
    parser.add_argument(
        "--audit-range",
        metavar="REVISION_RANGE",
        help="audit an existing Git revision range instead of a pending message",
    )
    args = parser.parse_args(argv)
    if args.audit_range is not None:
        return _audit_range(args.audit_range)
    if args.message_file is None:
        parser.print_usage(sys.stderr)
        return 2
    return _audit_message_file(args.message_file)


if __name__ == "__main__":
    sys.exit(main())
