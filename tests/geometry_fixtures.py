# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — device geometry fixtures

"""Fixtures of the device-model tests: one synthetic, one anchored.

The **reference** pair is synthetic. Its numbers are round and were chosen
to make the arithmetic of a test legible; they describe nothing.

The **anchor** pair is built from the as-built Yingguang-1 hardware that
Zhu & Wu print in Table I of arXiv:2607.11908v1 (2026). This module is the
one home of those printed values; the physics fixtures import the ones
they need from here rather than restating them.

Printed by the source, and therefore anchor values:

- coil inner diameter ``12.4 cm``, so the coil bore radius is ``0.062 m``;
- quartz tube radii ``5.25 / 5.5 cm``, so a wall of ``0.0025 m``;
- active coil length ``36 cm``;
- eight coils of ``3.5 cm`` width on a ``4.5 cm`` axial pitch;
- fill density ``2e15 cm^-3``, so ``2e21 m^-3``;
- working ion deuterium.

Declared here, and said to be declared:

- the separatrix radius and length. The source's separatrix radius is a
  simulation result printed as "approximately 1 cm", not a measured device
  dimension, so it is **not** an anchor value; only the coil bore and the
  quartz bore that contain it are printed.
- the separatrix shape index. The source of the shape function
  (Ma et al., arXiv:2103.00839v1, equation 13) names ``m = 2`` as the
  ellipse; the anchor uses that value and declares it.
- the coil winding thickness, the end-wall thickness and the external
  field. Zhu & Wu print coil currents, not a winding thickness or a field.

Reproducing a printed value is an anchor, never a claim about that
machine.
"""

from __future__ import annotations

from scpn_frc_core.configuration import DeviceConfiguration, RegistryBinding
from scpn_frc_core.geometry.device import DeviceGeometry
from scpn_frc_core.parameters import OperationalLimits, SeparatrixGeometry

REGISTRY = RegistryBinding(version="1.0.0", digest_sha256="0" * 64)

#: Coil inner diameter printed by Zhu & Wu, Table I: 12.4 cm.
ANCHOR_COIL_INNER_DIAMETER_M = 0.124
#: Half of the printed coil inner diameter; exact in binary.
ANCHOR_COIL_RADIUS_M = ANCHOR_COIL_INNER_DIAMETER_M / 2.0
#: Quartz confinement tube radii printed by Zhu & Wu, Table I: 5.25 / 5.5 cm.
ANCHOR_QUARTZ_INNER_RADIUS_M = 0.0525
ANCHOR_QUARTZ_OUTER_RADIUS_M = 0.055
#: Wall thickness implied by the two printed radii. It is derived rather
#: than written down: the difference is NOT the decimal 0.0025 in binary,
#: and writing that literal would put a value in the fixture that the two
#: printed radii do not have between them. Adding this back to the printed
#: inner radius reproduces the printed outer radius exactly, which is the
#: property the anchor test asserts.
ANCHOR_QUARTZ_WALL_THICKNESS_M = (
    ANCHOR_QUARTZ_OUTER_RADIUS_M - ANCHOR_QUARTZ_INNER_RADIUS_M
)
#: Active coil length printed by Zhu & Wu, Table I: 36 cm.
ANCHOR_ACTIVE_COIL_LENGTH_M = 0.36
#: Coil count, width and axial pitch printed by Zhu & Wu, Table I.
ANCHOR_COIL_COUNT = 8
ANCHOR_COIL_WIDTH_M = 0.035
ANCHOR_COIL_PITCH_M = 0.045
#: Fill density printed by Zhu & Wu, Table I: 2e15 cm^-3.
ANCHOR_FILL_DENSITY_PER_M3 = 2.0e21

#: Declared: the source prints no separatrix radius that is a device
#: dimension, only a simulation result given as "approximately 1 cm".
ANCHOR_SEPARATRIX_RADIUS_M = 0.02
#: Declared, and bounded above by the printed active coil length.
ANCHOR_SEPARATRIX_LENGTH_M = 0.30
#: Declared: the ellipse of the shape function's own source.
ANCHOR_SHAPE_INDEX = 2.0
#: Declared: the source prints coil currents, not a winding thickness.
ANCHOR_COIL_WALL_THICKNESS_M = 0.01
#: Declared: the source prints no end-wall thickness.
ANCHOR_END_WALL_THICKNESS_M = 0.005
#: Declared: the source prints coil currents, not a field.
ANCHOR_EXTERNAL_FIELD_T = 1.0

#: Segment and sample counts of the reference tessellation.
REFERENCE_SEGMENTS = 64
REFERENCE_PROFILE_SAMPLES = 41


def reference_configuration() -> DeviceConfiguration:
    """Build the synthetic reference configuration.

    Returns
    -------
    DeviceConfiguration
        A validated configuration whose numbers are round.
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


def reference_geometry() -> DeviceGeometry:
    """Build the synthetic reference envelope.

    Returns
    -------
    DeviceGeometry
        A validated envelope that fits the reference configuration.
    """
    return DeviceGeometry(
        confinement_tube_inner_radius_m=0.4,
        confinement_tube_wall_thickness_m=0.02,
        coil_wall_thickness_m=0.05,
        coil_length_m=3.0,
        end_wall_thickness_m=0.03,
        separatrix_shape_index=2.0,
    )


def anchor_configuration() -> DeviceConfiguration:
    """Build the configuration anchored on the printed hardware.

    Returns
    -------
    DeviceConfiguration
        A validated configuration whose coil bore is the printed one and
        whose separatrix is declared.
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


def anchor_geometry() -> DeviceGeometry:
    """Build the envelope anchored on the printed hardware.

    Returns
    -------
    DeviceGeometry
        A validated envelope carrying the printed quartz radii and the
        printed active coil length.
    """
    return DeviceGeometry(
        confinement_tube_inner_radius_m=ANCHOR_QUARTZ_INNER_RADIUS_M,
        confinement_tube_wall_thickness_m=ANCHOR_QUARTZ_WALL_THICKNESS_M,
        coil_wall_thickness_m=ANCHOR_COIL_WALL_THICKNESS_M,
        coil_length_m=ANCHOR_ACTIVE_COIL_LENGTH_M,
        end_wall_thickness_m=ANCHOR_END_WALL_THICKNESS_M,
        separatrix_shape_index=ANCHOR_SHAPE_INDEX,
    )
