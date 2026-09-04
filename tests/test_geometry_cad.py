# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — tier-G2 device model tests

"""The B-rep bodies agree with their closed forms and with tier G1."""

from __future__ import annotations

import hashlib
import json
import math

import pytest
from geometry_fixtures import (
    ANCHOR_ACTIVE_COIL_LENGTH_M,
    ANCHOR_COIL_RADIUS_M,
    ANCHOR_QUARTZ_INNER_RADIUS_M,
    ANCHOR_QUARTZ_OUTER_RADIUS_M,
    ANCHOR_SEPARATRIX_RADIUS_M,
    anchor_configuration,
    anchor_geometry,
    reference_configuration,
    reference_geometry,
)
from scpn_reactor_kernels.cad import MANIFEST_SCHEMA, MEASURE_TOLERANCE
from scpn_reactor_kernels.geometry import profile_lateral_area_m2, profile_volume_m3

from scpn_frc_core.errors import DeviceGeometryError
from scpn_frc_core.geometry.cad import (
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    DEFAULT_REFERENCE_PROFILE_SAMPLES,
    DeviceModelCAD,
    build_device_cad,
    smallest_tessellated_radius_m,
)
from scpn_frc_core.geometry.model import BODY_NAMES, separatrix_profile

#: Digest of the reference CAD model record in the pinned back-end
#: environment (cadquery 2.8.0, OCP 7.9.3.1); a back-end bump re-pins it
#: as a governed data change.
REFERENCE_CAD_MODEL_SHA256 = (
    "c4879026600cc02011060a0d33803090768948fb3410a1b26772b56dd7790c87"
)


def model() -> DeviceModelCAD:
    """Build the reference B-rep model of these tests."""
    return build_device_cad(reference_configuration(), reference_geometry())


def test_the_bodies_are_the_five_in_order() -> None:
    """The B-rep body set matches the tier-G1 set exactly."""
    assert tuple(body.name for body in model().bodies) == BODY_NAMES


def test_every_body_agrees_with_its_analytic_closed_form() -> None:
    """Volume and area sit inside the library's measure tolerance."""
    for body in model().bodies:
        assert body.volume_relative_error <= MEASURE_TOLERANCE
        assert body.surface_area_relative_error <= MEASURE_TOLERANCE


def test_every_body_is_inside_its_faceting_deficit_bound() -> None:
    """The faceted volume is below the exact one, within the chord bound."""
    for body in model().bodies:
        assert body.faceted_volume_relative_deficit >= 0.0
        assert body.faceted_volume_relative_deficit <= body.faceted_volume_deficit_bound


def test_every_body_agrees_with_its_tier_g1_twin() -> None:
    """The two tiers describe one body, not two similar ones."""
    for body in model().bodies:
        assert abs(body.mesh_volume_relative_difference) <= (
            body.mesh_volume_difference_bound
        )


def test_the_separatrix_carries_the_profile_closed_forms() -> None:
    """The revolved separatrix is measured against the frustum sums.

    A pole contributes no end disc, so the area reference is the lateral
    sum alone — the same two functions the open profile uses.
    """
    profile = separatrix_profile(
        reference_configuration().geometry.separatrix_radius_m,
        reference_configuration().geometry.separatrix_length_m / 2.0,
        reference_geometry().separatrix_shape_index,
        DEFAULT_REFERENCE_PROFILE_SAMPLES,
    )
    separatrix = model().bodies[0]
    assert separatrix.analytic_volume_m3 == profile_volume_m3(profile)
    assert separatrix.analytic_surface_area_m2 == profile_lateral_area_m2(profile)


def test_the_smallest_radius_excludes_the_poles() -> None:
    """A pole is a point, not a circle, so it cannot bound a deficit.

    Taking the pole radius would divide by zero in the ``2 d / r`` bound
    and taking the midplane radius would assert a bound the body does not
    satisfy near its ends; the narrowest ring it is actually built from is
    the honest value.
    """
    profile = separatrix_profile(0.02, 0.15, 2.0, 41)
    smallest = smallest_tessellated_radius_m(profile)
    assert smallest > 0.0
    assert smallest == min(radius for _, radius in profile[1:-1])
    assert smallest < 0.02
    assert profile[0][1] == 0.0
    assert profile[-1][1] == 0.0


