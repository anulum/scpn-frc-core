# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — tier-G1 device model

"""Tier-G1 tessellated model of a field-reversed-configuration device.

Five bodies in a fixed order: the plasma separatrix, the confinement tube
it sits inside, the confinement coil around that, and the two end walls.

The separatrix is the reason this tier needed a library increment. It is
not a column: it is a closed surface that comes to a point on the axis at
each pole, published as ``r^2 / a^2 + |z|^m / b^m = 1`` (H. J. Ma et al.,
arXiv:2103.00839v1 (2021), equation 13), so
``r(z) = a sqrt(1 - |z / b|^m)``. Drawing it as a cylinder would be a
substitute for the part rather than the part, so the shared library gained
``closed_profiled_solid`` (kernels ADR 0012) and this tier is built on it.

The axis is ``z``, the origin is the midplane, and the separatrix is
symmetric about it. Every length comes from the validated configuration or
the validated geometry; nothing is invented here and every relation
between them is checked fail-closed before a body is built.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_reactor_kernels.errors import GeometryError, NumericsError
from scpn_reactor_kernels.geometry import (
    TriangleMesh,
    annular_tube,
    closed_profiled_solid,
    cylinder_solid,
    require_segments,
)
from scpn_reactor_kernels.numerics.transcendental import power

from scpn_frc_core.configuration import DeviceConfiguration
from scpn_frc_core.errors import DeviceGeometryError
from scpn_frc_core.geometry.device import DeviceGeometry

MODEL_SCHEMA: Final = "scpn.frc-3d-model.v1"
MODEL_SCHEMA_VERSION: Final = "1.0.0"
MODEL_UNITS: Final = {
    "length": "metre",
    "handedness": "right",
    "axis": "z along the axis of the confinement coil",
    "origin": "z = 0 at the midplane, where the separatrix is widest",
}
MODEL_NON_CLAIMS: Final = (
    "analytic surfaces tessellated from a synthetic configuration and geometry",
    (
        "the separatrix is the published shape function evaluated at a "
        "declared shape index; it is not an equilibrium solution and no "
        "equilibrium equation is solved"
    ),
    (
        "the open field region outside the separatrix, the scrape-off layer "
        "and the coil segmentation are not modelled at this tier"
    ),
    "no body is a CAD solid or an engineering model",
    "no material property, load, field or neutronic quantity is carried",
    "no value describes or validates any real machine",
)

ROLE_PLASMA: Final = "plasma"
ROLE_VACUUM_BOUNDARY: Final = "vacuum_boundary"
ROLE_COIL: Final = "coil"
ROLE_STRUCTURE: Final = "structure"
MATERIAL_PLASMA: Final = "plasma"
MATERIAL_TUBE_WALL: Final = "tube_wall"
MATERIAL_COIL_CONDUCTOR: Final = "coil_conductor"
MATERIAL_END_WALL: Final = "end_wall"

BODY_PLASMA_SEPARATRIX: Final = "plasma_separatrix"
BODY_CONFINEMENT_TUBE: Final = "confinement_tube"
BODY_CONFINEMENT_COIL: Final = "confinement_coil"
BODY_END_WALL_UPSTREAM: Final = "end_wall_upstream"
BODY_END_WALL_DOWNSTREAM: Final = "end_wall_downstream"
BODY_NAMES: Final = (
    BODY_PLASMA_SEPARATRIX,
    BODY_CONFINEMENT_TUBE,
    BODY_CONFINEMENT_COIL,
    BODY_END_WALL_UPSTREAM,
    BODY_END_WALL_DOWNSTREAM,
)

#: Fewest profile samples the separatrix may be built from: the two poles
#: and the midplane.
MIN_PROFILE_SAMPLES: Final = 3


def require_profile_samples(samples: int) -> int:
    """Validate the sample count of the separatrix profile.

    Parameters
    ----------
    samples
        Number of ``(z, radius)`` samples across the whole separatrix.

    Returns
    -------
    int
        The validated count.

    Raises
    ------
    DeviceGeometryError
        If the count is below :data:`MIN_PROFILE_SAMPLES` or is even. An
        even count has no sample at the midplane, so the widest point of
        the separatrix would not be a vertex of the model and the body's
        radius would depend on where the sampling happened to fall.
    """
    if isinstance(samples, bool) or samples < MIN_PROFILE_SAMPLES:
        raise DeviceGeometryError(
            f"profile_samples: must be at least {MIN_PROFILE_SAMPLES}, got {samples!r}"
        )
    if samples % 2 == 0:
        raise DeviceGeometryError(
            f"profile_samples: must be odd so the midplane is a sample, got {samples!r}"
        )
    return samples


def separatrix_profile(
    midplane_radius_m: float,
    half_length_m: float,
    shape_index: float,
    samples: int,
) -> tuple[tuple[float, float], ...]:
    """Sample the published separatrix shape function.

    Evaluates ``r(z) = a sqrt(1 - |z / b|^m)`` at equally spaced heights
    from ``-b`` to ``+b``.

    The two poles are set to exactly zero rather than computed, because
    that is what they are: at ``|z| = b`` the shape function is exactly
    zero, and the closed-profile contract requires the ends to be exactly
    zero rather than nearly so. The midplane term is likewise taken as
    exactly zero without calling the library, because the transcendental
    kernel requires a positive normal base and ``0^m`` is not one.

    Parameters
    ----------
    midplane_radius_m
        The separatrix radius ``a`` at the midplane; strictly positive.
    half_length_m
        Half the separatrix length, ``b``; strictly positive.
    shape_index
        The exponent ``m``; at least two.
    samples
        Odd count of samples across the whole separatrix.

    Returns
    -------
    tuple of (float, float)
        The profile, strictly increasing in ``z``, zero at both ends.

    Raises
    ------
    DeviceGeometryError
        If the sample count is invalid, or if the shape function leaves
        the transcendental kernel's admissible range (the kernel's
        refusal is re-raised under the device error type with its
        message).
    """
    require_profile_samples(samples)
    last = samples - 1
    profile: list[tuple[float, float]] = [(-half_length_m, 0.0)]
    for index in range(1, last):
        fraction = 2.0 * index / last - 1.0
        height = half_length_m * fraction
        normalised = abs(fraction)
        if normalised == 0.0:
            term = 0.0
        else:
            try:
                term = power(normalised, shape_index)
            except NumericsError as exc:
                raise DeviceGeometryError(str(exc)) from exc
        profile.append((height, midplane_radius_m * math.sqrt(1.0 - term)))
    profile.append((half_length_m, 0.0))
    return tuple(profile)


@dataclass(frozen=True, slots=True)
class DeviceModel3D:
    """The tessellated device model of one configuration and geometry.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the configuration the model was built from.
    geometry_digest_sha256
        Digest of the geometry the model was built from.
    segments
        Circumferential segment count every body was tessellated at.
    profile_samples
        Sample count the separatrix profile was built from.
    meshes
        The five bodies in the fixed order of :data:`BODY_NAMES`.

    Raises
    ------
    DeviceGeometryError
        If the body names or their order differ from :data:`BODY_NAMES`.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    segments: int
    profile_samples: int
    meshes: tuple[TriangleMesh, ...]

    def __post_init__(self) -> None:
        """Validate the body set and its order.

        Raises
        ------
        DeviceGeometryError
            If the body names or their order differ from
            :data:`BODY_NAMES`.
        """
        names = tuple(mesh.name for mesh in self.meshes)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"meshes: bodies must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            The schema-tagged record with one entry per body.
        """
        return {
            "schema": MODEL_SCHEMA,
            "schema_version": MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "segments": self.segments,
            "profile_samples": self.profile_samples,
            "bodies": [
                {
                    "name": mesh.name,
                    "role": mesh.role,
                    "material_identifier": mesh.material_identifier,
                    "vertex_count": mesh.vertex_count,
                    "face_count": mesh.face_count,
                    "volume_m3": mesh.signed_volume_m3(),
                    "surface_area_m2": mesh.surface_area_m2(),
                }
                for mesh in self.meshes
            ],
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the model record canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact model record.

        Returns
        -------
        str
            SHA-256 of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _require_envelope(
    configuration: DeviceConfiguration, geometry: DeviceGeometry
) -> None:
    """Refuse a configuration and geometry that do not fit together.

    Parameters
    ----------
    configuration
        Validated device configuration.
    geometry
        Validated mechanical envelope.

    Raises
    ------
    DeviceGeometryError
        If the plasma does not fit inside the tube, the tube does not fit
        inside the coil bore, or the separatrix is longer than the coil.
        Each refusal names the two fields and their values.
    """
    separatrix_radius = configuration.geometry.separatrix_radius_m
    if separatrix_radius >= geometry.confinement_tube_inner_radius_m:
        raise DeviceGeometryError(
            "separatrix_radius_m: must be strictly smaller than "
            f"confinement_tube_inner_radius_m ({separatrix_radius!r} >= "
            f"{geometry.confinement_tube_inner_radius_m!r})"
        )
    coil_radius = configuration.geometry.coil_radius_m
    if geometry.confinement_tube_outer_radius_m >= coil_radius:
        raise DeviceGeometryError(
            "confinement_tube_outer_radius_m: must be strictly smaller than "
            f"coil_radius_m ({geometry.confinement_tube_outer_radius_m!r} >= "
            f"{coil_radius!r})"
        )
    separatrix_length = configuration.geometry.separatrix_length_m
    if separatrix_length > geometry.coil_length_m:
        raise DeviceGeometryError(
            "separatrix_length_m: must not exceed coil_length_m "
            f"({separatrix_length!r} > {geometry.coil_length_m!r})"
        )


def build_device_model(
    configuration: DeviceConfiguration,
    geometry: DeviceGeometry,
    segments: int,
    profile_samples: int,
) -> DeviceModel3D:
    """Tessellate the five bodies of a validated design.

    Parameters
    ----------
    configuration
        Validated FRC configuration; it fixes the separatrix radius, the
        separatrix length and the coil bore.
    geometry
        Validated mechanical envelope.
    segments
        Circumferential segments for every body; at least 8, multiple
        of 8.
    profile_samples
        Odd count of samples across the separatrix.

    Returns
    -------
    DeviceModel3D
        The composed model.

    Raises
    ------
    DeviceGeometryError
        If the segment count or the sample count is invalid, or if the
        configuration and the geometry do not fit together. The library's
        refusals from the two contracts this function applies itself —
        the segment count and the profile — are re-raised under the device
        error type with their messages.

    Notes
    -----
    The body constructors below are not wrapped. Every argument they
    receive has its precondition established before the call: the tube's
    outer radius exceeds its inner one because the wall is positive, the
    coil's likewise, each axial pair is ordered because the coil length
    and the end-wall thickness are positive, the profile came from
    :func:`separatrix_profile`, and the segment count has already passed
    the library's own contract. A translation layer there could not run,
    and an unreachable one would have to be excused rather than tested.
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    require_profile_samples(profile_samples)
    _require_envelope(configuration, geometry)
    separatrix_radius = configuration.geometry.separatrix_radius_m
    half_length = configuration.geometry.separatrix_length_m / 2.0
    profile = separatrix_profile(
        separatrix_radius,
        half_length,
        geometry.separatrix_shape_index,
        profile_samples,
    )
    coil_half = geometry.coil_length_m / 2.0
    coil_inner = configuration.geometry.coil_radius_m
    tube_inner = geometry.confinement_tube_inner_radius_m
    tube_outer = geometry.confinement_tube_outer_radius_m
    wall = geometry.end_wall_thickness_m
    bodies = (
        (
            BODY_PLASMA_SEPARATRIX,
            ROLE_PLASMA,
            MATERIAL_PLASMA,
            closed_profiled_solid(profile, segments),
        ),
        (
            BODY_CONFINEMENT_TUBE,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_TUBE_WALL,
            annular_tube(tube_inner, tube_outer, -coil_half, coil_half, segments),
        ),
        (
            BODY_CONFINEMENT_COIL,
            ROLE_COIL,
            MATERIAL_COIL_CONDUCTOR,
            annular_tube(
                coil_inner,
                coil_inner + geometry.coil_wall_thickness_m,
                -coil_half,
                coil_half,
                segments,
            ),
        ),
        (
            BODY_END_WALL_UPSTREAM,
            ROLE_STRUCTURE,
            MATERIAL_END_WALL,
            cylinder_solid(tube_outer, -coil_half - wall, -coil_half, segments),
        ),
        (
            BODY_END_WALL_DOWNSTREAM,
            ROLE_STRUCTURE,
            MATERIAL_END_WALL,
            cylinder_solid(tube_outer, coil_half, coil_half + wall, segments),
        ),
    )
    meshes = tuple(
        TriangleMesh(
            name=name,
            role=role,
            material_identifier=material,
            vertices=vertices,
            faces=faces,
        )
        for name, role, material, (vertices, faces) in bodies
    )
    return DeviceModel3D(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        segments=segments,
        profile_samples=profile_samples,
        meshes=meshes,
    )
