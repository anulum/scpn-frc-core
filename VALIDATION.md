<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — VALIDATION
-->

# Validation

Every gate currently active in this repository, with its exact scope,
followed by the evidence record of each implemented capability.

## Local gates

| Gate | Command | Scope |
|---|---|---|
| Lint | `ruff check .` | all Python under `src/`, `tools/`, and `tests/` |
| Format | `ruff format --check .` | same scope |
| Typing | `mypy --strict src tools tests` | zero errors, strict mode |
| Tests + coverage | `pytest -q --cov=src --cov=tools --cov-branch --cov-fail-under=100` | 100 % statement and branch coverage of `src/` and `tools/` |
| Domain manifest | `python3 tools/validate_reactor_domain.py reactor-domain.json` | schema, registry version/digest, exact configuration set, capability inventory shape and ceiling rule, safety boundary |
| Studio descriptor | `python3 tools/derive_studio_descriptor.py --check` | committed descriptor byte-identical to a fresh derivation |
| Capability inventory | `python3 tools/generate_capability_inventory.py --check` | committed inventory byte-identical to a fresh generation |
| Licensing | `reuse lint` | REUSE 3.x compliance of the full tree |
| Workflow lint | `actionlint` | all files under `.github/workflows/` |
| Workflow modularity | `python3 tools/audit_workflows.py` | distributed workflow inventory: single ownership per job, coordinator/gate contract, action pinning, size ceilings |
| Documentation | `python3 tools/preflight.py --only docs` | UTF-8 readability and relative-link integrity of every Markdown file |
| Orchestrated | `python3 tools/preflight.py` | fail-closed run of all gates above |

## Workflow gates

Definitions are present in-repository; they run on the hosted platform
only once a remote exists under separate owner authority.

The hosted surface is modular: `ci.yml` is a coordinator that carries
only trigger policy, two reusable-workflow calls, and one stable
fail-closed `gate` job aggregating every category (failure,
cancellation, and unexpected skips all fail the gate). Every job is
declared and owned exactly once in the versioned inventory
`.github/workflow-inventory.json`, which the workflow-modularity guard
verifies locally and in hosted CI.

| Workflow | Purpose |
|---|---|
| `ci.yml` | coordinator and stable required gate |
| `reusable-static-policy.yml` | lint, format, typing, domain policy, workflow guard |
| `reusable-tests.yml` | tests with complete statement and branch coverage |
| `pre-commit.yml` | exact pre-commit parity |
| `codeql.yml` | Python code scanning |
| `security-audit.yml` | secrets, dependency, licence, and workflow policy |
| `docs.yml` | strict documentation and link validation, no deployment |
| `sbom.yml` | reproducible dependency inventory, no release |
| `scorecard.yml` | read-only supply-chain analysis |

## Shared ecosystem gate

From the monorepo root:

```bash
python3 agentic-shared/scripts/repository_tier0_scaffold_audit.py \
  03_CODE/SCPN-FRC-CORE --json
```

proves the Tier-0 local-scaffold machine profile (required and forbidden
paths, Git/remote boundary, workflow pins and permissions, badge non-claims,
JSON integrity, defensive ignore rules).

## Device configuration model

