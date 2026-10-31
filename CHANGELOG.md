<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — CHANGELOG
-->

# Changelog

## [Unreleased]

### Security

- `configuration_from_bytes` refuses duplicate JSON members and any document
  that is not byte-for-byte the canonical serialisation, as the
  diagnostic-plan and plan-envelope parsers already did; a duplicate member
  was resolved last-wins.
- All three public parsers report JSON nested deeper than the decoder can
  follow as their own error type; a `RecursionError` previously escaped
  them. Property and fuzz tests cover arbitrary bytes, single-byte
  mutations, field substitutions and overflowing number literals.

### Fixed

- `build_device_cad` raises `CadUnavailableError` when the optional CAD
  back-end is missing, as documented; it previously re-raised it as
  `DeviceGeometryError`.

### Added

- A level-0 physics benchmark (`benchmarks/level0_physics.py`) per the
  ecosystem benchmark standard, timing the closed forms and the composed
  record on the Python floor, with a committed local artefact, and
  `docs/benchmarks.md` stating the computation contract of every kernel and
  the backend status: Python floor only, the decision on a native backend
  open with the project owner. `benchmarks/` joins the typed cohort and the
  enrolled surfaces.

- README badge block for the evidence this repository has earned: the CI,
  CodeQL, pre-commit, security-audit and docs workflows on `main`, the
  AGPL-3.0-or-later licence, the commercial licence route and GitHub
  Sponsors, bound by a contract test; unearned services stay forbidden.
- An installed-wheel job in the required CI gate: the wheel is built
  without build isolation from hash-locked `setuptools` and `wheel`
  (`requirements-build.txt`), installed into clean base and CAD environments
  and exercised from outside the checkout by `tools/installed_package_check.py`.

### Changed

- Source citations match the filed pages: the `4.5 cm` coil pitch is printed
  in the text of Zhu & Wu (p. 9), not in their Table I, and the average-beta
  relation, cited to a review that is not freely available, now says so and
  names the filed paper that uses the same factor. No value changes.

- The physical constants name their edition: the vacuum permeability, the
  vacuum permittivity and both ion masses are CODATA 2018 values (each
  differs from CODATA 2022 by about `1e-9` relative or less); the elementary
  charge and the speed of light are exact SI values. No value changes; tests
  bind each edition and offset.

- `scpn_frc_core.observability` is now a package with one module per
  responsibility — vocabulary, catalogue binding, frames, clocks, signals and
  channels, plan composition, record parsing — behind the unchanged public
  import path. The 33 public names, canonical plan bytes and refusal
  behaviour are unchanged.

- The documentation gate reads only files git would publish, so a
  git-ignored private tree is never link-checked (it failed the gate locally
  while passing in CI, where that tree is absent). Hooks without their own
  stage list run before a commit and before a push only; commit-msg runs the
  trailer guard alone.
- Local and hosted gates check the same cohorts: `make typecheck` now checks
  `src/` as CI does, `make test` measures `src/` as CI does, `conftest.py`
  joins the typed cohort everywhere, and `make validate` runs the workflow
  audit. A parity test binds the make targets and the preflight plan to the
  hosted workflows, and an enrollment test maps every tracked file to exactly
  one gated surface.

- Install every CI dependency from hash-locked requirement sets with
  `--require-hashes`: the development toolchain, the CAD extra, the audit
  and inventory tools, and the first-party kernel library by source-archive
  digest at the commit pinned in `pyproject.toml`. `make lock` regenerates
  the sets; the package itself installs with `--no-deps`. Toolchain, action
  and interpreter pins move to their newest releases.

### Added

- Commit-trailer guard: `--audit-range REVISION_RANGE` applies the commit
  message policy to commits that already exist, exiting `0` for a compliant
  range, `1` naming each failing commit, and `2` when the audit cannot run.
  The range must be a safe literal, `git` is resolved to an absolute path and
  invoked without a shell, and history is only ever read. It is an operator
  command rather than a gate, because commits written before the hook existed
  cannot retroactively satisfy it.

- Diagnostic-plan depth: per-channel signal inventories, frame
  transformations with a fixed kind-admissibility table and connectivity
  rule, and a clock topology partitioning the physical clocks into rooted
  domains with a star of relations to the reference root. Envelope
  `scpn.reactor-diagnostic-plan-envelope.v1` bumped to `1.2.0`; the
  fixture is regenerated from the public surface and re-pinned. All new
  members are declarations: no observation, phase, mapping, or control
  authority is created.

### Fixed

- Added the nullable `timing_uncertainty_s` channel member (always `null`;
  no event-relative candidate is applicable) so the diagnostic-plan
  channel shape matches the portfolio-uniform envelope 1.1.0 contract;
  fixture regenerated and re-pinned.

