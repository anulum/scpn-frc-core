# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — level-0 device physics package

"""Level-0 device physics of the field-reversed-configuration family.

Two closed forms evaluated on the validated device configuration: the
radial pressure balance across the separatrix, which fixes the peak and
average plasma pressure from the external field and the average-beta
relation, and the empirical ``S* / E`` kinetic-scale bound that orders how
far an operating point sits from the fluid limit its tilt instability is
derived in. Every function is a closed-form evaluation; no equation is
solved and no value describes a real machine. Design record: ADR 0005.
"""

from __future__ import annotations

from scpn_frc_core.physics.equilibrium import (
    DEUTERON_MASS_KG,
    ELEMENTARY_CHARGE_C,
    MU0,
    PROTON_MASS_KG,
    RadialPressureBalance,
    alfven_speed_m_s,
    magnetic_pressure_pa,
    radial_pressure_balance,
    require_average_beta,
)
from scpn_frc_core.physics.level0 import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0Physics,
    ModelInputs,
    level0_physics,
)
from scpn_frc_core.physics.stability import (
    EMPIRICAL_SE_BOUND,
    SPEED_OF_LIGHT_M_PER_S,
    VACUUM_PERMITTIVITY_F_PER_M,
    KineticScaleBound,
    ion_plasma_frequency_rad_s,
    ion_skin_depth_m,
    kinetic_scale_bound,
)

__all__ = [
    "DEUTERON_MASS_KG",
    "ELEMENTARY_CHARGE_C",
    "EMPIRICAL_SE_BOUND",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "MU0",
    "PROTON_MASS_KG",
    "SPEED_OF_LIGHT_M_PER_S",
    "VACUUM_PERMITTIVITY_F_PER_M",
    "KineticScaleBound",
    "Level0Physics",
    "ModelInputs",
    "RadialPressureBalance",
    "alfven_speed_m_s",
    "ion_plasma_frequency_rad_s",
    "ion_skin_depth_m",
    "kinetic_scale_bound",
    "level0_physics",
    "magnetic_pressure_pa",
    "radial_pressure_balance",
    "require_average_beta",
]
