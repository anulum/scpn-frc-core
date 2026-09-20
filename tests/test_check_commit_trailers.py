# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — commit trailer verifier tests

"""Contract tests for the commit-message trailer guard."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from check_commit_trailers import (
    REQUIRED_AUTHORSHIP_LINE,
    GitAuditError,
    main,
    message_violations,
    range_findings,
)

VALID_MESSAGE = (
    "feat: add configuration policy surface\n\nbody text\n\n"
    f"Seat: rs01\n{REQUIRED_AUTHORSHIP_LINE}\n"
)


def test_valid_message_has_no_violations() -> None:
    """A compliant message passes with no findings."""
    assert message_violations(VALID_MESSAGE) == []


@pytest.mark.parametrize(
    ("message", "fragment"),
    [
        ("feat: x\n\nSeat: rs01\n", "missing required authorship line"),
        (
            (
                f"feat: x\n\nSeat: rs01\n{REQUIRED_AUTHORSHIP_LINE}\n"
                f"{REQUIRED_AUTHORSHIP_LINE}\n"
            ),
            "exactly one authorship line",
        ),
        (f"feat: x\n\n{REQUIRED_AUTHORSHIP_LINE}\n", "missing `Seat:"),
        (
            f"feat: x\n\nSeat: a1\nSeat: b2\n{REQUIRED_AUTHORSHIP_LINE}\n",
            "exactly one `Seat:",
        ),
        (f"feat: x\n\nSeat: !bad!\n{REQUIRED_AUTHORSHIP_LINE}\n", "invalid `Seat:"),
        (
            f"feat: x\n\nSeat: claude-1\n{REQUIRED_AUTHORSHIP_LINE}\n",
            "vendor-prefixed",
        ),
        (
            f"feat: x\n\nSeat: rs01\nextra\n{REQUIRED_AUTHORSHIP_LINE}\n",
            "immediately precede",
        ),
        (
            f"feat: x\n\n{REQUIRED_AUTHORSHIP_LINE}\nSeat: rs01\n",
            "immediately precede",
        ),
        (
            (
                f"feat: x\n\nCo-Authored-By: Someone\nSeat: rs01\n"
                f"{REQUIRED_AUTHORSHIP_LINE}\n"
            ),
            "Co-Authored-By",
        ),
        (
            (
                f"feat: comprehensive robust module\n\nSeat: rs01\n"
                f"{REQUIRED_AUTHORSHIP_LINE}\n"
            ),
            "banned public subject term(s): comprehensive, robust",
        ),
    ],
)
def test_violation_is_reported(message: str, fragment: str) -> None:
    """Each policy breach yields a finding naming the failing rule."""
    findings = message_violations(message)
    assert any(fragment in finding for finding in findings), findings


def test_main_accepts_valid_file(tmp_path: Path) -> None:
    """The hook exits 0 for a compliant commit-message file."""
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text(VALID_MESSAGE, encoding="utf-8")
    assert main([str(path)]) == 0


def test_main_rejects_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The hook exits 1 and names the violations for a bad message."""
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("feat: x\n", encoding="utf-8")
    assert main([str(path)]) == 1
    err = capsys.readouterr().err
    assert "Commit message rejected" in err
    assert "Seat: <seat-id>" in err