### Added

- Local gate parity with the wider ecosystem: the pre-commit chain now
  also runs REUSE licensing compliance and a typographical checker
  (`_typos.toml` carries the deliberate reactor vocabulary), and adds
  the upstream YAML, TOML, large-file and private-key guards. Licensing
  and spelling were previously verified only in hosted CI, so a broken
  REUSE annotation — including the aggregate annotation that covers the
  binary header images — could reach a push before being caught.
- Generated repository header artwork: `docs/assets/generate_header.py`
  renders three deterministic 1280x640 images from the repository's own
  domain surface (the prolate FRC in its confinement coil used by the
  README, the average-beta relation, and the prolate geometry flag).
- Modular hosted-workflow surface per the ecosystem workflow-modularity
  standard: `ci.yml` reduced to a coordinator with a stable fail-closed
  `gate` job, single-responsibility reusable workflows for static
  analysis/repository policy and for tests, a versioned machine-readable
  inventory (`.github/workflow-inventory.json`,
  `scpn.workflow-inventory.v1` `1.0.0`), and a fail-closed modularity
  guard (`tools/audit_workflows.py`) enforced locally (preflight gate,
  pre-commit hook) and in hosted CI. The duplicate documentation-links
  step was removed from the CI chain; `docs.yml` remains the single
  owner of documentation validation.

- Typed reference frames, clock synchronisation relations (synthetic
  bounds only; no correlation evidence claimed), and per-channel
  acquisition windows and element counts in the diagnostic model;
  hardened decoders (recursive exact-key, duplicate-member, and
  byte-canonical refusal in both codecs); envelope `1.1.0` adding
  `manifest_sha256` over the committed canonical `reactor-domain.json`
  (fixture regenerated; byte hash re-pinned in tests).

- Portable diagnostic-plan envelope
  (`src/scpn_frc_core/plan_envelope.py`,
  `scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): a
  producer-owned, canonically serialised wrapper carrying project
  identity, exact owned configurations, capability and maturity,
  synthetic/review-only/non-actuating statements, both SPO registry
  pins, the inner plan's SHA-256, the producer revision, and fixed
  no-observation/no-control non-claims; strict parsers refuse unknown,
  duplicate, and non-finite members, and an immutable committed fixture
  exercises the exchange end to end.

- Diagnostic and clock semantics model
  (`src/scpn_frc_core/observability.py`), the second implemented
  capability at `computational_prototype`: frozen clock, channel,
  deferral, and plan objects aligned fail-closed with the pinned SPO
  observability-profile catalogue (candidate applicability, carrier
  admissibility, exact class-fixed evidence vocabularies, clock-kind
  compatibility, Nyquist bounds); a cited advisory band check; canonical
  serialisation with SHA-256 digests and strict NaN-rejecting round-trip
  parsing (design record `docs/adr/0003-diagnostic-clock-semantics.md`).

- Device configuration model (`src/scpn_frc_core/`), the first implemented
  capability at `computational_prototype`: validated frozen parameter
  objects with device-specific invariants and documented, cited
  consistency estimates; canonical serialisation with SHA-256 digests
  and strict NaN-rejecting round-trip parsing; a data-only pin to the
  SPO reactor registry; and the reactor-domain validator branch
  enforcing populated capability inventories with the ADR 0002
  evidence-maturity ceiling rule (design record
  `docs/adr/0002-device-configuration-model.md`).

- Architecture-only repository scaffold: governance, security, licensing,
  REUSE metadata, contribution and support policies, and citation metadata.
- Machine-readable domain manifest `reactor-domain.json` binding the project
  to SCPN Phase Orchestrator reactor registry `1.0.0`
  (configuration `field_reversed_configuration`).
- Device-owned CONTROL adapter specification and threat model.
- Derived Studio portfolio descriptor (`not_federated`) and generated
  capability inventory (zero implemented capabilities).
- Validation tooling: domain-manifest validator, descriptor derivation and
  inventory generation with drift checks, and a fail-closed preflight
  orchestrator, each with statement- and branch-complete tests.
- Continuous-integration, code-scanning, security-audit, documentation,
  SBOM, pre-commit, and Scorecard workflow definitions (read-only
  permissions; no publication or deployment workflows).

### Changed

- Studio portfolio descriptor schema ratified at version 1.1.0 after
  downstream review, before any consumer adoption (1.0.0 superseded
  unconsumed): canonical JSON Schema published in-repository with a strict
  unknown-field policy, explicit source repository, nullable lifecycle
  evidence pointer, nullable versioned control-intent reference, ratified
  capability item shape, and a machine-protection object (independent
  final-veto owner with availability `not_assessed`) replacing the former
  boolean flag.