Evidence record of the `device_configuration_model` capability
(`computational_prototype`; design record: `docs/adr/0002-device-configuration-model.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen parameter objects (`SeparatrixGeometry`,
  `OperationalLimits`, `DeviceConfiguration`) rejecting non-finite
  values, non-positive extents, and a separatrix at or beyond the coil
  radius (the hard `x_s < 1` invariant) — every rejection branch is
  tested.
- The FRC average-beta relation `<beta> = 1 - x_s^2 / 2` (Tuszewski,
  Nucl. Fusion 28 (1988) 2033) as a documented derived quantity.
- Advisory consistency findings with documented bounds, reported and
  never clamped: oblate geometry (elongation below one; FRC equilibria
  are prolate) and a separatrix within five percent of the coil radius.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.
- A data-only pin equality check binding the model to the SPO reactor
  registry version and digest declared in `reactor-domain.json`.

Bounded claims — what is NOT claimed:

- No parameter set describes, approximates, or validates any real
  machine; every exercised parameter set is a synthetic test fixture.
- The estimates are advisory regime checks, not equilibrium, transport,
  or stability results; no benchmark, dataset, solver, controller, or
  experimental correlation exists in this repository.

## Diagnostic and clock semantics

Evidence record of the `diagnostic_clock_semantics` capability
(`computational_prototype`; design record: `docs/adr/0003-diagnostic-clock-semantics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- The nullable `timing_uncertainty_s` member, declared `null` on every
  channel because no event-relative candidate is applicable here; a
  non-null value is refused. This keeps the channel shape identical across
  the portfolio under envelope 1.1.0.
- Validated frozen declaration objects (`ClockModel`,
  `DiagnosticChannelPlan`, `DeferredCandidate`, `DiagnosticPlan`)
  rejecting catalogue misalignment: inapplicable candidates,
  inadmissible carriers, evidence-vocabulary mismatches, incompatible
  clock kinds, Nyquist violations, and incomplete candidate coverage —
  every rejection branch is tested.
- A data-only pin (`ObservabilityBinding`) to the SPO
  observability-profile catalogue release `1.0.0`
  (`d70c0de696534e5a77066ef8420cf7ca17bc4d7321984b0ac83523dbc1dce609`),
  bound in turn to reactor registry `1.0.0`; a plan pinned to any other
  release is rejected.
- A reference plan mirroring canonical practice with synthetic
  declarations: excluded-flux set, interferometer, Mirnov array, synthetic oscillator, each bound to its clock domain.
- A documented advisory band check with its source stated in the code:
  the FRC rotational n=2 instability scale of tens of kHz (Tuszewski 1988); findings are reported, never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.

Bounded claims — what is NOT claimed:

- No channel describes a real diagnostic, measurement, or facility;
  every plan is a synthetic declaration of HOW evidence slots would be
  bound, marked `synthetic=True` by hard invariant.
- No SPO semantic-profile ingress is declared; the profile registry
  `ingress_state` for this device family remains `not_declared`, and
  no adapter, producer, or handoff exists in this repository.

### Portable plan envelope

The `diagnostic_clock_semantics` capability additionally exercises a
producer-owned portable envelope
(`src/scpn_frc_core/plan_envelope.py`,
`scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): one
canonically serialised object carrying the exact project identity and
owned configurations, the capability and its maturity, the
synthetic/review-only/non-actuating statements, both SPO registry pins,
the SHA-256 digest of the inner canonical plan, the producer revision,
and fixed no-observation/no-control non-claims. The committed immutable
fixture (`tests/data/plan_envelope_fixture.json`, byte hash pinned in
the tests) is verified together with positive, tamper, wrong-project,
wrong-configuration, registry-drift, duplicate-member, and non-finite
rejection paths, all under the 100 % coverage gate. The envelope claims
nothing beyond the enveloped synthetic declaration.

### Typed frames, clock relations, and acquisition geometry

The deepened model adds typed reference frames (per-repository allowed
`FrameKind` subset; every noncyclic `coordinate_frame` binding must
reference a declared frame), clock synchronisation relations
(synthetic offset/uncertainty BOUNDS between declared non-simulation
clocks with an explicit method statement — no correlation evidence is
claimed and no clock is mapped to physical wall time), and per-channel
acquisition windows and element counts with device-cited advisory
scales. Both decoders are hardened per the SPO intake architecture:
recursive exact-key refusal in every nested entry, duplicate-member
refusal, and byte-canonical refusal (a document that is not exactly
canonical bytes is rejected). The envelope is `1.1.0`, adding
`manifest_sha256` — the SHA-256 of the committed canonical
`reactor-domain.json` — verified in tests against the committed file.
All declarations remain synthetic; nothing here observes or controls
anything.

### Signal inventories, frame transformations, and clock topology

The depth slice (envelope `1.2.0`; a `1.1.0` document is refused by the
`1.2.0` codec and vice versa — no defaults, no cross-version coercion;
`1.1.0` remains historical custody at the consumer) adds three typed
declaration surfaces, every branch under the 100 % statement-and-branch
gate:

- A per-channel **signal inventory** (`SignalDeclaration`: identifier,
  quantity, unit, role, description). Hard rules: non-empty, unique and
  sorted; exactly one `carrier`; no `timing_marker` (no
  event-relative candidate is applicable); numerical-only
  channels declare a single `phase`/`rad` carrier. Quantity and unit are
  declared tokens — no SI or UCUM validation is performed or claimed —
  and no declaration creates or overrides a candidate, carrier,
  observation, or phase: the candidate profile stays authoritative. An
  advisory flags a multi-element cyclic array without an amplitude
  signal.
- **Frame transformations** (`FrameTransformation`) between declared
  frames: kind admissibility fixed by frame-kind pair (`flux_mapping`
  for machine↔flux, flux↔Boozer, field-line↔machine; `projection` for
  blanket↔machine; `rigid` for chamber↔beamline), `equilibrium_dependent`
  exactly for flux mappings, at most one transformation per frame pair,
  sorted by source then target, and — with two or more frames — a
  connected transformation graph. Methods are declarations;
  `evidence_claimed` is always `False`.
- A **clock topology** (`ClockDomain`, `ClockTopology`): every physical
  clock in exactly one domain, the simulation clock in none; a domain
  holding a facility clock is rooted there, otherwise at its shot-event
  epoch; every non-root member declares a relation to its root; every
  non-reference root declares a relation to the reference root (star);
  relations must not form a cycle. The reference plan declares one
  domain (`clk_facility` root, `clk_shot` member); multi-domain rules
  are exercised by test-constructed plans. Scopes are declarations;
  `mapping_state` stays `unmapped`.

## Level-0 device physics

Evidence record of the `level0_device_physics` capability
(`computational_prototype`; design record: `docs/adr/0005-level0-device-physics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- **Radial pressure balance across the separatrix.** The plasma pressure
  at the field null carries the whole external magnetic pressure,
  `p_max = B_e^2 / 2 mu0`; averaging the balance over the separatrix
  cross-section introduces the average-beta relation
  `<beta> = 1 - x_s^2 / 2` and gives `<p>` and, with a declared particle
  density, the summed electron and ion temperature.
- **The empirical kinetic-scale bound.** `S* = r_s / delta_i` with the ion
  skin depth `delta_i = c / omega_pi`, the elongation `E = l_s / (2 r_s)`,
  their ratio, and whether the ratio sits below the bound `3.5` printed by
  Bala et al. (arXiv:2204.07978v1, equation 14). A test drives two
  configurations that differ only in separatrix length across the bound
  and proves the verdict turns there.
- **The Alfvén speed** of the same operating point, with the ordering
  between a proton and a deuteron plasma tested rather than asserted.
- Every refusal branch: a field, density or ion mass that is zero,
  negative, infinite or not-a-number is refused **naming the field**, and
  nothing is clamped.
- Canonical serialisation (sorted keys, minimal separators, NaN and
  infinity rejected), SHA-256 digest identity, digest stability across two
  compositions, and digest movement when a declared input moves. The
  canonicity test asserts idempotence of the serialisation rather than the
  absence of a comma-space, because the non-claims are prose and contain
  several.

Anchoring — what is printed and what is declared:

- **Printed** by Zhu & Wu (arXiv:2607.11908v1, Table I, as-built
  Yingguang-1 hardware) and reproduced from the built objects: the coil
  inner diameter `12.4 cm`, hence the coil radius `0.062 m`; the active
  coil length `36 cm`; eight coils on a `4.5 cm` pitch; the fill density
  `2e15 cm^-3`; the working ion. Two of these equalities are exact in
  binary and were checked before being written: half of `0.124` is
  `0.062`, and eight times `0.045` is `0.36`.
- **Declared, and said to be declared**: the separatrix radius, the
  separatrix length and the external field of the anchor fixture. That
  paper's separatrix radius is a simulation result printed as
  "approximately 1 cm" — not a device dimension — and is therefore not
  used as an anchor value. The paper prints coil currents, not a field.

Bounded claims — what is NOT claimed:

- No equilibrium, stability, compression or transport equation is solved;
  every number is a closed-form evaluation on a declared operating point.
- The kinetic-scale bound is empirical and orders operating points. A
  configuration inside the bound is **not** claimed stable, and the field
  is named `within_bound` for that reason.
- The split of the total temperature between electrons and ions is not
  modelled and is not claimed.
- No yield, gain, reactivity, confinement or breakeven statement is made,
  and no value describes or validates a real machine. Reproducing a
  number a filed source prints is an anchor on the arithmetic and nothing
  further.

## Device 3D model

Evidence record of the `device_3d_model` capability
(`computational_prototype`; design record: `docs/adr/0006-device-3d-and-cad-models.md`,
contract: `docs/DEVICE_3D_MODEL_CONTRACT.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- **The separatrix as its own published shape**, not a column:
  `r(z) = a sqrt(1 - |z / b|^m)` from Ma et al. (arXiv:2103.00839v1,
  equation 13). The poles are exactly zero and the midplane is exactly
  `(0, a)`, both asserted; the profile increases strictly in `z`; and an
  even sample count is refused because it would leave the widest point of
  the body off the model.
- **The ellipse reproduces its own closed form.** At `m = 2` the body is
  an ellipsoid of revolution; the sampled volume rises monotonically
  towards `4/3 pi a^2 b` and is within 1e-5 of it at 801 samples. The
  bound is measured, not assumed: convergence is not clean second order
  because the ellipse meets the axis with infinite slope, and the measured
  deficits are 3.1e-2, 6.5e-4 and 8.3e-6 at 11, 81 and 801 samples. A
  larger shape index gives a fuller body, which is what "racetrack-like"
  means in the source.
- **Five bodies in a fixed order**, each closed and outward-oriented, the
  plasma inside the tube, the tube inside the coil bore, and the two end
  walls meeting the coil exactly at its ends.
- **Every envelope relation refused in the direction it is wrong**: a
  plasma wider than the tube, a tube wider than the bore, a separatrix
  longer than the coil, an inadmissible segment count, an even or too
  small sample count, and a shape index below the ellipse. Every message
  names the field and its value.
- Canonical serialisation, digest identity, and both input digests bound
  into the record.

Anchoring — what is printed and what is declared:

- **Printed** by Zhu & Wu (arXiv:2607.11908v1, Table I, as-built
  Yingguang-1 hardware) and recovered **from the built bodies**: the
  quartz tube radii `5.25 / 5.5 cm` as vertex coordinates of the tube
  mesh, the coil bore `6.2 cm` as a vertex coordinate of the coil mesh,
  and the active coil length `36 cm` as the coil's bounding-box extent.
  The eight coils on a `4.5 cm` pitch multiply to exactly that length, and
  that equality is exact in binary.
- The tube wall is **derived** from the two printed radii rather than
  written down, because their difference is not the decimal `0.0025` in
  binary. What is exact, and what the test asserts, is that adding it back
  reproduces the printed outer radius.
- **Declared, and said to be declared**: the separatrix radius and length,
  the shape index, the winding thickness, the end-wall thickness and the
  external field. That paper's separatrix radius is a simulation result
  printed as "approximately 1 cm", not a device dimension, and is not used
  as an anchor value.

## Device CAD model

Evidence record of the `device_cad_model` capability
(`computational_prototype`; same design record and contract).

What is exercised:

- The same five bodies as exact solids of revolution, each checked
  fail-closed by the library's evidence kernel: volume and area against
  their analytic closed forms within the measure tolerance, the faceted
  volume within the chord-deficit bound, and the faceted volume against
  the tier-G1 mesh of the same design within the polygon-deficit bound.
- **The separatrix needs no new closed form**: a pole contributes no end
  disc, so its area reference is the lateral sum alone and its volume
  reference the same frustum sum tier G1 uses.
- **The faceting radius excludes the poles.** A pole is a point, not a
  circle; the bound is taken at the smallest circle the tessellation
  actually carries. Taking the pole would divide by zero and taking the
  midplane would assert a bound the body does not satisfy near its ends.
- Canonical record, pinned digest in the pinned back-end environment,
  determinism across two builds, normalised STEP bytes whose digest is
  the digest of the file a caller writes, and refusals for a manifest of
  the wrong schema or body count and for bodies out of order.

Declared limit, measured while landing this capability:

- The back-end's revolution stops reproducing the exact frustum sum when
  two adjacent profile radii come close together. On the reference
  fixture at 17 samples the agreement is exact to 2e-16 at `m = 2` and
  degrades to 1.6e-4, 5.5e-5, 3.0e-4 and 3.3e-4 at `m = 2.5`, `3`, `4`
  and `6`; a deliberately flat-topped polyline with nothing to do with an
  FRC reproduces the same effect.
- **The limitation is the CAD back-end's.** It is not new and not the
  closed-profile kernel's: the open primitive of kernels ADR 0011 shows
  the same numbers when the same shape is lifted off the axis, and tier
  G1 builds those shapes exactly.
- **Nothing is tuned to pass.** The tier-G2 reference sampling is chosen
  from measurement and records the numbers it was chosen from, and a
  shape the back-end cannot honour is refused by the evidence kernel
  naming the body and the bound. Both are tested, including the pairing
  that tier G1 accepts the shape tier G2 refuses.

Bounded claims — what is NOT claimed:

- No body is an equilibrium boundary; the separatrix is a shape function
  evaluated at a declared index and no equilibrium equation is solved.
- STEP determinism is claimed inside one pinned back-end environment
  only, never across back-end versions.
- No engineering model, material property, load, field, neutronic
  quantity or fabrication tolerance is carried, and no value describes or
  validates any real machine.
