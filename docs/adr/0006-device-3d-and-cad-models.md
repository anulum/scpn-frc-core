<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — ADR 0006
-->

# ADR 0006 — Device 3D and CAD models, on a separatrix that is not a column

Status: accepted (2026-09-04). Adds the fourth and fifth implemented
capabilities, `device_3d_model` and `device_cad_model`, at
`computational_prototype`, and pins the shared kernel library for the
first time in this repository.

## Context

The repository carried a configuration model, diagnostic semantics and
level-0 physics, and no geometry. Every sibling family that has landed a
device model builds its plasma from a cylinder or a tube. An FRC cannot
be built that way.

Its plasma is bounded by a **separatrix**: a closed surface with no hole,
whose radius falls to zero at two poles on the axis. The shape is
published as `r² / a² + |z|^m / b^m = 1` (H. J. Ma et al.,
arXiv:2103.00839v1 (2021), equation 13), so
`r(z) = a·sqrt(1 - |z / b|^m)`, with `a` the midplane radius, `b` the
half-length and `m` a shape index that the source names as `2` for the
ellipse and larger for progressively more racetrack-like.

Drawing that as a cylinder would be a substitute for the part rather than
the part.

## Decision

1. **The library gained the capability rather than this repository
   drawing around the gap.** The profile primitives demanded a strictly
   positive radius at every sample and could not express a body that comes
   to a point; `closed_profiled_solid` and its B-rep twin were added to
   the shared library (kernels ADR 0012) and this family is the first
   consumer of them.

2. **Five bodies in a fixed order**: `plasma_separatrix`,
   `confinement_tube`, `confinement_coil`, `end_wall_upstream`,
   `end_wall_downstream`. The axis is `z` and the origin is the midplane,
   where the separatrix is widest.

3. **One number, one home.** The separatrix radius, the separatrix length
   and the coil bore live in the configuration and are read from there.
   `DeviceGeometry` adds only what the configuration does not carry: the
   confinement tube's bore and wall, the coil's winding thickness and
   axial length, the end-wall thickness, and the shape index. Three
   relations between the two are checked fail-closed before any body is
   built — the plasma inside the tube, the tube inside the bore, the
   separatrix no longer than the coil — each refused in the direction it
   is wrong and naming both fields with their values.

4. **The profile sampling is odd by contract.** An even count has no
   sample at the midplane, so the widest point of the separatrix would not
   be a vertex of the model and the body's radius would depend on where
   the sampling happened to fall. The poles are set to exactly zero rather
   than computed, because the closed-profile contract requires exact
   zeros; the midplane term is taken as exactly zero without calling the
   library, because the transcendental kernel requires a positive normal
   base and `0^m` is not one.

5. **The shape index is admitted from the ellipse upward.** `m = 2` is
   what the source names; below it the model would be extrapolating past
   what the source describes, so it is refused rather than accepted
   silently.

6. **Tier G2 declares a back-end limitation instead of hiding it.** The
   evidence kernel bounds a faceted volume deficit by `2 d / r` at the
   body's smallest circular radius, and the separatrix has none: it falls
   to zero at each pole. The radius passed is the smallest circle the
   tessellation actually carries — the interior sample nearest a pole.

   Separately, and measured while landing this record: the back-end's
   revolution stops reproducing the exact frustum sum when two adjacent
   profile radii come close together. On the reference fixture at 17
   samples the agreement is exact to 2e-16 at `m = 2` and degrades to
   1.6e-4, 5.5e-5, 3.0e-4 and 3.3e-4 at `m = 2.5`, `3`, `4` and `6`. The
   limitation is **not** the closed-profile kernel's and is not new: the
   same numbers come out of the open primitive of kernels ADR 0011 when
   the same shape is lifted off the axis. Tier G1 builds those shapes
   exactly, which is what locates the limitation in the CAD back-end.

   Nothing is tuned to pass. The tier-G2 reference sampling is chosen
   from measurement and says so, and a shape the back-end cannot honour
   is **refused** by the library's evidence kernel, naming the body and
   the bound. Both behaviours are tested.

7. **Anchoring.** The fixtures carry two pairs. The anchor is built from
   the as-built Yingguang-1 hardware Zhu & Wu print in Table I of
   arXiv:2607.11908v1: the coil inner diameter `12.4 cm`, the quartz tube
   radii `5.25 / 5.5 cm`, the active coil length `36 cm`, and eight coils
   of `3.5 cm` on a `4.5 cm` pitch. Each of those is proven recoverable
   **from the built bodies** — vertex coordinates and bounding boxes of
   the meshes and the solids — not from the configuration that fed them.

   The wall thickness is derived from the two printed radii rather than
   written down, because their difference is not the decimal `0.0025` in
   binary; what is exact, and what the test asserts, is that adding it
   back reproduces the printed outer radius.

   The separatrix radius, the separatrix length, the shape index, the
   winding thickness, the end-wall thickness and the external field are
   **declared and said to be declared**. That paper's separatrix radius is
   a simulation result printed as "approximately 1 cm", not a device
   dimension, and is not used.

8. The kernel-library pin is recorded in `pyproject.toml`, in the
   manifest's `kernel_library` block with the inventory digest measured at
   that commit, and proven consistent by a contract test. The CAD extra is
   optional per package and names the same commit.

## Consequences

The family has a device model at both tiers whose plasma is the shape its
own literature publishes. Every relation between the configuration and the
envelope is refused fail-closed, every printed dimension is recoverable
from a built body, and the one place the back-end cannot honour the exact
form is measured, declared and tested rather than avoided.

Nothing here is an equilibrium solution, an engineering model or a
statement about a real machine. Reproducing a printed dimension is an
anchor on the geometry and nothing further.
