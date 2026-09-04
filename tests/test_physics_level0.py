# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN FRC Core — level-0 record tests

"""Tests of the composed level-0 physics record."""

from __future__ import annotations

import hashlib
import json
import math

import pytest
from geometry_fixtures import ANCHOR_FILL_DENSITY_PER_M3
from physics_fixtures import (
    anchor_configuration,
    anchor_inputs,
    reference_configuration,
    reference_inputs,
)

from scpn_frc_core.errors import DeviceConfigurationError
from scpn_frc_core.physics.equilibrium import DEUTERON_MASS_KG, alfven_speed_m_s
from scpn_frc_core.physics.level0 import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    ModelInputs,
    level0_physics,
)


def test_inputs_record_carries_both_declared_values() -> None:
    """The declared inputs project to their own record."""
    assert reference_inputs().to_record() == {
        "particle_density_per_m3": 1.0e20,
        "ion_mass_kg": DEUTERON_MASS_KG,
    }


@pytest.mark.parametrize(
    ("density", "mass", "field_name"),
    [
        (0.0, DEUTERON_MASS_KG, "particle_density_per_m3"),
        (math.nan, DEUTERON_MASS_KG, "particle_density_per_m3"),
        (1.0e20, -1.0, "ion_mass_kg"),
        (1.0e20, math.inf, "ion_mass_kg"),
    ],
)
def test_inputs_refuse_each_field_by_name(
    density: float, mass: float, field_name: str
) -> None:
    """A declared input outside its domain is refused, naming the field."""
    with pytest.raises(DeviceConfigurationError, match=field_name):
        ModelInputs(particle_density_per_m3=density, ion_mass_kg=mass)


def test_record_is_schema_tagged_and_states_its_non_claims() -> None:
    """The record names its schema and carries the non-claims verbatim."""
    record = level0_physics(reference_configuration(), reference_inputs()).to_record()
    assert record["schema"] == LEVEL0_SCHEMA
    assert record["schema_version"] == LEVEL0_SCHEMA_VERSION
    assert record["non_claims"] == list(LEVEL0_NON_CLAIMS)
    assert list(record) == [
        "schema",
        "schema_version",
        "configuration_digest_sha256",
        "inputs",
        "radial_pressure_balance",
        "kinetic_scale_bound",
        "alfven_speed_m_s",
        "non_claims",
    ]


def test_record_binds_the_configuration_it_was_built_from() -> None:
    """The record carries the digest of its own configuration."""
    configuration = reference_configuration()
    physics = level0_physics(configuration, reference_inputs())
    assert physics.configuration_digest_sha256 == configuration.digest_sha256()


def test_record_composes_the_alfven_speed_of_the_same_operating_point() -> None:
    """The speed is the one the balance's field and the inputs give."""
    configuration = reference_configuration()
    inputs = reference_inputs()
    physics = level0_physics(configuration, inputs)
    assert physics.alfven_speed_m_s == alfven_speed_m_s(
        configuration.limits.external_field_t,
        inputs.particle_density_per_m3,
        inputs.ion_mass_kg,
    )


def test_canonical_bytes_are_already_in_canonical_form() -> None:
    """Re-canonicalising the bytes is a no-op, and they round-trip.

    Testing for the absence of a comma-space would be wrong: the
    non-claims are English prose and contain several. The property that
    matters is idempotence — serialising what these bytes decode to,
    canonically, reproduces the bytes exactly.
    """
    physics = level0_physics(reference_configuration(), reference_inputs())
    data = physics.canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data)
    assert decoded == physics.to_record()
    assert list(decoded) == sorted(decoded)
    again = json.dumps(decoded, sort_keys=True, separators=(",", ":"))
    assert data == (again + "\n").encode("utf-8")


def test_digest_identifies_the_exact_bytes() -> None:
    """The digest is the SHA-256 of the canonical bytes and nothing else."""
    physics = level0_physics(reference_configuration(), reference_inputs())
    assert (
        physics.digest_sha256() == hashlib.sha256(physics.canonical_bytes()).hexdigest()
    )


def test_digest_is_stable_across_two_compositions() -> None:
    """The same configuration and inputs give the same bytes."""
    first = level0_physics(reference_configuration(), reference_inputs())
    second = level0_physics(reference_configuration(), reference_inputs())
    assert first.digest_sha256() == second.digest_sha256()


def test_digest_moves_when_a_declared_input_moves() -> None:
    """A different density is a different record."""
    base = level0_physics(reference_configuration(), reference_inputs())
    other = level0_physics(
        reference_configuration(),
        ModelInputs(particle_density_per_m3=2.0e20, ion_mass_kg=DEUTERON_MASS_KG),
    )
    assert base.digest_sha256() != other.digest_sha256()


def test_anchor_printed_density_is_recoverable_from_the_built_record() -> None:
    """The printed fill density survives into the composed record.

    The value is proved recoverable from the record the model builds, not
    merely present in the fixture that fed it.
    """
    record = level0_physics(anchor_configuration(), anchor_inputs()).to_record()
    assert record["inputs"]["particle_density_per_m3"] == ANCHOR_FILL_DENSITY_PER_M3
    assert (
        record["radial_pressure_balance"]["particle_density_per_m3"]
        == ANCHOR_FILL_DENSITY_PER_M3
    )
    assert record["kinetic_scale_bound"]["bound"] == 3.5
    assert record["kinetic_scale_bound"]["elongation"] == 7.5
