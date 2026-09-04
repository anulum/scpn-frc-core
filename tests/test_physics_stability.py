# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — kinetic-scale bound tests

"""Tests of the empirical ``S* / E`` kinetic-scale bound."""

from __future__ import annotations

import math

import pytest
from geometry_fixtures import (
    ANCHOR_ACTIVE_COIL_LENGTH_M,
    ANCHOR_COIL_COUNT,
    ANCHOR_COIL_INNER_DIAMETER_M,
    ANCHOR_COIL_PITCH_M,
    ANCHOR_COIL_RADIUS_M,
    ANCHOR_FILL_DENSITY_PER_M3,
)
from physics_fixtures import (
    anchor_configuration,
    anchor_inputs,
    reference_configuration,
)

from scpn_frc_core.errors import DeviceConfigurationError
from scpn_frc_core.parameters import OperationalLimits, SeparatrixGeometry
from scpn_frc_core.physics.equilibrium import (
    DEUTERON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    PROTON_MASS_KG,
)
from scpn_frc_core.physics.stability import (
    EMPIRICAL_SE_BOUND,
    SPEED_OF_LIGHT_M_PER_S,
    VACUUM_PERMITTIVITY_F_PER_M,
    ion_plasma_frequency_rad_s,
    ion_skin_depth_m,
    kinetic_scale_bound,
)


def test_ion_plasma_frequency_is_the_closed_form() -> None:
    """The frequency is the root of n e^2 over eps0 m_i."""
    assert ion_plasma_frequency_rad_s(1.0e20, DEUTERON_MASS_KG) == math.sqrt(
        1.0e20
        * ELEMENTARY_CHARGE_C
        * ELEMENTARY_CHARGE_C
        / (VACUUM_PERMITTIVITY_F_PER_M * DEUTERON_MASS_KG)
    )


def test_ion_plasma_frequency_rises_with_the_square_root_of_density() -> None:
    """Four times the density is twice the frequency."""
    one = ion_plasma_frequency_rad_s(1.0e20, DEUTERON_MASS_KG)
    four = ion_plasma_frequency_rad_s(4.0e20, DEUTERON_MASS_KG)
    assert math.isclose(four, 2.0 * one, rel_tol=1.0e-15)


def test_ion_skin_depth_is_light_speed_over_the_frequency() -> None:
    """The skin depth inverts the frequency at the speed of light."""
    assert ion_skin_depth_m(1.0e20, DEUTERON_MASS_KG) == (
        SPEED_OF_LIGHT_M_PER_S / ion_plasma_frequency_rad_s(1.0e20, DEUTERON_MASS_KG)
    )


def test_the_heavier_ion_has_the_deeper_skin_depth() -> None:
    """A deuteron plasma admits the field further than a proton one."""
    assert ion_skin_depth_m(1.0e20, DEUTERON_MASS_KG) > ion_skin_depth_m(
        1.0e20, PROTON_MASS_KG
    )


@pytest.mark.parametrize(
    ("density", "mass", "field_name"),
    [
        (0.0, DEUTERON_MASS_KG, "particle_density_per_m3"),
        (-1.0, DEUTERON_MASS_KG, "particle_density_per_m3"),
        (math.inf, DEUTERON_MASS_KG, "particle_density_per_m3"),
        (1.0e20, 0.0, "ion_mass_kg"),
        (1.0e20, math.nan, "ion_mass_kg"),
    ],
)
def test_the_frequency_refuses_each_argument_by_name(
    density: float, mass: float, field_name: str
) -> None:
    """Each refusal names the field that is wrong."""
    with pytest.raises(DeviceConfigurationError, match=field_name):
        ion_plasma_frequency_rad_s(density, mass)


