<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — ROADMAP
-->

# Roadmap

Planned work and implemented capability are kept strictly separate. Anything
listed under "Planned" carries no implementation, no code, and no claim in
this repository until it appears in the capability inventory with evidence.

## Implemented (repository infrastructure, not reactor capability)

- Domain manifest (`reactor-domain.json`) with validator.
- Derived Studio portfolio descriptor (`not_federated`) with drift check.
- Generated capability inventory (truthfully empty) with drift check.
- CONTROL adapter specification (contract only, no implementation).
- Local and workflow gate definitions (lint, typing, tests, coverage,
  REUSE, security audit, SBOM, documentation checks).

- **Device configuration model** (landed 2026-08-31) — validated
  separatrix/coil geometry and operational-limit objects for
  `field_reversed_configuration` with the hard `x_s = r_s/r_c < 1`
  invariant, the average-beta relation `<beta> = 1 - x_s^2/2`
  (Tuszewski 1988), prolateness and wall-proximity advisories, canonical
  digests, and the SPO registry data pin; `computational_prototype`
  (ADR 0002, `VALIDATION.md#device-configuration-model`).
  Formation-method classes and sustainment inventory remain future work
  under the same capability.
- **Diagnostic and clock semantics** (landed 2026-08-31) — synthetic
  diagnostic-channel and clock declarations aligned fail-closed with the
  pinned SPO observability-profile catalogue (release `1.0.0`): candidate
  applicability, carrier admissibility, exact evidence vocabularies,
  clock-kind compatibility, Nyquist bounds, canonical digests; the
  reference plan mirrors canonical practice (excluded-flux set, interferometer, Mirnov array, synthetic oscillator);
  `computational_prototype` (ADR 0003,
  `VALIDATION.md#diagnostic-and-clock-semantics`). No ingress is
  declared; the SPO semantic-profile state remains `not_declared`.

## Planned (no implementation exists; ordering is not a commitment)
1. **Safety-envelope declaration** — machine-readable operational envelope
   (bank energies, density and mode margins) consumed by the CONTROL
   adapter contract.
2. **CONTROL adapter implementation** — device-owned adapter against the
   published specification, with replay fixtures and HIL evidence,
   targeting `control_research_ready` only after replay and HIL
   acceptance.
3. **Solver seam consumption and physics migration** — versioned
   consumption of exact `SCPN-FUSION-CORE` FRC seams; the architecture
   record names canonical FRC physics as a likely migration into this
   repository strictly through the family migration gate, while
   `SCPN-MIF-CORE` keeps the pulsed integration and trigger boundary.
4. **Facility-data correlation** — preregistered acceptance contracts
   against identified facility or published experimental data, targeting
   `experiment_correlated` per capability.

## Not planned in this repository

The pulsed FRC/MIF merge-compression workflow, trigger, and RTL
(`SCPN-MIF-CORE`); spheromaks; theta-pinch compression devices; tokamak and
stellarator systems; inertial systems; mirrors; electrostatic devices;
generic controller mathematics; machine-protection logic; any direct
actuation path.
