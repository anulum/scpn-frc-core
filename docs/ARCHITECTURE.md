<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — Architecture
-->

# Architecture

## Purpose and evidence state

`SCPN-FRC-CORE` is the device-family owner for field-reversed configuration
systems in the SCPN Reactor Systems Research Group portfolio. The
repository owns two implemented capabilities at
`computational_prototype` in `src/scpn_frc_core/`: the device
configuration model (design record ADR 0002, evidence record
`VALIDATION.md#device-configuration-model`) and the diagnostic and
clock semantics model (design record ADR 0003, evidence record
`VALIDATION.md#diagnostic-and-clock-semantics`). Every other
section below describes boundaries and contracts. The claim inventory is
empty; capability and claim inventories are generated and drift-checked.

## The five-surface boundary

1. **Governing confinement physics** — the `field_reversed_configuration`
   (field-reversed compact toroid): an elongated, simply connected compact
   toroid confined almost entirely by poloidal field, with negligible
   toroidal field, a closed-field core inside a separatrix embedded in an
   open-field scrape-off region, and volume-averaged beta near unity.
   Stability is shaped by kinetic effects (large ion orbits relative to
   device scale) against the internal tilt and rotational modes. The
   spheromak (comparable toroidal field, Taylor relaxation), theta-pinch
   compression devices, and toroidal-vessel configurations fail this
   sharing test and are excluded.
2. **Primary driver and energy delivery** — formation of the closed-field
   configuration by field-reversed theta-pinch-class programming,
   translation into a confinement chamber where applicable, and
   sustainment by rotating-magnetic-field current drive and neutral-beam
   injection as configuration facets. The pulsed merge/compression
   integration of two FRCs is explicitly not this repository's lifecycle —
   it is the accepted scope of `SCPN-MIF-CORE`.
3. **Plant and shot lifecycle** — shot lifecycle for a single confined
   FRC: formation, translation, confined sustainment or decay, and
   termination, with device-truth records for rotational-mode onset and
   separatrix-volume evolution.
4. **Diagnostic, reference-frame, and clock model** — excluded-flux
   reconstruction conventions, separatrix-relative spatial labels,
   interferometry and magnetics layouts, and pulse-relative clock
   identities resolving formation and translation timescales.
5. **Solver, evidence, and control-contract boundary** — versioned seams
   towards `SCPN-FUSION-CORE` (which currently owns the shared FRC solver
   surfaces), review-only semantics towards `SCPN-PHASE-ORCHESTRATOR`, and
   the device-owned CONTROL adapter specification towards `SCPN-CONTROL`.

## Position in the SCPN ecosystem

```text
SCPN-FRC-CORE (device truth: high-beta compact-toroid policy, lifecycle,
               separatrix diagnostics, safety envelope, adapter spec)
   │  optional versioned solver seams (none active)
   ├──────────────► SCPN-FUSION-CORE      (solver mathematics, evidence)
   │  typed review-only semantics
   ├──────────────► SCPN-PHASE-ORCHESTRATOR (semantics, comparability)
   │  device-owned adapter (specification only; no implementation)
   ├──────────────► SCPN-CONTROL          (admission; sole ControlAction author)
   │  derived portfolio descriptor (not_federated)
   ├──────────────► SCPN-STUDIO           (catalogue, evidence UI, gating)
   │  FRC physics truth consumed by the pulsed merge/compression owner
   └──────────────► SCPN-MIF-CORE         (merge/compression workflow, RTL)

SCPN-CONTROL ──admitted ControlAction──► independent machine protection
                                          (final veto) ─► plant actuators
```

## Repository layout

| Path | Role |
|---|---|
| `reactor-domain.json` | portable source of project identity and contracts |
| `studio/portfolio-descriptor.json` | derived Studio descriptor, `not_federated` |
| `capability-inventory.json` | generated, truthfully empty inventory |
| `docs/CONTROL_ADAPTER_SPECIFICATION.md` | device-owned adapter contract |
| `docs/THREAT_MODEL.md` | assets, trust boundaries, misuse paths |
| `docs/adr/0001-repository-boundary.md` | boundary decision record |
| `tools/` | validators, derivation tools, preflight orchestrator |
| `tests/` | statement- and branch-complete tests for `tools/` |
| `.github/workflows/` | read-only CI definitions (no publication) |

## Contract surfaces and versioning

- `reactor-domain.json` follows schema `scpn.reactor-domain.v1`; unknown
  schemas are rejected by consumers.
- The Studio descriptor is derived deterministically and embeds the
  manifest's SHA-256; manual edits are detected as drift.
- The CONTROL adapter contract is specification-only at `0.1.0-spec`.
- SPO binding is fixed to reactor registry `1.0.0`, digest
  `786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090`.

## What would change this architecture

Acceptance of a FUSION solver seam through the family migration gate — the
architecture record names canonical FRC physics as a likely migration
candidate into this repository, while `SCPN-MIF-CORE` keeps the pulsed
integration and trigger boundary — ratification of an SPO
`ControlIntent`-class contract, or Studio federation after a real
capability passes producer and consumer gates. Each arrives as a
versioned, evidence-bound contract change recorded in a new ADR.