def _git(repository: Path, *args: str) -> str:
    """Run ``git`` inside a throwaway repository and return standard output.

    Parameters
    ----------
    repository
        Working tree the command runs in.
    *args
        Arguments after the executable.

    Returns
    -------
    str
        The command's standard output.
    """
    executable = shutil.which("git")
    assert executable is not None, "git is required for the range-audit tests"
    completed = subprocess.run(
        [executable, *args],
        capture_output=True,
        check=True,
        cwd=repository,
        shell=False,
        text=True,
    )
    return completed.stdout


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return a real Git repository with one compliant commit on its branch.

    Parameters
    ----------
    tmp_path
        Pytest-supplied empty directory.
    monkeypatch
        Used to make the repository the process working directory, because the
        guard audits whatever repository it is invoked from.

    Returns
    -------
    pathlib.Path
        The initialised repository root.
    """
    _git(tmp_path, "init", "--quiet", "--initial-branch", "main", str(tmp_path))
    _git(tmp_path, "config", "user.name", "Test Owner")
    _git(tmp_path, "config", "user.email", "owner@example.invalid")
    (tmp_path / "first.txt").write_text("first\n", encoding="utf-8")
    _git(tmp_path, "add", "first.txt")
    _git(tmp_path, "commit", "--quiet", "--no-verify", "-m", VALID_MESSAGE)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _commit(repository: Path, name: str, message: str) -> None:
    """Add one file and commit it with the supplied message.

    Parameters
    ----------
    repository
        Repository to commit into.
    name
        File name to create.
    message
        Full commit message.
    """
    (repository / name).write_text(name, encoding="utf-8")
    _git(repository, "add", name)
    _git(repository, "commit", "--quiet", "--no-verify", "-m", message)


def test_range_findings_empty_for_compliant_history(repository: Path) -> None:
    """A range whose commits all comply yields no findings."""
    _commit(repository, "second.txt", VALID_MESSAGE)
    assert range_findings("HEAD~1..HEAD") == []


def test_range_findings_names_each_failing_commit(repository: Path) -> None:
    """Every non-compliant commit in the range is reported with its short sha."""
    _commit(repository, "second.txt", "feat: no trailers at all\n")
    _commit(repository, "third.txt", VALID_MESSAGE)
    findings = range_findings("HEAD~2..HEAD")
    assert len(findings) == 1
    head_two = _git(repository, "rev-parse", "HEAD~1").strip()
    assert findings[0].startswith(head_two[:12])
    assert "missing required authorship line" in findings[0]


@pytest.mark.usefixtures("repository")
def test_range_findings_covers_an_empty_range() -> None:
    """A range that selects no commit is a pass, not an error."""
    assert range_findings("HEAD..HEAD") == []


@pytest.mark.usefixtures("repository")
@pytest.mark.parametrize("range_spec", ["--all", "-n1", "", "HEAD;rm -rf /"])
def test_range_findings_refuses_an_unsafe_range(range_spec: str) -> None:
    """A range that could be read as an option or a shell string is refused."""
    with pytest.raises(GitAuditError, match="unsafe revision range"):
        range_findings(range_spec)


@pytest.mark.usefixtures("repository")
def test_range_findings_reports_an_unresolvable_range() -> None:
    """A syntactically safe but unresolvable range raises rather than passing."""
    with pytest.raises(GitAuditError, match="rev-list"):
        range_findings("nonexistent-ref..HEAD")


@pytest.mark.usefixtures("repository")
def test_range_findings_requires_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a git executable the audit refuses instead of reporting a pass."""
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    with pytest.raises(GitAuditError, match="git executable not found"):
        range_findings("HEAD~1..HEAD")


def test_main_audit_range_passes(
    repository: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The audit mode exits 0 and names the audited range."""
    _commit(repository, "second.txt", VALID_MESSAGE)
    assert main(["--audit-range", "HEAD~1..HEAD"]) == 0
    assert "Trailer audit passed for HEAD~1..HEAD." in capsys.readouterr().out


def test_main_audit_range_fails(
    repository: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The audit mode exits 1 and lists each failing commit on stderr."""
    _commit(repository, "second.txt", "feat: no trailers at all\n")
    assert main(["--audit-range", "HEAD~1..HEAD"]) == 1
    err = capsys.readouterr().err
    assert "Trailer audit failed for HEAD~1..HEAD:" in err
    assert "missing required authorship line" in err


@pytest.mark.usefixtures("repository")
def test_main_audit_range_reports_infrastructure_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An audit that cannot run exits 2 and says why, rather than passing.

    The range is attached with ``=`` because that is the only way an
    option-shaped value reaches the guard at all: bare ``--audit-range --all``
    is rejected by the argument parser before any policy code runs.
    """
    assert main(["--audit-range=--all"]) == 2
    assert "Trailer audit could not run" in capsys.readouterr().err


def test_main_without_arguments_reports_usage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invoking the guard with neither mode exits 2 and prints usage."""
    assert main([]) == 2
    assert "usage:" in capsys.readouterr().err
