<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN FRC Core — device model contract
-->

# Device model contract

What a consumer of this repository's device models may rely on, written
from the code rather than from a template. Design record:
`docs/adr/0006-device-3d-and-cad-models.md`.

## The two tiers

| Tier | Record | Schema | Built from |
|---|---|---|---|
| G1, tessellated | `DeviceModel3D` | `scpn.frc-3d-model.v1` 1.0.0 | the library's `geometry` group |
| G2, B-rep | `DeviceModelCAD` | `scpn.frc-cad-model.v1` 1.0.0 | the library's `cad` group |

Both are built from the same validated `DeviceConfiguration` and
`DeviceGeometry` and describe the same five bodies. Tier G2 is optional:
it needs the `cad` extra, and every other capability of this package works
without a B-rep back-end.

## Units and frame

| Quantity | Value |
|---|---|
| length | metre |
| handedness | right |
| axis | `z` along the axis of the confinement coil |
| origin | `z = 0` at the midplane, where the separatrix is widest |

## The bodies, in this order

| Name | Role | Material token |
|---|---|---|
| `plasma_separatrix` | `plasma` | `plasma` |
| `confinement_tube` | `vacuum_boundary` | `tube_wall` |
| `confinement_coil` | `coil` | `coil_conductor` |
| `end_wall_upstream` | `structure` | `end_wall` |
| `end_wall_downstream` | `structure` | `end_wall` |

The order is fixed and checked at construction on both tiers. A record
whose bodies are reordered or renamed is refused, not sorted.

## Where each dimension comes from

The configuration owns the separatrix radius `a`, the separatrix length
`2b` and the coil bore. The geometry owns the confinement tube's bore and
wall, the coil's winding thickness and axial length, the end-wall
thickness and the separatrix shape index. Neither repeats the other, and
three relations between them are checked before any body is built:

- the separatrix radius is strictly smaller than the tube bore;
- the tube's outer radius is strictly smaller than the coil bore;
- the separatrix is no longer than the coil.

Each is refused in the direction it is wrong, naming both fields and their
values. Nothing is clamped.

## The separatrix

`r(z) = a·sqrt(1 - |z / b|^m)`, the published shape function
(Ma et al., arXiv:2103.00839v1, equation 13). It is sampled at an **odd**
count of equally spaced heights so the midplane is a sample and the widest
point of the body is a vertex of the model. The two poles are exactly
zero, so the body closes on the axis; the library builds it with one apex
vertex per pole rather than a degenerate ring.

The shape index is admitted from `2` — the ellipse the source names —
upward.

## Exports and identity

Both records serialise canonically (sorted keys, minimal separators, a
trailing newline, NaN and infinity refused) and carry a SHA-256 digest of
those bytes. Each binds the digests of the configuration and the geometry
it was built from. Tier G2 additionally carries normalised STEP bytes with
their own digest and the versions of the pinned back-ends.

## Declared limits

- **STEP determinism is claimed inside one pinned back-end environment
  only**, never across back-end versions. The record carries the versions.
- **The back-end's revolution has a measured limit.** It stops reproducing
  the exact frustum sum when two adjacent profile radii come close
  together; on the reference fixture at 17 samples the agreement is exact
  at `m = 2` and degrades to between 5e-5 and 3e-4 at `m = 2.5` through
  `6`. The limitation belongs to the CAD back-end, not to this repository
  and not to the closed-profile kernel: tier G1 builds the same shapes
  exactly, and the open primitive shows the same numbers. A body the
  back-end cannot honour is **refused** by the library's evidence kernel,
  naming the body and the bound it missed.
- The faceting deficit of the separatrix is bounded at the smallest circle
  the tessellation actually carries. A pole is a point, not a circle.

## Non-claims

- No body is an equilibrium boundary. The separatrix is the published
  shape function evaluated at a declared index; no equilibrium equation is
  solved.
- The open field region outside the separatrix, the scrape-off layer and
  the coil segmentation are not modelled.
- No body is an engineering model; no material property, load, field,
  neutronic quantity or fabrication tolerance is carried.
- No value describes or validates any real machine. Where a record
  reproduces a dimension a filed source prints, that is an anchor on the
  geometry and nothing further.
