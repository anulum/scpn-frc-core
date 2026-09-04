# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — device capability package

"""Device capability models of the SCPN field-reversed-configuration family.

Public surface of the ``device_configuration_model``,
``diagnostic_clock_semantics`` and ``level0_device_physics`` capabilities
at ``computational_prototype`` maturity: validated parameter objects,
the radial pressure balance and the empirical kinetic-scale bound,
synthetic diagnostic and clock declarations aligned with the pinned SPO
observability catalogue, documented consistency estimates, canonical
serialisation with SHA-256 digests, and data-only pins to the SPO
registries. No claim about any real machine or diagnostic is made
anywhere in this package.
"""

from __future__ import annotations

from typing import Final

from scpn_frc_core.configuration import (
    OWNED_CONFIGURATIONS,
    PROLATE_MIN_ELONGATION,
    WALL_PROXIMITY_MAX_XS,
    ConsistencyFinding,
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_frc_core.errors import DeviceConfigurationError, DiagnosticPlanError
from scpn_frc_core.observability import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
    CandidateProfile,
    ClockKind,
    ClockModel,
    ClockRelation,
    DeferredCandidate,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    FrameKind,
    ObservabilityBinding,
    ObservabilityClass,
    ReferenceFrame,
    SemanticCarrier,
    plan_from_bytes,
    plan_from_record,
)
from scpn_frc_core.parameters import (
    OperationalLimits,
    SeparatrixGeometry,
)
from scpn_frc_core.physics import (
    EMPIRICAL_SE_BOUND,
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    KineticScaleBound,
    Level0Physics,
    ModelInputs,
    RadialPressureBalance,
    kinetic_scale_bound,
    level0_physics,
    radial_pressure_balance,
)
from scpn_frc_core.plan_envelope import (
    PlanEnvelope,
    envelope_for_plan,
    envelope_from_bytes,
    envelope_from_record,
    verify_envelope,
)

__version__: Final = "0.1.0.dev0"

__all__ = [
    "APPLICABLE_CANDIDATES",
    "CATALOGUE_BINDING",
    "EMPIRICAL_SE_BOUND",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "OWNED_CONFIGURATIONS",
    "PROLATE_MIN_ELONGATION",
    "WALL_PROXIMITY_MAX_XS",
    "CandidateProfile",
    "ClockKind",
    "ClockModel",
    "ClockRelation",
    "ConsistencyFinding",
    "DeferredCandidate",
    "DeviceConfiguration",
    "DeviceConfigurationError",
    "DiagnosticChannelPlan",
    "DiagnosticPlan",
    "DiagnosticPlanError",
    "FrameKind",
    "KineticScaleBound",
    "Level0Physics",
    "ModelInputs",
    "ObservabilityBinding",
    "ObservabilityClass",
    "OperationalLimits",
    "PlanEnvelope",
    "RadialPressureBalance",
    "ReferenceFrame",
    "RegistryBinding",
    "SemanticCarrier",
    "SeparatrixGeometry",
    "__version__",
    "configuration_from_bytes",
    "configuration_from_record",
    "envelope_for_plan",
    "envelope_from_bytes",
    "envelope_from_record",
    "kinetic_scale_bound",
    "level0_physics",
    "plan_from_bytes",
    "plan_from_record",
    "radial_pressure_balance",
    "verify_envelope",
]
