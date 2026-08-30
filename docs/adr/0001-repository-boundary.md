<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — ADR 0001: repository boundary
-->

# ADR 0001 — Repository boundary and ownership

**Status:** accepted (2026-08-30)  
**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The SCPN reactor portfolio assigns every built-in configuration of the SCPN
Phase Orchestrator reactor registry (version `1.0.0`, 32 configurations) to
exactly one device-family repository. The FRC is unusual in this portfolio:
an existing project, `SCPN-MIF-CORE`, already owns the pulsed FRC/MIF
merge-compression workflow, its trigger decision, and RTL, while the
canonical FRC solver physics currently lives with the solver owner. The
boundary decision must therefore separate FRC physics truth from the pulsed
integration lifecycle without duplicating either.

## Decision

1. `SCPN-FRC-CORE` owns exactly one registry configuration:
   `field_reversed_configuration` (field-reversed compact toroid).
2. The repository owns FRC device truth: high-beta compact-toroid
   configuration policy, equilibrium/transport/stability parameter
   envelopes and regime identification as device declarations,
   single-FRC lifecycle semantics (formation, translation, sustainment or
   decay, termination), separatrix-relative diagnostic and clock
   declarations, actuator-response boundaries, the safety-envelope
   declaration, and the device-owned CONTROL adapter specification.
3. The pulsed merge/compression workflow, trigger decision, RTL, formal
   timing, and hardware-adjacent evidence remain with `SCPN-MIF-CORE`
   (accepted existing owner; the map assigns it `frc_compression_mif`).
4. Solver mathematics — including the current FRC solver surfaces — stays
   in `SCPN-FUSION-CORE` until an exact surface passes the family
   migration gate; the architecture record names canonical FRC physics as
   a likely future migration into this repository. No solver code is
   copied at scaffold time.
5. Typed semantics remain in `SCPN-PHASE-ORCHESTRATOR` (review-only).
   Admission and `ControlAction` formation remain exclusively in
   `SCPN-CONTROL`. Machine protection remains independent with the final
   veto. Presentation remains in `SCPN-STUDIO`; this project is
   `not_federated`.
6. The repository starts, and remains until evidenced otherwise, at
   `architecture_only` with empty capability and claim inventories.

## Alternatives considered

- **One combined compact-toroid repository** (FRC + spheromak): rejected —
  toroidal-field content, relaxation physics, and formation drivers differ
  on surfaces 1 and 2; the portfolio map separates the owners.
- **Folding FRC physics into `SCPN-MIF-CORE`**: rejected — MIF owns the
  pulsed integration lifecycle; merging device physics into it would
  recreate an undifferentiated container and blur the five-surface rule
  the portfolio standard enforces.
- **Absorbing FUSION's FRC solver code at scaffold time**: rejected —
  violates the migration gate.

## Consequences

- Downstream consumers get one stable identity for FRC physics truth,
  while `SCPN-MIF-CORE` continues to own the merge/compression workflow
  and consumes this repository's declarations rather than duplicating
  them.
- The validator fails on any capability or claim entry while maturity is
  `architecture_only`.
- Boundary changes require a portfolio-level map change first; a future
  ADR records any such change here.
