# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — tier-G1 device model tests

"""The five bodies close, orient outward, and carry the printed hardware."""

from __future__ import annotations

import hashlib
import json
import math
from itertools import pairwise

import pytest
from geometry_fixtures import (
    ANCHOR_ACTIVE_COIL_LENGTH_M,
    ANCHOR_COIL_COUNT,
    ANCHOR_COIL_PITCH_M,
    ANCHOR_COIL_RADIUS_M,
    ANCHOR_QUARTZ_INNER_RADIUS_M,
    ANCHOR_QUARTZ_OUTER_RADIUS_M,
    ANCHOR_SEPARATRIX_LENGTH_M,
    ANCHOR_SEPARATRIX_RADIUS_M,
    REFERENCE_PROFILE_SAMPLES,
    REFERENCE_SEGMENTS,
    anchor_configuration,
    anchor_geometry,
    reference_configuration,
    reference_geometry,
)

from scpn_frc_core.errors import DeviceGeometryError
from scpn_frc_core.geometry.model import (
    BODY_NAMES,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    DeviceModel3D,
    build_device_model,
    require_profile_samples,
    separatrix_profile,
)


def reference_model() -> DeviceModel3D:
    """Build the synthetic reference model."""
    return build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_SEGMENTS,
        REFERENCE_PROFILE_SAMPLES,
    )


def test_the_profile_is_zero_at_both_poles_exactly() -> None:
    """The closed-profile contract needs exact zeros, not near-zeros."""
    profile = separatrix_profile(0.02, 0.15, 2.0, 9)
    assert profile[0] == (-0.15, 0.0)
    assert profile[-1] == (0.15, 0.0)


def test_the_midplane_is_a_sample_and_carries_the_full_radius() -> None:
    """An odd count puts the widest point of the separatrix on the model."""
    profile = separatrix_profile(0.02, 0.15, 2.0, 9)
    assert profile[4] == (0.0, 0.02)


def test_the_profile_increases_strictly_in_height() -> None:
    """The library's contract needs strictly increasing heights."""
    profile = separatrix_profile(0.02, 0.15, 2.0, 41)
    assert all(later[0] > earlier[0] for earlier, later in pairwise(profile))


def test_the_ellipse_reproduces_its_own_closed_form() -> None:
    """At m = 2 the body is an ellipsoid of revolution.

    Sampling a curve with straight segments inscribes it, so the sampled
    volume sits below ``4/3 pi a^2 b`` and approaches it as the sample
    count rises. That ordering is the test; the deficit is the linear
    interpolation, not an error.

    The bound is measured rather than assumed. Convergence is not clean
    second order because the ellipse meets the axis with infinite slope,
    so the interpolation error at the poles falls more slowly than it does
    along the flanks: the measured deficits are 3.1e-2, 6.5e-4 and 8.3e-6
    at 11, 81 and 801 samples.
    """
    from scpn_reactor_kernels.geometry import profile_volume_m3

    exact = 4.0 / 3.0 * math.pi * 0.02 * 0.02 * 0.15
    volumes = [
        profile_volume_m3(separatrix_profile(0.02, 0.15, 2.0, samples))
        for samples in (11, 81, 801)
    ]
    assert all(earlier < later for earlier, later in pairwise(volumes))
    assert volumes[-1] < exact
    assert (exact - volumes[-1]) / exact < 1.0e-5


def test_a_larger_shape_index_makes_a_fuller_body() -> None:
    """Racetrack-like is fuller than elliptical, which is the source's word."""
    from scpn_reactor_kernels.geometry import profile_volume_m3

    ellipse = profile_volume_m3(separatrix_profile(0.02, 0.15, 2.0, 101))
    racetrack = profile_volume_m3(separatrix_profile(0.02, 0.15, 6.0, 101))
    assert racetrack > ellipse


@pytest.mark.parametrize("samples", [2, 1, 0, -3])
def test_too_few_profile_samples_are_refused(samples: int) -> None:
    """Three samples are the fewest that carry two poles and a midplane."""
    with pytest.raises(DeviceGeometryError, match="profile_samples"):
        require_profile_samples(samples)


