# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — level-0 physics record

"""Level-0 physics record of one validated FRC configuration.

The record composes the two closed forms this package implements — the
radial pressure balance across the separatrix and the empirical ``S* / E``
kinetic-scale bound — on a validated configuration together with the model
inputs the configuration does not carry, and serialises canonically with a
SHA-256 digest.

It states its own non-claims. Every number in it is a closed-form
evaluation on a declared operating point at ``computational_prototype``
maturity: no equilibrium is solved, no transport is modelled, and nothing
here describes or validates a real machine. Where the record reproduces a
number a filed source prints, that is an anchor on the arithmetic, never a
claim about the machine the source measured.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_frc_core.configuration import DeviceConfiguration
from scpn_frc_core.parameters import require_positive
from scpn_frc_core.physics.equilibrium import (
    RadialPressureBalance,
    alfven_speed_m_s,
    radial_pressure_balance,
)
from scpn_frc_core.physics.stability import (
    KineticScaleBound,
    kinetic_scale_bound,
)

LEVEL0_SCHEMA: Final = "scpn.frc-level0-physics.v1"
LEVEL0_SCHEMA_VERSION: Final = "1.0.0"
LEVEL0_NON_CLAIMS: Final = (
    (
        "closed-form evaluation of the radial pressure balance and the empirical "
        "kinetic-scale bound on a declared operating point"
    ),
    "no equilibrium, stability, compression or transport equation is solved",
    "no yield, gain, reactivity, confinement or breakeven statement",
    (
        "the empirical bound orders operating points; a point inside it is not "
        "claimed stable"
    ),
    (
        "no value describes or validates any real machine; an anchor reproduces "
        "a number the filed source prints and nothing further"
    ),
)


@dataclass(frozen=True, slots=True)
class ModelInputs:
    """Declared inputs the configuration does not carry.

    Parameters
    ----------
    particle_density_per_m3
        Total particle density; strictly positive.
    ion_mass_kg
        Ion mass; strictly positive.

    Raises
    ------
    DeviceConfigurationError
        If either input is not strictly positive or not finite.
    """

    particle_density_per_m3: float
    ion_mass_kg: float

    def __post_init__(self) -> None:
        """Validate both declared inputs.

        Raises
        ------
        DeviceConfigurationError
            If either input is not strictly positive or not finite.
        """
        require_positive("particle_density_per_m3", self.particle_density_per_m3)
        require_positive("ion_mass_kg", self.ion_mass_kg)

    def to_record(self) -> dict[str, Any]:
        """Project the inputs to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            One key per declared input.
        """
        return {
            "particle_density_per_m3": self.particle_density_per_m3,
            "ion_mass_kg": self.ion_mass_kg,
        }


@dataclass(frozen=True, slots=True)
class Level0Physics:
    """Composed level-0 record of one configuration and its inputs.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the configuration the record was built from.
    inputs
        The declared model inputs.
    balance
        The radial pressure balance.
    scale_bound
        The empirical kinetic-scale bound.
    alfven_speed_m_s
        ``B_e / sqrt(mu0 n m_i)`` of the same operating point.
    """

    configuration_digest_sha256: str
    inputs: ModelInputs
    balance: RadialPressureBalance
    scale_bound: KineticScaleBound
    alfven_speed_m_s: float

    def to_record(self) -> dict[str, Any]:
        """Project the record to a JSON-serialisable object.

        Returns
        -------
        dict[str, Any]
            The schema-tagged record with its non-claims.
        """
        return {
            "schema": LEVEL0_SCHEMA,
            "schema_version": LEVEL0_SCHEMA_VERSION,
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "inputs": self.inputs.to_record(),
            "radial_pressure_balance": self.balance.to_record(),
            "kinetic_scale_bound": self.scale_bound.to_record(),
            "alfven_speed_m_s": self.alfven_speed_m_s,
            "non_claims": list(LEVEL0_NON_CLAIMS),
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

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
        """Identify the exact record.

        Returns
        -------
        str
            SHA-256 of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def level0_physics(
    configuration: DeviceConfiguration,
    inputs: ModelInputs,
) -> Level0Physics:
    """Compose the level-0 physics record of one validated configuration.

    Parameters
    ----------
    configuration
        Validated device configuration.
    inputs
        Declared model inputs the configuration does not carry.

    Returns
    -------
    Level0Physics
        The composed record.

    Raises
    ------
    DeviceConfigurationError
        If a declared input or a derived quantity falls outside its
        model bound; the refusals of the composed relations are raised
        unchanged, with the field they name.
    """
    balance = radial_pressure_balance(configuration, inputs.particle_density_per_m3)
    bound = kinetic_scale_bound(
        configuration, inputs.particle_density_per_m3, inputs.ion_mass_kg
    )
    return Level0Physics(
        configuration_digest_sha256=configuration.digest_sha256(),
        inputs=inputs,
        balance=balance,
        scale_bound=bound,
        alfven_speed_m_s=alfven_speed_m_s(
            configuration.limits.external_field_t,
            inputs.particle_density_per_m3,
            inputs.ion_mass_kg,
        ),
    )
