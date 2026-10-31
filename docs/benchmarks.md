<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — Benchmarks and computation contract
-->

# Benchmarks and computation contract

## Computation contract

The level-0 physics of this package is a set of closed forms evaluated in
IEEE-754 binary64 on the Python floor:

| Kernel | Inputs (SI) | Output | Operations |
|---|---|---|---|
| `magnetic_pressure_pa` | field `B` (T), finite, positive | `B^2 / 2 mu0` (Pa) | `* /` |
| `alfven_speed_m_s` | field (T), particle density (m^-3), ion mass (kg), each finite and positive | `B / sqrt(mu0 n m_i)` (m/s) | `* /`, `sqrt` |
| `ion_plasma_frequency_rad_s` | particle density, ion mass | `sqrt(n e^2 / (eps0 m_i))` (rad/s) | `* /`, `sqrt` |
| `ion_skin_depth_m` | particle density, ion mass | `c / omega_pi` (m) | `/`, via the frequency |
| `radial_pressure_balance` | validated configuration, particle density | peak and average pressure, average beta, temperature | `+ - * /` |
| `kinetic_scale_bound` | validated configuration, particle density, ion mass | `S* / E` against the published bound | `* /`, via the skin depth |
| `level0_physics` | validated configuration, `ModelInputs` | canonical record with SHA-256 digest | composition of the above, JSON serialisation |

Every input outside its domain is refused with the package error, never
clamped. No kernel uses a transcendental function other than the square
root, which IEEE-754 requires to be correctly rounded, so any conforming
backend that keeps the operation order reproduces every value bit for bit.
The constants and their editions are documented in the modules and bound by
tests.

**Backend status.** Python floor only. There is no native crate: the
kernels are a few multiplications, divisions and square roots, and the
measurement below puts a complete composed record at tens of microseconds
on the floor. Audit plan Q01 asks for a native path on required numeric
paths and allows a scoped, owner-approved exception for trivial non-hot
arithmetic; that decision is the owner's and is recorded as open in the
backlog. The benchmark marks the native backend as unavailable instead of
omitting it.

## Level-0 physics — local workstation (non-isolated)

Artefact: `benchmarks/results/level0_physics.local.json` (schema
`scpn-frc-core.level0-physics-benchmark.v1`, generated 2026-10-31T01:32:16.002518+00:00, at commit
`f4d2d0a5bd80` with the working tree of the landing commit).
Host: 11th Gen Intel(R) Core(TM) i5-11600K @ 3.90GHz, Linux-7.0.0-34-generic-x86_64-with-glibc2.39, Python 3.12.3; load average
at start 2.17; cores not isolated (shared
workstation, so treat the numbers as a smoke timing, not a performance
measurement). Parameters: 20000 closed-form points and
2000 records, 3 warm-up passes, 20 timed passes.

### `closed_forms` (magnetic pressure, Alfvén speed, ion skin depth per point)

| Backend | P50 µs/point | P95 µs/point | P99 µs/point | mean µs/point | throughput points/s | status |
|---|---|---|---|---|---|---|
| `python_floor` (public API) | 0.601 | 0.762 | 0.863 | 0.631 | 1664845 | measured |
| `rust_native` | — | — | — | — | — | unavailable: no native crate |

### `level0_record` (composed record with canonical bytes per point)

| Backend | P50 µs/record | P95 µs/record | P99 µs/record | mean µs/record | throughput records/s | status |
|---|---|---|---|---|---|---|
| `python_floor` (public API) | 24.343 | 25.876 | 30.508 | 24.370 | 41079 | measured |
| `rust_native` | — | — | — | — | — | unavailable: no native crate |

## Regenerate

```bash
.venv/bin/python benchmarks/level0_physics.py --label local
```

The script writes `benchmarks/results/level0_physics.<label>.json` with the
provenance above. A number from a fixed CI runner or isolated cores would
replace the smoke timing here; none is claimed yet.
