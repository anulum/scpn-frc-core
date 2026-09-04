# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — device geometry tests

"""The mechanical envelope validates, serialises and round-trips."""

from __future__ import annotations

import json
import math
from typing import Any

import pytest
from geometry_fixtures import (
    ANCHOR_QUARTZ_INNER_RADIUS_M,
    ANCHOR_QUARTZ_OUTER_RADIUS_M,
    ANCHOR_QUARTZ_WALL_THICKNESS_M,
    anchor_geometry,
    reference_geometry,
)

from scpn_frc_core.errors import DeviceGeometryError
from scpn_frc_core.geometry.device import (
    GEOMETRY_FIELDS,
    MIN_SHAPE_INDEX,
    DeviceGeometry,
    geometry_from_record,
)


def test_the_record_carries_every_declared_field() -> None:
    """The record is exactly the declared fields, and nothing else."""
    assert sorted(reference_geometry().to_record()) == sorted(GEOMETRY_FIELDS)


def test_the_outer_radius_is_the_bore_plus_the_wall() -> None:
    """The derived radius is a sum, not a second declared number."""
    geometry = reference_geometry()
    assert geometry.confinement_tube_outer_radius_m == (
        geometry.confinement_tube_inner_radius_m
        + geometry.confinement_tube_wall_thickness_m
    )


def test_the_anchor_wall_adds_back_to_the_printed_outer_radius() -> None:
    """The derived wall reproduces the printed outer radius exactly.

    The difference of the two printed radii is not the decimal 0.0025 in
    binary, so the fixture derives the wall instead of writing that
    literal. What is exact, and what the anchor rests on, is that adding
    it back gives the printed outer radius.
    """
    assert ANCHOR_QUARTZ_WALL_THICKNESS_M != 0.0025
    assert (
        ANCHOR_QUARTZ_INNER_RADIUS_M + ANCHOR_QUARTZ_WALL_THICKNESS_M
        == ANCHOR_QUARTZ_OUTER_RADIUS_M
    )
    assert anchor_geometry().confinement_tube_outer_radius_m == (
        ANCHOR_QUARTZ_OUTER_RADIUS_M
    )


@pytest.mark.parametrize("field", GEOMETRY_FIELDS)
@pytest.mark.parametrize("value", [0.0, -1.0, math.inf, math.nan])
def test_every_field_is_refused_outside_its_domain(field: str, value: float) -> None:
    """A non-finite or non-positive value is refused, naming the field."""
    record = reference_geometry().to_record()
    record[field] = value
    with pytest.raises(DeviceGeometryError, match=field):
        geometry_from_record(record)


def test_a_shape_index_below_the_ellipse_is_refused() -> None:
    """The model admits the source's range and refuses below it."""
    record = reference_geometry().to_record()
    record["separatrix_shape_index"] = 1.9
    with pytest.raises(DeviceGeometryError, match="separatrix_shape_index"):
        geometry_from_record(record)


def test_the_ellipse_itself_is_admitted() -> None:
    """The bound is inclusive: m = 2 is the shape the source names."""
    record = reference_geometry().to_record()
    record["separatrix_shape_index"] = MIN_SHAPE_INDEX
    assert geometry_from_record(record).separatrix_shape_index == MIN_SHAPE_INDEX


def test_a_record_round_trips_through_its_own_projection() -> None:
    """Projecting and rebuilding gives an equal geometry."""
    geometry = reference_geometry()
    assert geometry_from_record(geometry.to_record()) == geometry


def test_an_unknown_field_is_refused_and_named() -> None:
    """The parser is strict: an unexpected key is an error."""
    record: dict[str, Any] = dict(reference_geometry().to_record())
    record["coil_turns"] = 8
    with pytest.raises(DeviceGeometryError, match="coil_turns"):
        geometry_from_record(record)


def test_a_missing_field_is_refused_and_named() -> None:
    """Every declared field is required."""
    record = reference_geometry().to_record()
    del record["coil_length_m"]
    with pytest.raises(DeviceGeometryError, match="coil_length_m"):
        geometry_from_record(record)


@pytest.mark.parametrize("value", ["0.5", None, True])
def test_a_field_of_the_wrong_type_is_refused(value: Any) -> None:
    """A string, a null and a boolean are not real numbers."""
    record: dict[str, Any] = dict(reference_geometry().to_record())
    record["coil_length_m"] = value
    with pytest.raises(DeviceGeometryError, match="coil_length_m"):
        geometry_from_record(record)


def test_canonical_bytes_are_sorted_and_newline_terminated() -> None:
    """The serialisation is canonical and round-trips to the record."""
    geometry = reference_geometry()
    data = geometry.canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data)
    assert decoded == geometry.to_record()
    assert list(decoded) == sorted(decoded)


def test_the_digest_identifies_the_exact_bytes() -> None:
    """The digest moves with the geometry and only with it."""
    import hashlib

    geometry = reference_geometry()
    assert (
        geometry.digest_sha256()
        == hashlib.sha256(geometry.canonical_bytes()).hexdigest()
    )
    assert geometry.digest_sha256() != anchor_geometry().digest_sha256()


def test_the_geometry_is_frozen() -> None:
    """A validated envelope cannot be edited after construction."""
    with pytest.raises((AttributeError, TypeError)):
        reference_geometry().coil_length_m = 1.0  # type: ignore[misc]


def test_the_dataclass_is_reachable_directly() -> None:
    """The constructor validates the same way the parser does."""
    with pytest.raises(DeviceGeometryError, match="end_wall_thickness_m"):
        DeviceGeometry(0.4, 0.02, 0.05, 3.0, 0.0, 2.0)
