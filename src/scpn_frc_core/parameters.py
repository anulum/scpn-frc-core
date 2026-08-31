# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — field-reversed-configuration parameter model

"""Validated parameter objects of a field-reversed configuration.

The derived quantity implements one standard result and nothing more:
the FRC average-beta relation ``<beta> = 1 - x_s^2 / 2`` with
``x_s = r_s / r_c`` (M. Tuszewski, Nucl. Fusion 28 (1988) 2033). It is
a rough consistency instrument with documented applicability bounds; no
claim about any real machine follows from it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scpn_frc_core.errors import DeviceConfigurationError


def require_finite(name: str, value: float) -> float:
    """Return ``value`` when finite, otherwise fail closed.

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
    DeviceConfigurationError
        If ``value`` is NaN or infinite; non-finite input is rejected,
        never clamped.
    """
    if not math.isfinite(value):
        raise DeviceConfigurationError(f"{name}: must be finite, got {value!r}")
    return value


def require_positive(name: str, value: float) -> float:
    """Return ``value`` when finite and strictly positive.

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
    DeviceConfigurationError
        If ``value`` is non-finite or not strictly positive.
    """
    require_finite(name, value)
    if value <= 0.0:
        raise DeviceConfigurationError(
            f"{name}: must be strictly positive, got {value!r}"
        )
    return value


@dataclass(frozen=True, slots=True)
class SeparatrixGeometry:
    """Separatrix and confinement-coil geometry of an FRC.

    Parameters
    ----------
    separatrix_radius_m
        Separatrix radius ``r_s`` in metres; strictly positive and
        strictly smaller than ``coil_radius_m``.
    coil_radius_m
        Confinement-coil radius ``r_c`` in metres; strictly positive.
    separatrix_length_m
        Separatrix length ``l_s`` in metres; strictly positive.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or outside its model bound.
    """

    separatrix_radius_m: float
    coil_radius_m: float
    separatrix_length_m: float

    def __post_init__(self) -> None:
        """Validate every geometric invariant.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or outside its model bound.
        """
        require_positive("separatrix_radius_m", self.separatrix_radius_m)
        require_positive("coil_radius_m", self.coil_radius_m)
        require_positive("separatrix_length_m", self.separatrix_length_m)
        if self.separatrix_radius_m >= self.coil_radius_m:
            raise DeviceConfigurationError(
                "separatrix_radius_m: must be strictly smaller than "
                f"coil_radius_m ({self.separatrix_radius_m!r} >= "
                f"{self.coil_radius_m!r})"
            )

    @property
    def xs_ratio(self) -> float:
        """Separatrix-to-coil radius ratio ``x_s = r_s / r_c``.

        Returns
        -------
        float
            Ratio in ``(0, 1)`` for a validated geometry.
        """
        return self.separatrix_radius_m / self.coil_radius_m

    @property
    def elongation(self) -> float:
        """Separatrix elongation ``E = l_s / (2 r_s)``.

        Returns
        -------
        float
            Elongation of the validated separatrix.
        """
        return self.separatrix_length_m / (2.0 * self.separatrix_radius_m)

    def average_beta(self) -> float:
        """FRC average beta from the separatrix ratio.

        Returns
        -------
        float
            ``<beta> = 1 - x_s^2 / 2`` (Tuszewski, NF 28 (1988) 2033);
            an equilibrium average-beta relation, not a performance
            claim.
        """
        return 1.0 - self.xs_ratio**2 / 2.0


@dataclass(frozen=True, slots=True)
class OperationalLimits:
    """Declared operating-point limits of an FRC configuration.

    Parameters
    ----------
    external_field_t
        External axial confinement field ``B_e`` in tesla; strictly
        positive.
    pulse_duration_s
        Declared pulse duration in seconds; non-negative.

    Raises
    ------
    DeviceConfigurationError
        If any limit is non-finite or outside its model bound.
    """

    external_field_t: float
    pulse_duration_s: float

    def __post_init__(self) -> None:
        """Validate every declared limit.

        Raises
        ------
        DeviceConfigurationError
            If any limit is non-finite or outside its model bound.
        """
        require_positive("external_field_t", self.external_field_t)
        require_finite("pulse_duration_s", self.pulse_duration_s)
        if self.pulse_duration_s < 0.0:
            raise DeviceConfigurationError(
                f"pulse_duration_s: must be non-negative, got {self.pulse_duration_s!r}"
            )
