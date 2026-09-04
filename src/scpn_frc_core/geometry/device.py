# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — device geometry model

"""Validated mechanical envelope of a field-reversed-configuration device.

The geometry complements the
:class:`~scpn_frc_core.configuration.DeviceConfiguration`, which already
carries the separatrix radius, the separatrix length and the confinement
coil radius. Those three are **not** repeated here: they are read from the
configuration and cross-checked against this envelope when a model is
built, so each number has one home.

What the envelope adds is the hardware around the plasma: the bore and
wall of the confinement tube the plasma sits inside, the winding thickness
and axial length of the confinement coil around it, the thickness of the
two end walls, and the shape index of the separatrix.

The shape index is the ``m`` of the published separatrix equation
``r^2 / a^2 + |z|^m / b^m = 1`` (H. J. Ma et al., arXiv:2103.00839v1
(2021), equation 13), so the surface is ``r(z) = a sqrt(1 - |z / b|^m)``
with ``a`` the midplane separatrix radius and ``b`` the half-length. The
source names ``m = 2`` as the elliptical shape and larger values as
progressively more racetrack-like; this model admits that range and
refuses below it rather than extrapolating past what the source describes.

Validation is fail-closed, serialisation is canonical, and the SHA-256
digest identifies the exact geometry.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_frc_core.errors import DeviceGeometryError
from scpn_frc_core.parameters import require_positive

GEOMETRY_FIELDS: Final = (
    "confinement_tube_inner_radius_m",
    "confinement_tube_wall_thickness_m",
    "coil_wall_thickness_m",
    "coil_length_m",
    "end_wall_thickness_m",
    "separatrix_shape_index",
)

#: Smallest shape index the model admits: the ellipse of the source's
#: equation 13. Smaller values leave the family that source parameterises.
MIN_SHAPE_INDEX: Final = 2.0


def _positive(name: str, value: float) -> float:
    """Apply the shared positivity rule under the geometry error type.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceGeometryError
        If the value is non-finite or not strictly positive.
    """
    try:
        return require_positive(name, value)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class DeviceGeometry:
    """Validated FRC mechanical envelope (SI units in the field names).

    Parameters
    ----------
    confinement_tube_inner_radius_m
        Bore radius of the tube the plasma sits inside; strictly positive.
    confinement_tube_wall_thickness_m
        Radial wall thickness of that tube; strictly positive.
    coil_wall_thickness_m
        Radial winding thickness of the confinement coil; strictly
        positive. The coil's inner radius is the configuration's
        ``coil_radius_m`` and is not repeated here.
    coil_length_m
        Axial length of the confinement coil; strictly positive.
    end_wall_thickness_m
        Axial thickness of each of the two end walls; strictly positive.
    separatrix_shape_index
        The ``m`` of the separatrix equation; at least
        :data:`MIN_SHAPE_INDEX`.

    Raises
    ------
    DeviceGeometryError
        If any value is non-finite or not strictly positive, or if the
        shape index is below the ellipse.
    """

    confinement_tube_inner_radius_m: float
    confinement_tube_wall_thickness_m: float
    coil_wall_thickness_m: float
    coil_length_m: float
    end_wall_thickness_m: float
    separatrix_shape_index: float

    def __post_init__(self) -> None:
        """Validate every declared value.

        Raises
        ------
        DeviceGeometryError
            If any value is non-finite or not strictly positive, or if
            the shape index is below the ellipse.
        """
        for name in GEOMETRY_FIELDS:
            _positive(name, getattr(self, name))
        if self.separatrix_shape_index < MIN_SHAPE_INDEX:
            raise DeviceGeometryError(
                "separatrix_shape_index: must be at least "
                f"{MIN_SHAPE_INDEX} (the ellipse of the source's equation 13), "
                f"got {self.separatrix_shape_index!r}"
            )

    @property
    def confinement_tube_outer_radius_m(self) -> float:
        """Outer radius of the confinement tube (bore plus wall)."""
        return (
            self.confinement_tube_inner_radius_m
            + self.confinement_tube_wall_thickness_m
        )

    def to_record(self) -> dict[str, float]:
        """Project the geometry to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every declared parameter under its name.
        """
        return {name: getattr(self, name) for name in GEOMETRY_FIELDS}

    def canonical_bytes(self) -> bytes:
        """Serialise the geometry canonically.

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
        """Identify the exact geometry.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Decoded object.
    field
        Field name.

    Returns
    -------
    float
        The value as a float.

    Raises
    ------
    DeviceGeometryError
        If the field is absent or is not a real number.
    """
    if field not in record:
        raise DeviceGeometryError(f"{field}: required")
    value = record[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DeviceGeometryError(f"{field}: must be a real number, got {value!r}")
    return float(value)


def geometry_from_record(record: dict[str, Any]) -> DeviceGeometry:
    """Build a geometry from a decoded record, refusing unknown fields.

    Parameters
    ----------
    record
        Decoded object carrying exactly :data:`GEOMETRY_FIELDS`.

    Returns
    -------
    DeviceGeometry
        The validated geometry.

    Raises
    ------
    DeviceGeometryError
        If a field is missing, of the wrong type, unknown, or violates a
        model invariant.
    """
    unknown = sorted(set(record) - set(GEOMETRY_FIELDS))
    if unknown:
        raise DeviceGeometryError(f"geometry: unknown fields {unknown!r}")
    return DeviceGeometry(**{name: _number(record, name) for name in GEOMETRY_FIELDS})
