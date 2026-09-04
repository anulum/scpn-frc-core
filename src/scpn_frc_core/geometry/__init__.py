# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — device geometry package

"""Device 3D and CAD models of the field-reversed-configuration family.

The mechanical envelope, the tier-G1 tessellated model and the tier-G2
B-rep model of the same five bodies, all built on the shared kernel
library. The separatrix is a closed surface of revolution through the
published shape function, not a column. Design record: ADR 0006.
"""

from __future__ import annotations

from scpn_frc_core.geometry.cad import (
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    CAD_MODEL_UNITS,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    DEFAULT_REFERENCE_PROFILE_SAMPLES,
    DeviceModelCAD,
    build_device_cad,
    smallest_tessellated_radius_m,
)
from scpn_frc_core.geometry.device import (
    GEOMETRY_FIELDS,
    MIN_SHAPE_INDEX,
    DeviceGeometry,
    geometry_from_record,
)
from scpn_frc_core.geometry.model import (
    BODY_NAMES,
    MIN_PROFILE_SAMPLES,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceModel3D,
    build_device_model,
    require_profile_samples,
    separatrix_profile,
)

__all__ = [
    "BODY_NAMES",
    "CAD_MODEL_NON_CLAIMS",
    "CAD_MODEL_SCHEMA",
    "CAD_MODEL_SCHEMA_VERSION",
    "CAD_MODEL_UNITS",
    "DEFAULT_ANGULAR_DEFLECTION_RAD",
    "DEFAULT_LINEAR_DEFLECTION_M",
    "DEFAULT_REFERENCE_MESH_SEGMENTS",
    "DEFAULT_REFERENCE_PROFILE_SAMPLES",
    "GEOMETRY_FIELDS",
    "MIN_PROFILE_SAMPLES",
    "MIN_SHAPE_INDEX",
    "MODEL_NON_CLAIMS",
    "MODEL_SCHEMA",
    "MODEL_SCHEMA_VERSION",
    "MODEL_UNITS",
    "DeviceGeometry",
    "DeviceModel3D",
    "DeviceModelCAD",
    "build_device_cad",
    "build_device_model",
    "geometry_from_record",
    "require_profile_samples",
    "separatrix_profile",
    "smallest_tessellated_radius_m",
]