@pytest.mark.parametrize("samples", [4, 40, 100])
def test_an_even_profile_sample_count_is_refused(samples: int) -> None:
    """Without a midplane sample the widest point is not on the model."""
    with pytest.raises(DeviceGeometryError, match="odd"):
        require_profile_samples(samples)


def test_a_boolean_sample_count_is_refused() -> None:
    """A boolean is not a count, even though Python says it is an int."""
    boolean_count: int = True
    with pytest.raises(DeviceGeometryError, match="profile_samples"):
        require_profile_samples(boolean_count)


def test_a_shape_index_that_leaves_the_kernel_range_is_refused() -> None:
    """The transcendental kernel's refusal is re-raised, not swallowed."""
    with pytest.raises(DeviceGeometryError, match=r"power|exponent"):
        separatrix_profile(0.02, 0.15, 1.0e6, 9)


def test_the_model_carries_the_five_bodies_in_order() -> None:
    """The body set and its order are fixed."""
    model = reference_model()
    assert tuple(mesh.name for mesh in model.meshes) == BODY_NAMES


def test_every_body_is_closed_and_outward_oriented() -> None:
    """Each mesh satisfies the library's closed-surface contract."""
    for mesh in reference_model().meshes:
        assert mesh.signed_volume_m3() > 0.0
        assert mesh.surface_area_m2() > 0.0


def test_the_bodies_nest_the_way_the_device_does() -> None:
    """Plasma inside the tube, tube inside the coil bore."""
    model = reference_model()
    bodies = {mesh.name: mesh for mesh in model.meshes}
    separatrix = bodies["plasma_separatrix"].bounding_box()[1][0]
    tube_outer = bodies["confinement_tube"].bounding_box()[1][0]
    coil_outer = bodies["confinement_coil"].bounding_box()[1][0]
    assert separatrix < tube_outer < coil_outer


def test_the_end_walls_sit_outside_the_coil_and_face_each_other() -> None:
    """The two walls close the assembly at either end of the coil."""
    model = reference_model()
    bodies = {mesh.name: mesh for mesh in model.meshes}
    coil_low, coil_high = bodies["confinement_coil"].bounding_box()
    up_low, up_high = bodies["end_wall_upstream"].bounding_box()
    down_low, down_high = bodies["end_wall_downstream"].bounding_box()
    assert up_high[2] == coil_low[2]
    assert down_low[2] == coil_high[2]
    assert up_low[2] < up_high[2] < down_low[2] < down_high[2]


def test_the_record_is_schema_tagged_and_states_its_non_claims() -> None:
    """The record names its schema and carries the non-claims verbatim."""
    record = reference_model().to_record()
    assert record["schema"] == MODEL_SCHEMA
    assert record["schema_version"] == MODEL_SCHEMA_VERSION
    assert record["non_claims"] == list(MODEL_NON_CLAIMS)
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)


def test_the_record_binds_the_inputs_it_was_built_from() -> None:
    """Both digests are the digests of the objects that produced it."""
    configuration, geometry = reference_configuration(), reference_geometry()
    model = build_device_model(configuration, geometry, 64, 41)
    assert model.configuration_digest_sha256 == configuration.digest_sha256()
    assert model.geometry_digest_sha256 == geometry.digest_sha256()


def test_canonical_bytes_are_already_in_canonical_form() -> None:
    """Re-canonicalising the bytes is a no-op, and they round-trip."""
    model = reference_model()
    data = model.canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data)
    assert decoded == model.to_record()
    again = json.dumps(decoded, sort_keys=True, separators=(",", ":"))
    assert data == (again + "\n").encode("utf-8")
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()


def test_a_model_refuses_a_body_set_out_of_order() -> None:
    """The fixed order is enforced at construction, not assumed."""
    model = reference_model()
    reordered = (model.meshes[1], model.meshes[0], *model.meshes[2:])
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        DeviceModel3D(
            configuration_digest_sha256=model.configuration_digest_sha256,
            geometry_digest_sha256=model.geometry_digest_sha256,
            segments=model.segments,
            profile_samples=model.profile_samples,
            meshes=reordered,
        )


