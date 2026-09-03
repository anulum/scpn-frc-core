# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — repository header artwork generator

"""Generate the three README header images (1280x640) for this repository.

Every image is original generated artwork derived from this repository's
own domain surface — the prolate separatrix inside its confinement coil,
the average-beta relation the configuration model validates, and the
prolate-versus-oblate geometry flag. The right-hand text panel states
only facts backed by the repository itself.

Outputs (written next to this script):

- ``repo_header.png`` — the prolate FRC inside its theta-pinch coil
  with X-points and open outer field lines (used by ``README.md``).
- ``repo_header_beta_relation.png`` — the average-beta versus
  separatrix-ratio curve with the hard wall and the proximity flag.
- ``repo_header_prolate_invariant.png`` — prolate accepted, oblate
  flagged.

Generation-time tooling only: requires ``numpy`` and ``matplotlib``,
which are deliberately not part of the pinned development lock. Run as
``python3 docs/assets/generate_header.py`` from the repository root.
The output is deterministic (fixed geometry, no random input).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

OUT_DIR = Path(__file__).resolve().parent

BG = "#00050a"
CYAN = "#00ccff"
MAGENTA = "#ff00ff"
STEEL = "#334466"
PROBE = "#66aaff"
RED = "#ff3366"
GREEN = "#3ddc84"

WIDTH_IN, HEIGHT_IN, DPI = 12.8, 6.4, 100

TITLE_METRICS: list[tuple[str, str]] = [
    ("Device Configuration", "field_reversed_configuration"),
    ("Hard Invariant", "x_s < 1 · separatrix inside the coil"),
    ("Average Beta", "⟨β⟩ = 1 - x_s²/2 (Tuszewski 1988)"),
    ("Geometry Flags", "oblate · separatrix within 5% of coil"),
    ("Plan Envelope", "v1.1.0 · synthetic · review-only"),
    ("Quality Gates", "100% branch cov · mypy --strict"),
]


def _pyplot() -> Any:
    """Return pyplot configured for headless Agg rendering."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _glow_cmap() -> Any:
    """Build the family glow colormap (deep navy to cyan)."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "scpn_glow",
        ["#00050a", "#001428", "#002d55", "#005588", "#0088bb", "#00ccff"],
    )


def _text_panel(fig: Any, subtitle: str) -> None:
    """Draw the family right-hand text panel onto ``fig``."""
    ax = fig.add_axes([0.62, 0.0, 0.38, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.08,
        0.84,
        "SCPN",
        color="white",
        fontsize=36,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.74,
        "FRC CORE",
        color="white",
        fontsize=34,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.66,
        subtitle,
        color=CYAN,
        fontsize=11,
        fontfamily="monospace",
        alpha=0.85,
    )
    ax.plot([0.08, 0.85], [0.615, 0.615], color=STEEL, lw=0.8, alpha=0.5)
    y = 0.55
    for label, value in TITLE_METRICS:
        ax.text(
            0.08,
            y,
            f"▸ {label}",
            color="#6688aa",
            fontsize=9,
            fontfamily="monospace",
            alpha=0.9,
        )
        ax.text(
            0.10,
            y - 0.030,
            value,
            color="#99bbdd",
            fontsize=8,
            fontfamily="monospace",
            alpha=0.7,
        )
        y -= 0.072
    ax.text(
        0.08,
        0.06,
        "© 1996–2026 Miroslav Šotek",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.6,
    )
    ax.text(
        0.08,
        0.03,
        "anulum.li | AGPL-3.0",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.5,
    )


def _art_axes(fig: Any) -> Any:
    """Return the borderless left-hand art axes of ``fig``."""
    ax = fig.add_axes([0.0, 0.0, 0.68, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def _save(fig: Any, plt: Any, name: str) -> None:
    """Save ``fig`` to ``name`` inside the assets directory and close it."""
    target = OUT_DIR / name
    fig.savefig(target, dpi=DPI, facecolor=BG, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"generated {target}")


def racetrack(
    centre_x: float,
    centre_z: float,
    half_length: float,
    radius: float,
    samples: int = 500,
) -> tuple[Any, Any]:
    """Return a racetrack-like prolate separatrix outline."""
    theta = np.linspace(0.0, 2.0 * np.pi, samples)
    x = centre_x + half_length * np.sign(np.cos(theta)) * np.abs(np.cos(theta)) ** 0.62
    z = centre_z + radius * np.sign(np.sin(theta)) * np.abs(np.sin(theta)) ** 0.85
    return x, z


def generate_device_section() -> None:
    """Generate ``repo_header.png``: the prolate FRC inside its coil."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-2.6, 2.6)

    grid_x = np.linspace(1.2, 8.8, 260)
    grid_z = np.linspace(-1.35, 1.35, 120)
    mesh_x, mesh_z = np.meshgrid(grid_x, grid_z)
    rho = np.sqrt(((mesh_x - 5.0) / 3.4) ** 2 + (mesh_z / 1.05) ** 2)
    ax.contourf(
        mesh_x,
        mesh_z,
        np.exp(-rho * 2.4),
        levels=30,
        cmap=_glow_cmap(),
        alpha=0.85,
    )

    for rail_z in (+2.0, -2.0):
        ax.plot([0.7, 9.3], [rail_z, rail_z], color=STEEL, lw=3.0, alpha=0.8)
    for coil_x in np.linspace(0.95, 9.05, 14):
        for rail_z in (+2.0, -2.0):
            ax.plot([coil_x], [rail_z], "s", color=MAGENTA, ms=5, alpha=0.75)
    ax.text(
        5.0,
        2.22,
        "confinement coil · r_c",
        color="#667799",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    surfaces = [
        (1.0, 2.2, 0.95),
        (0.74, 0.8, 0.42),
        (0.5, 0.8, 0.42),
        (0.27, 0.8, 0.42),
    ]
    for fraction, lw, alpha in surfaces:
        x, z = racetrack(5.0, 0.0, 3.55 * fraction, 1.18 * fraction)
        ax.plot(x, z, color=CYAN, lw=lw, alpha=alpha)
    ax.plot(
        [5.0 - 2.35, 5.0 + 2.35],
        [0, 0],
        ".",
        color=MAGENTA,
        ms=5,
        alpha=0.9,
    )

    for line_z in (1.55, 1.78, -1.55, -1.78):
        xs = np.linspace(0.7, 9.3, 300)
        bulge = np.exp(-(((xs - 5.0) / 2.9) ** 2))
        ax.plot(
            xs,
            line_z - np.sign(line_z) * 0.28 * bulge,
            color=PROBE,
            lw=0.8,
            alpha=0.5,
        )

    for end_x in (5.0 - 3.55, 5.0 + 3.55):
        ax.plot(end_x, 0, "x", color=RED, ms=8, mew=1.8, alpha=0.95)
    ax.text(
        5.0 + 3.42,
        -0.38,
        "X-point",
        color=RED,
        fontsize=7.5,
        fontfamily="monospace",
        ha="right",
        alpha=0.9,
    )

    ax.annotate(
        "",
        xy=(5.0, 1.18),
        xytext=(5.0, 0.0),
        arrowprops={"arrowstyle": "->", "color": "white", "lw": 1.0, "alpha": 0.6},
    )
    ax.text(
        5.12,
        0.55,
        "r_s",
        color="white",
        fontsize=8,
        fontfamily="monospace",
        alpha=0.75,
    )

    ax.text(
        5.0,
        -2.35,
        "purely poloidal field · closed core, open exhaust ends",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "Prolate Compact Toroid, No Toroidal Field")
    _save(fig, plt, "repo_header.png")


def generate_beta_relation() -> None:
    """Generate ``repo_header_beta_relation.png``: beta versus x_s."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    ax.plot([1.0, 9.2], [1.7, 1.7], color=STEEL, lw=1.0, alpha=0.7)
    ax.plot([1.0, 1.0], [1.7, 9.1], color=STEEL, lw=1.0, alpha=0.7)
    ax.text(
        8.85,
        1.25,
        "x_s = r_s / r_c",
        color="#8899bb",
        fontsize=9.5,
        fontfamily="monospace",
        ha="right",
    )
    ax.text(
        1.15,
        8.85,
        "⟨β⟩",
        color="#8899bb",
        fontsize=11,
        fontfamily="monospace",
    )

    ratio = np.linspace(0.0, 1.0, 300)
    beta = 1.0 - ratio**2 / 2.0
    px = 1.0 + 8.0 * ratio
    py = 1.7 + 6.9 * (beta - 0.4) / 0.6
    ax.plot(px, py, color=CYAN, lw=2.6, alpha=0.95)
    ax.fill_between(px, py, 1.7, color=CYAN, alpha=0.05)

    for level in (1.0, 0.75, 0.5):
        level_y = 1.7 + 6.9 * (level - 0.4) / 0.6
        ax.plot([1.0, 9.0], [level_y, level_y], color=STEEL, lw=0.5, alpha=0.3)
        ax.text(
            0.9,
            level_y,
            f"{level:.2f}",
            color="#556677",
            fontsize=7.5,
            fontfamily="monospace",
            ha="right",
            va="center",
        )

    ax.plot([9.0, 9.0], [1.7, 9.1], color=RED, lw=2.0, alpha=0.9)
    ax.text(
        8.88,
        5.3,
        "x_s < 1 · HARD",
        color=RED,
        fontsize=8.5,
        fontfamily="monospace",
        ha="right",
        rotation=90,
        alpha=0.95,
    )

    ax.fill_between([1.0 + 8.0 * 0.95, 9.0], 1.7, 9.1, color=RED, alpha=0.10)
    ax.text(
        1.0 + 8.0 * 0.955,
        2.1,
        "flag",
        color="#ff8899",
        fontsize=7.5,
        fontfamily="monospace",
        rotation=90,
        alpha=0.9,
    )

    mark_x = 1.0 + 8.0 * 0.6
    mark_y = 1.7 + 6.9 * ((1 - 0.18) - 0.4) / 0.6
    ax.plot(mark_x, mark_y, "o", color=MAGENTA, ms=6, alpha=0.95)
    ax.text(
        mark_x + 0.15,
        mark_y + 0.25,
        "high-beta regime",
        color=MAGENTA,
        fontsize=8.5,
        fontfamily="monospace",
        alpha=0.95,
    )

    ax.text(
        5.0,
        0.75,
        "average beta follows the separatrix ratio · Tuszewski, "
        "Nucl. Fusion 28 (1988) 2033",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "Beta Bound To Geometry, Checked")
    _save(fig, plt, "repo_header_beta_relation.png")


def generate_prolate_invariant() -> None:
    """Generate ``repo_header_prolate_invariant.png``: the geometry flag."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-3.2, 3.2)

    grid_x = np.linspace(0.7, 4.3, 140)
    grid_z = np.linspace(-2.2, 2.2, 140)
    mesh_x, mesh_z = np.meshgrid(grid_x, grid_z)
    rho = np.sqrt(((mesh_x - 2.5) / 0.85) ** 2 + (mesh_z / 1.9) ** 2)
    ax.contourf(
        mesh_x,
        mesh_z,
        np.exp(-rho * 2.4),
        levels=24,
        cmap=_glow_cmap(),
        alpha=0.8,
    )
    prolate = [(1.0, 2.0, 0.95), (0.66, 0.7, 0.4), (0.36, 0.7, 0.4)]
    for fraction, lw, alpha in prolate:
        x, z = racetrack(2.5, 0.0, 0.95 * fraction, 2.05 * fraction)
        ax.plot(x, z, color=CYAN, lw=lw, alpha=alpha)
    ax.text(
        2.5,
        2.6,
        "prolate · E > 1",
        color=GREEN,
        fontsize=9,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
    )
    ax.text(
        2.5,
        -2.62,
        "ACCEPTED · prolate geometry",
        color="#445566",
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
    )

    oblate = [(1.0, 2.0, 0.8), (0.62, 0.7, 0.35)]
    for fraction, lw, alpha in oblate:
        x, z = racetrack(7.25, 0.0, 1.62 * fraction, 0.80 * fraction)
        ax.plot(x, z, color="#8899aa", lw=lw, alpha=alpha)
    ax.plot([6.15, 8.35], [-1.25, 1.25], color=RED, lw=2.2, alpha=0.85)
    ax.plot([6.15, 8.35], [1.25, -1.25], color=RED, lw=2.2, alpha=0.85)
    ax.text(
        7.25,
        2.6,
        "oblate · E < 1",
        color=RED,
        fontsize=9,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
    )
    ax.text(
        7.25,
        -2.62,
        "FLAGGED by the configuration model",
        color="#445566",
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
    )

    ax.plot([5.0, 5.0], [-2.4, 2.4], color=STEEL, lw=0.8, alpha=0.4)
    ax.text(
        5.0,
        -3.0,
        "elongation E = separatrix length / (2 · separatrix radius)",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "Prolate Enforced, Oblate Flagged")
    _save(fig, plt, "repo_header_prolate_invariant.png")


if __name__ == "__main__":
    generate_device_section()
    generate_beta_relation()
    generate_prolate_invariant()
