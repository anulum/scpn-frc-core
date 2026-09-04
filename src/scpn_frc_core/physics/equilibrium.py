# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — radial pressure balance

"""Radial pressure balance of a field-reversed configuration.

An FRC is confined by a poloidal field alone. Outside the separatrix the
external field ``B_e`` presses inward; inside, the field passes through a
null where the plasma pressure alone holds the column open. Balancing the
two across the separatrix gives the peak pressure ``p_max = B_e^2 / 2 mu0``
at the null, and averaging the balance over the separatrix cross-section
gives the standard FRC average-beta relation
``<beta> = 1 - x_s^2 / 2`` with ``x_s = r_s / r_c``, which
:class:`~scpn_frc_core.parameters.SeparatrixGeometry` already carries.

This module composes those two results on a validated configuration and a
declared particle density, and stops there. It solves no equilibrium: it
evaluates closed forms whose derivation is in the filed sources, and every
quantity it reports is a closed-form evaluation on a declared operating
point, never a statement about a machine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_frc_core.configuration import DeviceConfiguration
from scpn_frc_core.errors import DeviceConfigurationError
from scpn_frc_core.parameters import require_positive

#: Vacuum permeability, SI, CODATA.
MU0: Final = 1.25663706212e-6
#: Elementary charge in coulomb, exact by the 2019 SI redefinition.
ELEMENTARY_CHARGE_C: Final = 1.602176634e-19
#: Proton rest mass in kilogram, CODATA.
PROTON_MASS_KG: Final = 1.67262192369e-27
#: Deuteron rest mass in kilogram, CODATA.
DEUTERON_MASS_KG: Final = 3.3435837724e-27


def require_average_beta(beta: float) -> float:
    """Return ``beta`` when it lies strictly inside the physical domain.

    Parameters
    ----------
    beta
        Average beta of the operating point.

    Returns
    -------
    float
        The validated average beta.

    Raises
    ------
    DeviceConfigurationError
        If ``beta`` is not strictly between zero and one.

    Notes
    -----
    A validated separatrix has ``0 < x_s < 1`` and therefore
    ``0.5 < <beta> < 1``, so the refusal is unreachable from
    :func:`radial_pressure_balance`. The check stays because this is the
    family's public domain guard for a beta a caller supplies directly,
    and it is tested through that surface rather than through the
    composition, which cannot reach it.
    """
    if not 0.0 < beta < 1.0:
        raise DeviceConfigurationError(
            f"average_beta: must be strictly between zero and one, got {beta!r}"
        )
    return beta


@dataclass(frozen=True, slots=True)
class RadialPressureBalance:
    """Pressure balance across the separatrix of one operating point.

    Parameters
    ----------
    separatrix_ratio
        ``x_s = r_s / r_c`` of the validated geometry.
    average_beta
        ``<beta> = 1 - x_s^2 / 2``.
    external_field_t
        External field ``B_e`` outside the separatrix, in tesla.
    magnetic_pressure_pa
        ``B_e^2 / 2 mu0``.
    peak_plasma_pressure_pa
        Plasma pressure at the field null, equal to the magnetic pressure
        because the field there is zero.
    average_plasma_pressure_pa
        ``<beta>`` times the magnetic pressure.
    particle_density_per_m3
        Declared total particle density used to convert pressure to
        temperature.
    total_temperature_ev
        ``<p> / (n e)``: the sum of the electron and ion temperatures, in
        electronvolt. The split between species is not modelled and is
        not claimed.
    """

    separatrix_ratio: float
    average_beta: float
    external_field_t: float
    magnetic_pressure_pa: float
    peak_plasma_pressure_pa: float
    average_plasma_pressure_pa: float
    particle_density_per_m3: float
    total_temperature_ev: float

    def to_record(self) -> dict[str, Any]:
        """Project the balance to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            One key per field, in the declaration order of the class.
        """
        return {
            "separatrix_ratio": self.separatrix_ratio,
            "average_beta": self.average_beta,
            "external_field_t": self.external_field_t,
            "magnetic_pressure_pa": self.magnetic_pressure_pa,
            "peak_plasma_pressure_pa": self.peak_plasma_pressure_pa,
            "average_plasma_pressure_pa": self.average_plasma_pressure_pa,
            "particle_density_per_m3": self.particle_density_per_m3,
            "total_temperature_ev": self.total_temperature_ev,
        }


def magnetic_pressure_pa(field_t: float) -> float:
    """Return the magnetic pressure of a field.

    Parameters
    ----------
    field_t
        Magnetic flux density in tesla; strictly positive.

    Returns
    -------
    float
        ``B^2 / 2 mu0`` in pascal.

    Raises
    ------
    DeviceConfigurationError
        If the field is not strictly positive or is not finite.
    """
    field = require_positive("field_t", field_t)
    return field * field / (2.0 * MU0)


def radial_pressure_balance(
    configuration: DeviceConfiguration,
    particle_density_per_m3: float,
) -> RadialPressureBalance:
    """Compose the radial pressure balance of one validated configuration.

    Parameters
    ----------
    configuration
        Validated device configuration; its separatrix geometry supplies
        ``x_s`` and its limits supply the external field.
    particle_density_per_m3
        Declared total particle density; strictly positive. The
        configuration does not carry a density, so it is a declared model
        input and is recorded as one.

    Returns
    -------
    RadialPressureBalance
        The composed balance.

    Raises
    ------
    DeviceConfigurationError
        If the density is not strictly positive or not finite, or if the
        average beta of the geometry falls outside ``(0, 1)``.
    """
    density = require_positive("particle_density_per_m3", particle_density_per_m3)
    geometry = configuration.geometry
    beta = require_average_beta(geometry.average_beta())
    field = configuration.limits.external_field_t
    magnetic = magnetic_pressure_pa(field)
    average_pressure = beta * magnetic
    return RadialPressureBalance(
        separatrix_ratio=geometry.xs_ratio,
        average_beta=beta,
        external_field_t=field,
        magnetic_pressure_pa=magnetic,
        peak_plasma_pressure_pa=magnetic,
        average_plasma_pressure_pa=average_pressure,
        particle_density_per_m3=density,
        total_temperature_ev=average_pressure / (density * ELEMENTARY_CHARGE_C),
    )


def alfven_speed_m_s(
    field_t: float,
    particle_density_per_m3: float,
    ion_mass_kg: float,
) -> float:
    """Return the Alfvén speed of the external field in the plasma.

    Parameters
    ----------
    field_t
        Magnetic flux density in tesla; strictly positive.
    particle_density_per_m3
        Particle density; strictly positive.
    ion_mass_kg
        Ion mass; strictly positive.

    Returns
    -------
    float
        ``B / sqrt(mu0 n m_i)`` in metre per second. The square root is
        the IEEE-754 correctly rounded one, which is bit-identical on
        every conforming platform; no transcendental enters.

    Raises
    ------
    DeviceConfigurationError
        If any argument is not strictly positive or not finite.
    """
    field = require_positive("field_t", field_t)
    density = require_positive("particle_density_per_m3", particle_density_per_m3)
    mass = require_positive("ion_mass_kg", ion_mass_kg)
    return field / math.sqrt(MU0 * density * mass)