@pytest.mark.parametrize("segments", [4, 12, 0])
def test_an_inadmissible_segment_count_is_refused(segments: int) -> None:
    """The library's segment contract governs every body."""
    with pytest.raises(DeviceGeometryError, match="segments"):
        build_device_model(
            reference_configuration(), reference_geometry(), segments, 41
        )


def test_a_plasma_wider_than_the_tube_is_refused() -> None:
    """The envelope check names the two fields and their values."""
    from scpn_frc_core.geometry.device import DeviceGeometry

    narrow = DeviceGeometry(0.25, 0.02, 0.05, 3.0, 0.03, 2.0)
    with pytest.raises(DeviceGeometryError, match="separatrix_radius_m"):
        build_device_model(reference_configuration(), narrow, 64, 41)


def test_a_tube_wider_than_the_coil_bore_is_refused() -> None:
    """The tube must fit inside the bore the configuration declares."""
    from scpn_frc_core.geometry.device import DeviceGeometry

    fat = DeviceGeometry(0.45, 0.06, 0.05, 3.0, 0.03, 2.0)
    with pytest.raises(DeviceGeometryError, match="confinement_tube_outer_radius_m"):
        build_device_model(reference_configuration(), fat, 64, 41)


def test_a_separatrix_longer_than_the_coil_is_refused() -> None:
    """The plasma must lie within the coil that confines it."""
    from scpn_frc_core.geometry.device import DeviceGeometry

    short = DeviceGeometry(0.4, 0.02, 0.05, 2.0, 0.03, 2.0)
    with pytest.raises(DeviceGeometryError, match="separatrix_length_m"):
        build_device_model(reference_configuration(), short, 64, 41)


def test_an_even_sample_count_is_refused_by_the_builder() -> None:
    """The builder applies the sample contract before it builds."""
    with pytest.raises(DeviceGeometryError, match="odd"):
        build_device_model(reference_configuration(), reference_geometry(), 64, 40)


def test_the_anchor_bodies_carry_every_printed_dimension() -> None:
    """Each printed value is recoverable from the built bodies.

    Not from the configuration that fed them: the assertions below read
    vertices and bounding boxes of the meshes the model produced. The
    library's rings start at angle zero, so the vertex on the positive x
    axis of each ring carries that ring's radius exactly.
    """
    model = build_device_model(anchor_configuration(), anchor_geometry(), 64, 41)
    bodies = {mesh.name: mesh for mesh in model.meshes}

    tube_x = {vertex[0] for vertex in bodies["confinement_tube"].vertices}
    assert ANCHOR_QUARTZ_INNER_RADIUS_M in tube_x
    assert ANCHOR_QUARTZ_OUTER_RADIUS_M in tube_x

    coil_x = {vertex[0] for vertex in bodies["confinement_coil"].vertices}
    assert ANCHOR_COIL_RADIUS_M in coil_x

    coil_low, coil_high = bodies["confinement_coil"].bounding_box()
    assert coil_high[2] - coil_low[2] == ANCHOR_ACTIVE_COIL_LENGTH_M
    assert ANCHOR_COIL_COUNT * ANCHOR_COIL_PITCH_M == ANCHOR_ACTIVE_COIL_LENGTH_M


def test_the_anchor_separatrix_is_declared_and_fits_the_printed_bore() -> None:
    """The declared plasma sits inside the printed hardware."""
    model = build_device_model(anchor_configuration(), anchor_geometry(), 64, 41)
    bodies = {mesh.name: mesh for mesh in model.meshes}
    low, high = bodies["plasma_separatrix"].bounding_box()
    assert high[0] == ANCHOR_SEPARATRIX_RADIUS_M
    assert high[2] - low[2] == ANCHOR_SEPARATRIX_LENGTH_M
    assert high[0] < ANCHOR_QUARTZ_INNER_RADIUS_M
    assert high[2] - low[2] < ANCHOR_ACTIVE_COIL_LENGTH_M
