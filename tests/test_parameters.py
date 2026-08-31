# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — parameter model tests

"""Every validation branch of the FRC parameter model.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_frc_core.errors import DeviceConfigurationError
from scpn_frc_core.parameters import (
    OperationalLimits,
    SeparatrixGeometry,
    require_finite,
    require_positive,
)


def synthetic_geometry(**overrides: float) -> SeparatrixGeometry:
    """Build a valid synthetic geometry with optional field overrides."""
    values: dict[str, float] = {
        "separatrix_radius_m": 0.3,
        "coil_radius_m": 0.5,
        "separatrix_length_m": 2.4,
    }
    values.update(overrides)
    return SeparatrixGeometry(**values)


def synthetic_limits(**overrides: float) -> OperationalLimits:
    """Build valid synthetic limits with optional field overrides."""
    values: dict[str, float] = {
        "external_field_t": 0.5,
        "pulse_duration_s": 0.005,
    }
    values.update(overrides)
    return OperationalLimits(**values)


def test_require_finite_accepts_and_rejects() -> None:
    """The finite guard returns the value and rejects NaN and infinity."""
    assert require_finite("x", 1.5) == 1.5
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(DeviceConfigurationError, match="x: must be finite"):
            require_finite("x", bad)


def test_require_positive_accepts_and_rejects() -> None:
    """The positive guard returns the value and rejects zero and below."""
    assert require_positive("x", 0.1) == 0.1
    for bad in (0.0, -2.0):
        with pytest.raises(DeviceConfigurationError, match="strictly positive"):
            require_positive("x", bad)
    with pytest.raises(DeviceConfigurationError, match="must be finite"):
        require_positive("x", math.nan)


def test_valid_geometry_and_derived_quantities() -> None:
    """A valid geometry derives x_s, elongation, and average beta."""
    geometry = synthetic_geometry()
    assert geometry.xs_ratio == pytest.approx(0.6)
    assert geometry.elongation == pytest.approx(2.4 / 0.6)
    assert geometry.average_beta() == pytest.approx(1.0 - 0.36 / 2.0)


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"separatrix_radius_m": 0.0}, "separatrix_radius_m"),
        ({"coil_radius_m": -1.0}, "coil_radius_m"),
        ({"separatrix_length_m": 0.0}, "separatrix_length_m"),
        ({"separatrix_radius_m": 0.5}, "strictly smaller than"),
        ({"separatrix_radius_m": 0.6}, "strictly smaller than"),
        ({"coil_radius_m": math.nan}, "coil_radius_m"),
    ],
)
def test_invalid_geometry_is_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each geometric invariant violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_geometry(**overrides)


def test_valid_limits_construct() -> None:
    """A valid limit declaration constructs unchanged."""
    assert synthetic_limits().external_field_t == 0.5


def test_zero_pulse_is_valid() -> None:
    """A zero pulse duration is representable."""
    assert synthetic_limits(pulse_duration_s=0.0).pulse_duration_s == 0.0


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"external_field_t": 0.0}, "external_field_t"),
        ({"pulse_duration_s": -1.0}, "pulse_duration_s"),
        ({"pulse_duration_s": math.inf}, "pulse_duration_s"),
    ],
)
def test_invalid_limits_are_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each limit violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_limits(**overrides)