def test_the_record_is_schema_tagged_and_states_its_non_claims() -> None:
    """The record names its schema and carries the non-claims verbatim."""
    record = model().to_record()
    assert record["schema"] == CAD_MODEL_SCHEMA
    assert record["schema_version"] == CAD_MODEL_SCHEMA_VERSION
    assert record["non_claims"] == list(CAD_MODEL_NON_CLAIMS)
    assert record["reference_mesh_segments"] == DEFAULT_REFERENCE_MESH_SEGMENTS
    assert record["reference_profile_samples"] == DEFAULT_REFERENCE_PROFILE_SAMPLES
    assert record["linear_deflection_m"] == DEFAULT_LINEAR_DEFLECTION_M
    assert record["angular_deflection_rad"] == DEFAULT_ANGULAR_DEFLECTION_RAD
    assert record["assembly_manifest"]["schema"] == MANIFEST_SCHEMA
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)


def test_the_back_ends_are_recorded_and_present() -> None:
    """The record names the environment its determinism is claimed in."""
    versions = model().backend_versions
    assert versions["cadquery"] != "unavailable"
    assert versions["ocp"] != "unavailable"


def test_the_record_is_canonical_and_its_digest_is_pinned() -> None:
    """The bytes are canonical and reproduce the pinned digest."""
    built = model()
    data = built.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == built.to_record()
    assert built.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert built.digest_sha256() == REFERENCE_CAD_MODEL_SHA256


def test_two_builds_of_the_same_design_agree() -> None:
    """The record is deterministic inside the pinned environment."""
    assert model().digest_sha256() == model().digest_sha256()


def test_the_step_export_is_the_digested_bytes() -> None:
    """The exported file is exactly the bytes the record digests."""
    built = model()
    assert built.step_sha256 == hashlib.sha256(built.step_data).hexdigest()
    assert built.step_data.startswith(b"ISO-10303-21;")


def test_the_exported_bytes_are_what_a_caller_writes(tmp_path: object) -> None:
    """The record carries the bytes; writing them changes nothing."""
    from pathlib import Path

    built = model()
    target = Path(str(tmp_path)) / "frc.step"
    target.write_bytes(built.step_data)
    assert target.read_bytes() == built.step_data
    assert hashlib.sha256(target.read_bytes()).hexdigest() == built.step_sha256


def test_a_manifest_with_the_wrong_body_count_is_refused() -> None:
    """The record checks the manifest it was handed."""
    built = model()
    broken = dict(built.assembly_manifest)
    broken["body_count"] = 4
    with pytest.raises(DeviceGeometryError, match="body_count"):
        DeviceModelCAD(
            configuration_digest_sha256=built.configuration_digest_sha256,
            geometry_digest_sha256=built.geometry_digest_sha256,
            reference_mesh_segments=built.reference_mesh_segments,
            reference_profile_samples=built.reference_profile_samples,
            linear_deflection_m=built.linear_deflection_m,
            angular_deflection_rad=built.angular_deflection_rad,
            backend_versions=built.backend_versions,
            assembly_manifest=broken,
            step_sha256=built.step_sha256,
            bodies=built.bodies,
            step_data=built.step_data,
            faceted_meshes=built.faceted_meshes,
        )


def test_a_manifest_of_the_wrong_schema_is_refused() -> None:
    """A foreign manifest is not accepted silently."""
    built = model()
    broken = dict(built.assembly_manifest)
    broken["schema"] = "something.else.v1"
    with pytest.raises(DeviceGeometryError, match=r"assembly_manifest\.schema"):
        DeviceModelCAD(
            configuration_digest_sha256=built.configuration_digest_sha256,
            geometry_digest_sha256=built.geometry_digest_sha256,
            reference_mesh_segments=built.reference_mesh_segments,
            reference_profile_samples=built.reference_profile_samples,
            linear_deflection_m=built.linear_deflection_m,
            angular_deflection_rad=built.angular_deflection_rad,
            backend_versions=built.backend_versions,
            assembly_manifest=broken,
            step_sha256=built.step_sha256,
            bodies=built.bodies,
            step_data=built.step_data,
            faceted_meshes=built.faceted_meshes,
        )


def test_bodies_out_of_order_are_refused() -> None:
    """The fixed body order is enforced on the B-rep record too."""
    built = model()
    with pytest.raises(DeviceGeometryError, match="must be exactly"):
        DeviceModelCAD(
            configuration_digest_sha256=built.configuration_digest_sha256,
            geometry_digest_sha256=built.geometry_digest_sha256,
            reference_mesh_segments=built.reference_mesh_segments,
            reference_profile_samples=built.reference_profile_samples,
            linear_deflection_m=built.linear_deflection_m,
            angular_deflection_rad=built.angular_deflection_rad,
            backend_versions=built.backend_versions,
            assembly_manifest=built.assembly_manifest,
            step_sha256=built.step_sha256,
            bodies=(built.bodies[1], built.bodies[0], *built.bodies[2:]),
            step_data=built.step_data,
            faceted_meshes=built.faceted_meshes,
        )


