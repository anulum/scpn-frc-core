# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — level-0 physics fixtures

"""Fixtures of the level-0 physics tests: one synthetic, one anchored.

The **reference** pair is synthetic. Its numbers are round and were chosen
to make the arithmetic of a test legible; they describe nothing.

The **anchor** pair is built from values a filed source prints. Zhu & Wu
(arXiv:2607.11908v1, 2026) give a table of as-built Yingguang-1 hardware
and of the operating point their whole-device model reproduces, and the
values below are copied from it.

Printed by the source, and therefore anchor values:

- coil inner diameter ``12.4 cm``, so the coil radius is ``0.062 m``;
- active coil length ``36 cm``;
- fill density ``2e15 cm^-3``, so ``2e21 m^-3``;
- working ion deuterium.

Declared here, and said to be declared:

- the separatrix radius and length. The source's separatrix radius is a
  simulation result printed as "approximately 1 cm", not a measured
  device dimension, so it is **not** used as an anchor value; the values
  below are declared and only the coil bore that bounds them is printed.
- the external field. The source prints coil currents, not the field the
  configuration model carries.

Reproducing a printed value is an anchor, never a claim about that
machine.
"""

from __future__ import annotations

from geometry_fixtures import (
    ANCHOR_COIL_RADIUS_M,
    ANCHOR_EXTERNAL_FIELD_T,
    ANCHOR_FILL_DENSITY_PER_M3,
    ANCHOR_SEPARATRIX_LENGTH_M,
    ANCHOR_SEPARATRIX_RADIUS_M,
)

from scpn_frc_core.configuration import DeviceConfiguration, RegistryBinding
from scpn_frc_core.parameters import OperationalLimits, SeparatrixGeometry
from scpn_frc_core.physics import DEUTERON_MASS_KG, ModelInputs

REGISTRY = RegistryBinding(version="1.0.0", digest_sha256="0" * 64)

#: The printed hardware has one home: :mod:`geometry_fixtures`. These are
#: re-exported here so the physics tests read them under the names they
#: use, without a second copy of any printed value.
ANCHOR_ION_MASS_KG = DEUTERON_MASS_KG


def reference_configuration() -> DeviceConfiguration:
    """Build the synthetic reference configuration.

    Returns
    -------
    DeviceConfiguration
        A validated configuration whose numbers are round and describe
        nothing.
    """
    return DeviceConfiguration(
        identifier="field_reversed_configuration",
        geometry=SeparatrixGeometry(
            separatrix_radius_m=0.3,
            coil_radius_m=0.5,
            separatrix_length_m=2.4,
        ),
        limits=OperationalLimits(external_field_t=0.5, pulse_duration_s=0.005),
        registry=REGISTRY,
    )


def reference_inputs() -> ModelInputs:
    """Build the synthetic reference model inputs.

    Returns
    -------
    ModelInputs
        Round declared inputs for the reference configuration.
    """
    return ModelInputs(
        particle_density_per_m3=1.0e20,
        ion_mass_kg=DEUTERON_MASS_KG,
    )


def anchor_configuration() -> DeviceConfiguration:
    """Build the configuration anchored on the printed hardware.

    Returns
    -------
    DeviceConfiguration
        A validated configuration whose coil radius is the printed one
        and whose separatrix is declared.
    """
    return DeviceConfiguration(
        identifier="field_reversed_configuration",
        geometry=SeparatrixGeometry(
            separatrix_radius_m=ANCHOR_SEPARATRIX_RADIUS_M,
            coil_radius_m=ANCHOR_COIL_RADIUS_M,
            separatrix_length_m=ANCHOR_SEPARATRIX_LENGTH_M,
        ),
        limits=OperationalLimits(
            external_field_t=ANCHOR_EXTERNAL_FIELD_T,
            pulse_duration_s=0.005,
        ),
        registry=REGISTRY,
    )


def anchor_inputs() -> ModelInputs:
    """Build the model inputs anchored on the printed operating point.

    Returns
    -------
    ModelInputs
        The printed fill density and the printed working ion.
    """
    return ModelInputs(
        particle_density_per_m3=ANCHOR_FILL_DENSITY_PER_M3,
        ion_mass_kg=ANCHOR_ION_MASS_KG,
    )