def test_the_bound_composes_the_configuration_and_the_declared_inputs() -> None:
    """Every field follows from the geometry and the declared inputs."""
    configuration = reference_configuration()
    bound = kinetic_scale_bound(configuration, 1.0e20, DEUTERON_MASS_KG)
    depth = ion_skin_depth_m(1.0e20, DEUTERON_MASS_KG)
    assert bound.ion_skin_depth_m == depth
    assert bound.scale_count == configuration.geometry.separatrix_radius_m / depth
    assert bound.elongation == configuration.geometry.elongation
    assert bound.ratio == bound.scale_count / bound.elongation


def test_the_bound_constant_is_the_number_the_source_prints() -> None:
    """Bala et al. print 3.5 in their equation 14; the code carries it."""
    assert EMPIRICAL_SE_BOUND == 3.5
    bound = kinetic_scale_bound(reference_configuration(), 1.0e20, DEUTERON_MASS_KG)
    assert bound.bound == 3.5


def test_the_verdict_turns_exactly_at_the_published_bound() -> None:
    """A point below the bound is inside it and a point above is not.

    The two configurations differ only in the separatrix length, which
    enters through the elongation alone, so the pair isolates the bound
    rather than exercising two unrelated operating points.
    """
    registry = reference_configuration().registry
    configurations = [
        type(reference_configuration())(
            identifier="field_reversed_configuration",
            geometry=SeparatrixGeometry(
                separatrix_radius_m=0.3,
                coil_radius_m=0.5,
                separatrix_length_m=length,
            ),
            limits=OperationalLimits(external_field_t=0.5, pulse_duration_s=0.005),
            registry=registry,
        )
        for length in (2.4, 0.9)
    ]
    long_bound, short_bound = (
        kinetic_scale_bound(configuration, 1.0e20, DEUTERON_MASS_KG)
        for configuration in configurations
    )
    assert long_bound.ratio < short_bound.ratio
    assert long_bound.within_bound is (long_bound.ratio < EMPIRICAL_SE_BOUND)
    assert short_bound.within_bound is (short_bound.ratio < EMPIRICAL_SE_BOUND)
    assert long_bound.within_bound != short_bound.within_bound


def test_bound_record_keys_are_the_declared_fields() -> None:
    """The record carries one key per field, in declaration order."""
    bound = kinetic_scale_bound(reference_configuration(), 1.0e20, DEUTERON_MASS_KG)
    assert list(bound.to_record()) == [
        "ion_skin_depth_m",
        "scale_count",
        "elongation",
        "ratio",
        "bound",
        "within_bound",
    ]


def test_anchor_reproduces_the_printed_coil_geometry_from_the_built_objects() -> None:
    """The printed hardware is recoverable from the built configuration.

    Both equalities are exact in binary and were checked before being
    written: half of 0.124 is 0.062, and eight times 0.045 is 0.36.
    """
    configuration = anchor_configuration()
    assert configuration.geometry.coil_radius_m == ANCHOR_COIL_INNER_DIAMETER_M / 2.0
    assert configuration.geometry.coil_radius_m == ANCHOR_COIL_RADIUS_M
    assert ANCHOR_COIL_COUNT * ANCHOR_COIL_PITCH_M == ANCHOR_ACTIVE_COIL_LENGTH_M


def test_anchor_separatrix_fits_inside_the_printed_coil_bore() -> None:
    """The declared separatrix is bounded by the printed hardware."""
    geometry = anchor_configuration().geometry
    assert geometry.separatrix_radius_m < ANCHOR_COIL_RADIUS_M
    assert geometry.separatrix_length_m < ANCHOR_ACTIVE_COIL_LENGTH_M


def test_anchor_density_reaches_the_bound_through_the_built_record() -> None:
    """The printed fill density is what the skin depth is computed from."""
    inputs = anchor_inputs()
    assert inputs.particle_density_per_m3 == ANCHOR_FILL_DENSITY_PER_M3
    bound = kinetic_scale_bound(
        anchor_configuration(),
        inputs.particle_density_per_m3,
        inputs.ion_mass_kg,
    )
    assert bound.ion_skin_depth_m == ion_skin_depth_m(
        ANCHOR_FILL_DENSITY_PER_M3, DEUTERON_MASS_KG
    )
    assert bound.elongation == 7.5
