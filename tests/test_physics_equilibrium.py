# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — radial pressure balance tests

"""Tests of the radial pressure balance across the separatrix."""

from __future__ import annotations

import math

import pytest
from physics_fixtures import reference_configuration

from scpn_frc_core.errors import DeviceConfigurationError
from scpn_frc_core.physics.equilibrium import (
    DEUTERON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    MU0,
    PROTON_MASS_KG,
    alfven_speed_m_s,
    magnetic_pressure_pa,
    radial_pressure_balance,
    require_average_beta,
)


def test_magnetic_pressure_is_the_closed_form() -> None:
    """The magnetic pressure is B^2 over twice the permeability."""
    assert magnetic_pressure_pa(0.5) == 0.5 * 0.5 / (2.0 * MU0)


@pytest.mark.parametrize("field", [0.0, -1.0, math.inf, math.nan])
def test_magnetic_pressure_refuses_a_field_outside_its_domain(field: float) -> None:
    """A field that is not strictly positive and finite is refused."""
    with pytest.raises(DeviceConfigurationError, match="field_t"):
        magnetic_pressure_pa(field)


def test_average_beta_passes_a_value_inside_the_domain() -> None:
    """A beta strictly inside the unit interval is returned unchanged."""
    assert require_average_beta(0.75) == 0.75


@pytest.mark.parametrize("beta", [0.0, 1.0, -0.1, 1.5])
def test_average_beta_refuses_a_value_outside_the_domain(beta: float) -> None:
    """The relation is refused outside ``0 < beta < 1``, never clamped."""
    with pytest.raises(DeviceConfigurationError, match="average_beta"):
        require_average_beta(beta)


def test_balance_composes_the_configuration_and_the_declared_density() -> None:
    """Every field follows from the configuration and the declared density."""
    configuration = reference_configuration()
    balance = radial_pressure_balance(configuration, 1.0e20)
    geometry = configuration.geometry
    assert balance.separatrix_ratio == geometry.xs_ratio
    assert balance.average_beta == geometry.average_beta()
    assert balance.external_field_t == configuration.limits.external_field_t
    assert balance.magnetic_pressure_pa == magnetic_pressure_pa(0.5)
    assert balance.particle_density_per_m3 == 1.0e20


def test_peak_pressure_equals_the_magnetic_pressure_at_the_null() -> None:
    """The field is zero at the null, so the plasma carries all of it."""
    balance = radial_pressure_balance(reference_configuration(), 1.0e20)
    assert balance.peak_plasma_pressure_pa == balance.magnetic_pressure_pa


def test_average_pressure_is_beta_times_the_magnetic_pressure() -> None:
    """Averaging the balance over the cross-section introduces beta."""
    balance = radial_pressure_balance(reference_configuration(), 1.0e20)
    assert balance.average_plasma_pressure_pa == (
        balance.average_beta * balance.magnetic_pressure_pa
    )
    assert balance.average_plasma_pressure_pa < balance.peak_plasma_pressure_pa


def test_total_temperature_inverts_the_ideal_gas_relation() -> None:
    """The temperature is the average pressure per particle, in eV."""
    balance = radial_pressure_balance(reference_configuration(), 1.0e20)
    assert balance.total_temperature_ev == (
        balance.average_plasma_pressure_pa / (1.0e20 * ELEMENTARY_CHARGE_C)
    )


@pytest.mark.parametrize("density", [0.0, -1.0, math.inf, math.nan])
def test_balance_refuses_a_density_outside_its_domain(density: float) -> None:
    """A density that is not strictly positive and finite is refused."""
    with pytest.raises(DeviceConfigurationError, match="particle_density_per_m3"):
        radial_pressure_balance(reference_configuration(), density)


def test_balance_record_keys_are_the_declared_fields() -> None:
    """The record carries one key per field, in declaration order."""
    balance = radial_pressure_balance(reference_configuration(), 1.0e20)
    assert list(balance.to_record()) == [
        "separatrix_ratio",
        "average_beta",
        "external_field_t",
        "magnetic_pressure_pa",
        "peak_plasma_pressure_pa",
        "average_plasma_pressure_pa",
        "particle_density_per_m3",
        "total_temperature_ev",
    ]


def test_alfven_speed_is_the_closed_form() -> None:
    """The Alfvén speed is the field over the root of the mass density."""
    assert alfven_speed_m_s(0.5, 1.0e20, DEUTERON_MASS_KG) == 0.5 / math.sqrt(
        MU0 * 1.0e20 * DEUTERON_MASS_KG
    )


def test_alfven_speed_is_higher_for_the_lighter_ion() -> None:
    """A proton plasma carries the same field faster than a deuteron one."""
    proton = alfven_speed_m_s(0.5, 1.0e20, PROTON_MASS_KG)
    deuteron = alfven_speed_m_s(0.5, 1.0e20, DEUTERON_MASS_KG)
    assert proton > deuteron


@pytest.mark.parametrize(
    ("field", "density", "mass", "field_name"),
    [
        (0.0, 1.0e20, DEUTERON_MASS_KG, "field_t"),
        (0.5, 0.0, DEUTERON_MASS_KG, "particle_density_per_m3"),
        (0.5, 1.0e20, 0.0, "ion_mass_kg"),
        (math.nan, 1.0e20, DEUTERON_MASS_KG, "field_t"),
    ],
)
def test_alfven_speed_refuses_each_argument_in_the_direction_it_is_wrong(
    field: float, density: float, mass: float, field_name: str
) -> None:
    """Each refusal names the field that is wrong."""
    with pytest.raises(DeviceConfigurationError, match=field_name):
        alfven_speed_m_s(field, density, mass)
