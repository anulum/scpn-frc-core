# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — tier-G2 device model

"""Tier-G2 B-rep model of a field-reversed-configuration device.

The same five bodies as tier G1, built as exact solids of revolution
through the shared library's ``cad`` group instead of tessellated, with
every body checked fail-closed by the library's evidence kernel against
its analytic closed forms and against its tier-G1 twin, and exported as
normalised STEP bytes with a digest.

The separatrix is again the body that needed the library to grow: it
closes on the axis at both poles, which the open profile primitive cannot
express (kernels ADR 0012).

Two quantities are this repository's to choose and are chosen here rather
than inherited.

The first is the reference sampling of the separatrix, which is coarser
than tier G1 may use because the back-end's revolution has a measured
limit; see :data:`DEFAULT_REFERENCE_PROFILE_SAMPLES`.

The second is the radius that bounds the faceting deficit. The evidence
kernel bounds a body's faceted volume deficit by
``2 d / r`` at the body's smallest circular radius, and the separatrix has
no smallest circular radius: it falls to zero at each pole. The radius
passed for it is the **smallest circle the tessellation actually carries**,
which is the interior profile sample nearest a pole. Passing the pole
radius would be a division by zero, and passing the midplane radius would
be a bound the body does not satisfy near its ends.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_reactor_kernels.cad import (
    MANIFEST_SCHEMA,
    BodyEvidence,
    BrepAssembly,
    annular_tube_brep,
    assembly_evidence,
    backend_versions,
    closed_profiled_solid_brep,
    cylinder_solid_brep,
    facet_assembly,
    step_bytes,
    step_sha256,
)
from scpn_reactor_kernels.errors import CadError, GeometryError
from scpn_reactor_kernels.geometry import TriangleMesh

from scpn_frc_core.configuration import DeviceConfiguration
from scpn_frc_core.errors import DeviceGeometryError
from scpn_frc_core.geometry.device import DeviceGeometry
from scpn_frc_core.geometry.model import (
    BODY_CONFINEMENT_COIL,
    BODY_CONFINEMENT_TUBE,
    BODY_END_WALL_DOWNSTREAM,
    BODY_END_WALL_UPSTREAM,
    BODY_NAMES,
    BODY_PLASMA_SEPARATRIX,
    MATERIAL_COIL_CONDUCTOR,
    MATERIAL_END_WALL,
    MATERIAL_PLASMA,
    MATERIAL_TUBE_WALL,
    ROLE_COIL,
    ROLE_PLASMA,
    ROLE_STRUCTURE,
    ROLE_VACUUM_BOUNDARY,
    build_device_model,
    separatrix_profile,
)

CAD_MODEL_SCHEMA: Final = "scpn.frc-cad-model.v1"
CAD_MODEL_SCHEMA_VERSION: Final = "1.0.0"
CAD_MODEL_UNITS: Final = {
    "length": "metre",
    "handedness": "right",
    "axis": "z along the axis of the confinement coil",
    "origin": "z = 0 at the midplane, where the separatrix is widest",
}
CAD_MODEL_NON_CLAIMS: Final = (
    "exact solids of revolution of a synthetic configuration and geometry",
    (
        "the separatrix is the published shape function revolved at a "
        "declared shape index; it is not an equilibrium solution"
    ),
    (
        "determinism of the STEP bytes is claimed within one pinned back-end "
        "environment only, never across back-end versions"
    ),
    "no body is an engineering model and no fabrication tolerance is carried",
    "no material property, load, field or neutronic quantity is carried",
    "no value describes or validates any real machine",
)

#: Reference tessellation the B-rep bodies are checked against.
DEFAULT_REFERENCE_MESH_SEGMENTS: Final = 8
#: Reference profile sampling of the separatrix comparison. Coarser than
#: tier G1 may use, and the reason is measured rather than assumed: the
#: back-end's revolution stops reproducing the exact frustum sum when two
#: adjacent profile radii come close together, and finer sampling of a
#: separatrix brings them closer. For the anchor's shape the agreement is
#: exact to 4e-16 up to 29 samples and breaks at 33, where it jumps to
#: 6e-5 — far outside the library's measure tolerance of 1e-9. This value
#: sits inside that range with room to spare. Nothing is hidden by it: a
#: sampling or a shape the back-end cannot honour is refused by the
#: library's evidence kernel, naming the body and the bound.
DEFAULT_REFERENCE_PROFILE_SAMPLES: Final = 21
#: Mesher deflections of the faceting comparison.
DEFAULT_LINEAR_DEFLECTION_M: Final = 1.0e-4
DEFAULT_ANGULAR_DEFLECTION_RAD: Final = 0.1


@dataclass(frozen=True, slots=True)
class DeviceModelCAD:
    """The B-rep device model of one configuration and geometry.

    Parameters
    ----------
    configuration_digest_sha256, geometry_digest_sha256
        Digests of the inputs the model was built from.
    reference_mesh_segments, reference_profile_samples
        Tier-G1 reference the bodies were checked against.
    linear_deflection_m, angular_deflection_rad
        Mesher deflections of the faceting comparison.
    backend_versions
        Versions of the pinned back-ends that produced the solids.
    assembly_manifest
        The library's assembly manifest of the five bodies.
    step_sha256
        Digest of the normalised STEP bytes.
    bodies
        Checked evidence of each body, in the fixed order.
    step_data
        The normalised STEP bytes themselves.
    faceted_meshes
        The faceted meshes the evidence was computed from.

    Raises
    ------
    DeviceGeometryError
        If the manifest schema, the body count or the body order is wrong.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    reference_mesh_segments: int
    reference_profile_samples: int
    linear_deflection_m: float
    angular_deflection_rad: float
    backend_versions: dict[str, str]
    assembly_manifest: dict[str, Any]
    step_sha256: str
    bodies: tuple[BodyEvidence, ...]
    step_data: bytes
    faceted_meshes: tuple[TriangleMesh, ...]

    def __post_init__(self) -> None:
        """Validate the manifest and the body set.

        Raises
        ------
        DeviceGeometryError
            If the manifest schema, the body count or the body order is
            wrong.
        """
        if self.assembly_manifest.get("schema") != MANIFEST_SCHEMA:
            raise DeviceGeometryError(
                f"assembly_manifest.schema: must be {MANIFEST_SCHEMA!r}"
            )
        if self.assembly_manifest.get("body_count") != len(BODY_NAMES):
            raise DeviceGeometryError(
                f"assembly_manifest.body_count: must be {len(BODY_NAMES)}, got "
                f"{self.assembly_manifest.get('body_count')!r}"
            )
        names = tuple(body.name for body in self.bodies)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"bodies: must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            The schema-tagged record with one entry per body.
        """
        return {
            "schema": CAD_MODEL_SCHEMA,
            "schema_version": CAD_MODEL_SCHEMA_VERSION,
            "units": dict(CAD_MODEL_UNITS),
            "non_claims": list(CAD_MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "reference_mesh_segments": self.reference_mesh_segments,
            "reference_profile_samples": self.reference_profile_samples,
            "linear_deflection_m": self.linear_deflection_m,
            "angular_deflection_rad": self.angular_deflection_rad,
            "backend_versions": dict(self.backend_versions),
            "assembly_manifest": self.assembly_manifest,
            "step_sha256": self.step_sha256,
            "bodies": [body.to_record() for body in self.bodies],
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


def smallest_tessellated_radius_m(profile: tuple[tuple[float, float], ...]) -> float:
    """Return the smallest circle a closed profile actually carries.

    The poles are points, not circles, so they are excluded: what bounds
    the faceting deficit is the narrowest ring the body is built from.

    Parameters
    ----------
    profile
        A closed profile: zero at both ends, positive between them.

    Returns
    -------
    float
        The smallest interior radius.
    """
    return min(radius for _, radius in profile[1:-1])


def build_device_cad(
    configuration: DeviceConfiguration,
    geometry: DeviceGeometry,
    segments: int = DEFAULT_REFERENCE_MESH_SEGMENTS,
    profile_samples: int = DEFAULT_REFERENCE_PROFILE_SAMPLES,
    linear_deflection_m: float = DEFAULT_LINEAR_DEFLECTION_M,
    angular_deflection_rad: float = DEFAULT_ANGULAR_DEFLECTION_RAD,
) -> DeviceModelCAD:
    """Build the B-rep device model of a validated design.

    Parameters
    ----------
    configuration
        Validated FRC configuration.
    geometry
        Validated mechanical envelope.
    segments
        Segment count of the tier-G1 reference mesh of the comparison.
    profile_samples
        Odd sample count of the separatrix, for both tiers.
    linear_deflection_m, angular_deflection_rad
        Mesher deflections of the faceting comparison.

    Returns
    -------
    DeviceModelCAD
        The composed, fail-closed checked model with its STEP export.

    Raises
    ------
    DeviceGeometryError
        If the configuration and the geometry do not fit together, if a
        count or a deflection is invalid, or if a body violates a declared
        evidence bound; the library's refusals are re-raised under the
        device error type with their messages.
        :class:`~scpn_reactor_kernels.errors.CadUnavailableError` if the
        optional CAD back-end is absent.
    """
    reference = build_device_model(configuration, geometry, segments, profile_samples)
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
    try:
        assembly = BrepAssembly(
            (
                closed_profiled_solid_brep(
                    profile, BODY_PLASMA_SEPARATRIX, ROLE_PLASMA, MATERIAL_PLASMA
                ),
                annular_tube_brep(
                    tube_inner,
                    tube_outer,
                    -coil_half,
                    coil_half,
                    BODY_CONFINEMENT_TUBE,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_TUBE_WALL,
                ),
                annular_tube_brep(
                    coil_inner,
                    coil_inner + geometry.coil_wall_thickness_m,
                    -coil_half,
                    coil_half,
                    BODY_CONFINEMENT_COIL,
                    ROLE_COIL,
                    MATERIAL_COIL_CONDUCTOR,
                ),
                cylinder_solid_brep(
                    tube_outer,
                    -coil_half - wall,
                    -coil_half,
                    BODY_END_WALL_UPSTREAM,
                    ROLE_STRUCTURE,
                    MATERIAL_END_WALL,
                ),
                cylinder_solid_brep(
                    tube_outer,
                    coil_half,
                    coil_half + wall,
                    BODY_END_WALL_DOWNSTREAM,
                    ROLE_STRUCTURE,
                    MATERIAL_END_WALL,
                ),
            )
        )
        faceted = facet_assembly(assembly, linear_deflection_m, angular_deflection_rad)
        smallest_radii = (
            smallest_tessellated_radius_m(profile),
            tube_inner,
            coil_inner,
            tube_outer,
            tube_outer,
        )
        bodies = assembly_evidence(
            assembly.bodies,
            smallest_radii,
            faceted,
            reference.meshes,
            linear_deflection_m,
            segments,
        )
    except (CadError, GeometryError) as exc:
        raise DeviceGeometryError(str(exc)) from exc
    manifest = assembly.manifest()
    extras = {
        "schema": CAD_MODEL_SCHEMA,
        "schema_version": CAD_MODEL_SCHEMA_VERSION,
        "configuration_digest_sha256": configuration.digest_sha256(),
        "geometry_digest_sha256": geometry.digest_sha256(),
        "assembly_manifest_sha256": assembly.manifest_sha256(),
        "units": dict(CAD_MODEL_UNITS),
        "non_claims": list(CAD_MODEL_NON_CLAIMS),
        "backend_versions": backend_versions(),
    }
    step_data = step_bytes(assembly, extras)
    return DeviceModelCAD(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        reference_mesh_segments=segments,
        reference_profile_samples=profile_samples,
        linear_deflection_m=linear_deflection_m,
        angular_deflection_rad=angular_deflection_rad,
        backend_versions=backend_versions(),
        assembly_manifest=manifest,
        step_sha256=step_sha256(step_data),
        bodies=bodies,
        step_data=step_data,
        faceted_meshes=faceted,
    )


__all__ = [
    "CAD_MODEL_NON_CLAIMS",
    "CAD_MODEL_SCHEMA",
    "CAD_MODEL_SCHEMA_VERSION",
    "CAD_MODEL_UNITS",
    "DEFAULT_ANGULAR_DEFLECTION_RAD",
    "DEFAULT_LINEAR_DEFLECTION_M",
    "DEFAULT_REFERENCE_MESH_SEGMENTS",
    "DEFAULT_REFERENCE_PROFILE_SAMPLES",
    "DeviceModelCAD",
    "build_device_cad",
    "smallest_tessellated_radius_m",
]
