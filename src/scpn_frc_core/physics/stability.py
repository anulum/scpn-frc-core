# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — empirical kinetic stability bound

"""The empirical ``S* / E`` bound of a field-reversed configuration.

An FRC is formally unstable to the internal tilt mode in ideal
magnetohydrodynamics, yet experiments hold configurations together for
many Alfvén times. The observed separation is organised by how few ion
gyro-scales fit across the plasma: the fewer there are, the further the
configuration is from the fluid limit the instability is derived in.

The scale count used here is ``S* = r_s / delta_i``, the separatrix radius
over the ion skin depth ``delta_i = c / omega_pi``, and the bound is
``S* / E < 3.5`` against the elongation ``E`` (A. A. Bala et al.,
arXiv:2204.07978v1 (2022), their equation 14, quoting the experimental
compilations that established it).

The bound is empirical and this module treats it as exactly that. It
reports the ratio and whether the ratio sits below the published number;
it does not predict that a configuration is stable, and a configuration
below the bound is not thereby claimed to survive.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_frc_core.configuration import DeviceConfiguration
from scpn_frc_core.parameters import require_positive
from scpn_frc_core.physics.equilibrium import (
    ELEMENTARY_CHARGE_C,
)

#: Vacuum permittivity in farad per metre, CODATA.
VACUUM_PERMITTIVITY_F_PER_M: Final = 8.8541878128e-12
#: Speed of light in vacuum, metre per second, exact by SI definition.
SPEED_OF_LIGHT_M_PER_S: Final = 299792458.0
#: Published bound of the empirical criterion ``S* / E < 3.5``
#: (Bala et al., arXiv:2204.07978v1, equation 14).
EMPIRICAL_SE_BOUND: Final = 3.5


def ion_plasma_frequency_rad_s(
    particle_density_per_m3: float,
    ion_mass_kg: float,
) -> float:
    """Return the ion plasma frequency.

    Parameters
    ----------
    particle_density_per_m3
        Ion density; strictly positive.
    ion_mass_kg
        Ion mass; strictly positive.

    Returns
    -------
    float
        ``sqrt(n e^2 / (eps0 m_i))`` in radian per second.

    Raises
    ------
    DeviceConfigurationError
        If either argument is not strictly positive or not finite.
    """
    density = require_positive("particle_density_per_m3", particle_density_per_m3)
    mass = require_positive("ion_mass_kg", ion_mass_kg)
    return math.sqrt(
        density
        * ELEMENTARY_CHARGE_C
        * ELEMENTARY_CHARGE_C
        / (VACUUM_PERMITTIVITY_F_PER_M * mass)
    )


def ion_skin_depth_m(
    particle_density_per_m3: float,
    ion_mass_kg: float,
) -> float:
    """Return the ion skin depth.

    Parameters
    ----------
    particle_density_per_m3
        Ion density; strictly positive.
    ion_mass_kg
        Ion mass; strictly positive.

    Returns
    -------
    float
        ``c / omega_pi`` in metre.

    Raises
    ------
    DeviceConfigurationError
        If either argument is not strictly positive or not finite.
    """
    return SPEED_OF_LIGHT_M_PER_S / ion_plasma_frequency_rad_s(
        particle_density_per_m3, ion_mass_kg
    )


@dataclass(frozen=True, slots=True)
class KineticScaleBound:
    """The ``S* / E`` ratio of one operating point against its bound.

    Parameters
    ----------
    ion_skin_depth_m
        ``delta_i = c / omega_pi`` of the declared density and ion mass.
    scale_count
        ``S* = r_s / delta_i``: how many ion skin depths fit in the
        separatrix radius.
    elongation
        ``E = l_s / (2 r_s)`` of the validated separatrix.
    ratio
        ``S* / E``.
    bound
        The published bound, :data:`EMPIRICAL_SE_BOUND`.
    within_bound
        Whether ``ratio < bound``. A configuration inside the bound is
        not thereby claimed stable; the bound is an empirical ordering,
        not a prediction.
    """

    ion_skin_depth_m: float
    scale_count: float
    elongation: float
    ratio: float
    bound: float
    within_bound: bool

    def to_record(self) -> dict[str, Any]:
        """Project the bound to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            One key per field, in the declaration order of the class.
        """
        return {
            "ion_skin_depth_m": self.ion_skin_depth_m,
            "scale_count": self.scale_count,
            "elongation": self.elongation,
            "ratio": self.ratio,
            "bound": self.bound,
            "within_bound": self.within_bound,
        }


def kinetic_scale_bound(
    configuration: DeviceConfiguration,
    particle_density_per_m3: float,
    ion_mass_kg: float,
) -> KineticScaleBound:
    """Evaluate the empirical ``S* / E`` bound on one configuration.

    Parameters
    ----------
    configuration
        Validated device configuration supplying ``r_s`` and ``l_s``.
    particle_density_per_m3
        Declared ion density; strictly positive.
    ion_mass_kg
        Declared ion mass; strictly positive.

    Returns
    -------
    KineticScaleBound
        The composed ratio and its verdict against the published bound.

    Raises
    ------
    DeviceConfigurationError
        If the density or the ion mass is not strictly positive or not
        finite.
    """
    skin_depth = ion_skin_depth_m(particle_density_per_m3, ion_mass_kg)
    geometry = configuration.geometry
    scale_count = geometry.separatrix_radius_m / skin_depth
    elongation = geometry.elongation
    ratio = scale_count / elongation
    return KineticScaleBound(
        ion_skin_depth_m=skin_depth,
        scale_count=scale_count,
        elongation=elongation,
        ratio=ratio,
        bound=EMPIRICAL_SE_BOUND,
        within_bound=ratio < EMPIRICAL_SE_BOUND,
    )