def test_an_invalid_deflection_is_refused_by_the_builder() -> None:
    """The library's deflection contract governs the faceting."""
    with pytest.raises(DeviceGeometryError, match="deflection"):
        build_device_cad(
            reference_configuration(), reference_geometry(), 8, 41, 0.0, 0.1
        )


def test_an_envelope_that_does_not_fit_is_refused_before_any_solid() -> None:
    """The tier-G1 envelope check runs first and refuses the same way."""
    from scpn_frc_core.geometry.device import DeviceGeometry

    narrow = DeviceGeometry(0.25, 0.02, 0.05, 3.0, 0.03, 2.0)
    with pytest.raises(DeviceGeometryError, match="separatrix_radius_m"):
        build_device_cad(reference_configuration(), narrow)


def test_the_anchor_bodies_carry_the_printed_hardware_at_this_tier_too() -> None:
    """The printed dimensions survive into the B-rep bodies.

    Read from the measured bounding boxes of the solids the back-end
    built, not from the configuration that fed them.
    """
    built = build_device_cad(anchor_configuration(), anchor_geometry())
    record = built.to_record()
    bodies = {body["name"]: body for body in record["assembly_manifest"]["bodies"]}

    tube = bodies["confinement_tube"]
    assert math.isclose(
        tube["bounding_box_max_m"][0], ANCHOR_QUARTZ_OUTER_RADIUS_M, rel_tol=1.0e-12
    )
    coil = bodies["confinement_coil"]
    assert math.isclose(
        coil["bounding_box_max_m"][2] - coil["bounding_box_min_m"][2],
        ANCHOR_ACTIVE_COIL_LENGTH_M,
        rel_tol=1.0e-12,
    )
    separatrix = bodies["plasma_separatrix"]
    assert math.isclose(
        separatrix["bounding_box_max_m"][0],
        ANCHOR_SEPARATRIX_RADIUS_M,
        rel_tol=1.0e-12,
    )
    assert separatrix["bounding_box_max_m"][0] < ANCHOR_QUARTZ_INNER_RADIUS_M
    assert ANCHOR_QUARTZ_OUTER_RADIUS_M < ANCHOR_COIL_RADIUS_M


def test_a_shape_the_back_end_cannot_honour_is_refused() -> None:
    """A racetrack separatrix is refused, and that is the guard working.

    The back-end's revolution stops reproducing the exact frustum sum
    when two adjacent profile radii come close together, and a shape
    index above the ellipse flattens the separatrix at its midplane until
    they do. Measured on this fixture's dimensions at 17 samples: exact
    to 2e-16 at m = 2, and 1.6e-4, 5.5e-5, 3.0e-4 and 3.3e-4 at m = 2.5,
    3, 4 and 6.

    The limitation is not this repository's and is not new: the same
    numbers come out of the open profile primitive when the same shape is
    lifted off the axis, so it predates the closed-profile kernel. What
    matters here is that nothing silently accepts a body the back-end
    cannot reproduce — the library's evidence kernel refuses it, naming
    the body and the bound it missed.
    """
    from scpn_frc_core.geometry.device import DeviceGeometry

    racetrack = DeviceGeometry(0.4, 0.02, 0.05, 3.0, 0.03, 6.0)
    with pytest.raises(DeviceGeometryError, match="plasma_separatrix"):
        build_device_cad(reference_configuration(), racetrack)


def test_the_tier_g1_model_builds_that_same_shape_without_complaint() -> None:
    """The limitation is the back-end's, not the geometry's.

    The tessellated tier is exact for the shape tier G2 refuses, which is
    what locates the limitation in the CAD back-end rather than in the
    shape function or in the profile contract.
    """
    from scpn_frc_core.geometry.device import DeviceGeometry
    from scpn_frc_core.geometry.model import build_device_model

    racetrack = DeviceGeometry(0.4, 0.02, 0.05, 3.0, 0.03, 6.0)
    tessellated = build_device_model(reference_configuration(), racetrack, 64, 21)
    assert tessellated.meshes[0].signed_volume_m3() > 0.0
