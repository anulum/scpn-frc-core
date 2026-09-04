<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — ADR 0005
-->

# ADR 0005 — Level-0 device physics: radial pressure balance and the empirical kinetic-scale bound

Status: accepted (2026-09-04). Adds the third implemented capability,
`level0_device_physics`, at `computational_prototype`.

## Context

Until this record the repository carried no physics beyond the average-beta
property of the configuration model. That property cited M. Tuszewski,
Nucl. Fusion 28 (1988) 2033, and the repository's source ledger recorded
that the review is behind a subscription and could not be filed. A cited
relation whose source cannot be opened is a relation nobody in this
repository can check.

Searching for the family rather than for the citation settled it. Three
freely available papers carry what the review was cited for, and all three
are now filed with their digests:

- **Zhu & Wu, arXiv:2607.11908v1 (2026)** — a whole-device kinetic model of
  the Yingguang-1 formation experiment, whose Table I prints the as-built
  hardware and the operating point.
- **Ma, Xie, Deng, Bai, Cheng, Li, Chen, Tuszewski, Zhao & Liu,
  arXiv:2103.00839v1 (2021)** — a two-dimensional FRC equilibrium study,
  co-authored by the author of the paywalled review.
- **Bala, Zhu, Li et al., arXiv:2204.07978v1 (2022)** — quasi-static
  magnetic compression, carrying the average-beta and elongation scalings
  and the empirical stability criterion with its printed bound.

## Decision

1. The package implements **two** closed forms and no more, each traceable
   to a filed source.

   **Radial pressure balance.** An FRC is held by a poloidal field alone.
   The field passes through a null inside the separatrix, so at the null
   the plasma pressure carries the whole external magnetic pressure:
   `p_max = B_e^2 / 2 mu0`. Averaging the balance over the separatrix
   cross-section introduces the average beta the configuration model
   already carries, `<beta> = 1 - x_s^2 / 2`, giving
   `<p> = <beta> B_e^2 / 2 mu0` and, with a declared particle density, the
   summed electron and ion temperature `<p> / (n e)`. The split between
   species is not modelled and is not claimed.

   **The empirical kinetic-scale bound.** An FRC is formally unstable to
   the internal tilt mode in ideal magnetohydrodynamics and experiments
   nevertheless hold configurations together. The separation is ordered by
   how few ion gyro-scales fit across the plasma. The package reports
   `S* = r_s / delta_i` with `delta_i = c / omega_pi`, the elongation
   `E = l_s / (2 r_s)`, their ratio, and whether the ratio sits below the
   published bound `3.5` (Bala et al., equation 14).

2. **The bound is reported, never predicted from.** A configuration inside
   the bound is not claimed stable. The record says so in its non-claims,
   and the field is named `within_bound` rather than anything that reads
   as a verdict on the machine.

3. **No transcendental enters.** Both relations need square roots only,
   and the IEEE-754 square root is correctly rounded and therefore
   bit-identical on every conforming platform. The shared kernel library
   is not pinned by this record; it will be pinned when the device model
   needs the axial-profile primitive, whose exponent is a genuine
   transcendental.

4. **Anchoring.** The fixtures carry two pairs. The reference pair is
   synthetic and round. The anchor pair is built from what Zhu & Wu print:
   the coil inner diameter `12.4 cm`, the active coil length `36 cm`, the
   eight coils on a `4.5 cm` pitch, the fill density `2e15 cm^-3` and the
   working ion. Two of the anchor's equalities are exact in binary and
   were checked before they were written: half of `0.124` is `0.062`, and
   eight times `0.045` is `0.36`.

   The separatrix radius that paper prints is a **simulation result**
   given as "approximately 1 cm", not a device dimension, and is therefore
   not an anchor value. The separatrix radius and length of the anchor
   fixture, and the external field, are declared and are said to be
   declared, in the fixture docstring and in `VALIDATION.md`.

5. The record is schema-tagged `scpn.frc-level0-physics.v1`, serialises
   canonically with a SHA-256 digest, binds the digest of the
   configuration it was built from, and carries its non-claims in the
   record itself rather than only in prose.

## Consequences

The repository now has a physics capability of its own, bounded to two
closed forms whose sources any reader can open. Every refusal names the
field that is wrong and its value; nothing is clamped.

The average-beta relation is no longer cited to a source this repository
cannot produce. The citation in `parameters.py` stays, because the review
is where the relation is from; what changes is that the repository can now
also point at filed papers that carry it.

Nothing here claims stability, confinement, yield or performance, and no
value describes a real machine. Reproducing a printed number is an anchor
on the arithmetic and nothing further.
