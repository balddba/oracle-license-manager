"""Tests for processor license calculations."""

from __future__ import annotations

from license_tracker.db.models.processor_core_factor import ProcessorCoreFactor
from license_tracker.db.seed import load_core_factor_seed_rows
from license_tracker.domain.license_calc import (
    calculate_named_users_required,
    calculate_processor_licenses,
    match_core_factor,
)


def _factor(
    name: str,
    pattern: str,
    value: float,
    *,
    priority: int = 0,
    is_default: bool = False,
) -> ProcessorCoreFactor:
    return ProcessorCoreFactor(
        name=name,
        match_pattern=pattern,
        core_factor=value,
        priority=priority,
        is_default=is_default,
    )


def _seed_factors() -> list[ProcessorCoreFactor]:
    return [
        ProcessorCoreFactor(
            name=row["name"],
            match_pattern=row["match_pattern"],
            core_factor=row["core_factor"],
            priority=row["priority"],
            is_default=row["is_default"],
            notes=row["notes"],
        )
        for row in load_core_factor_seed_rows()
    ]


def test_calculate_processor_licenses_rounds_up() -> None:
    """Processor licenses round up fractional requirements."""
    assert calculate_processor_licenses(16, 0.5) == 8
    assert calculate_processor_licenses(17, 0.5) == 9
    assert calculate_processor_licenses(32, 0.25) == 8


def test_calculate_named_users_required_from_licensable_cores() -> None:
    """NUP minimum is 25 named users per licensable core."""
    assert calculate_named_users_required(8) == 200
    assert calculate_named_users_required(None) is None
    assert calculate_named_users_required(0) is None


def test_match_core_factor_prefers_highest_priority() -> None:
    """More specific patterns with higher priority win."""
    factors = [
        _factor("Generic Xeon", "xeon", 1.0, priority=5),
        _factor("Intel Xeon", "xeon", 0.5, priority=20),
        _factor("Default", "*", 1.0, is_default=True),
    ]
    matched = match_core_factor("Intel(R) Xeon(R) Gold 6248", factors)
    assert matched is not None
    assert matched.core_factor == 0.5


def test_match_core_factor_uses_default_when_unknown() -> None:
    """Unknown CPU models fall back to the default factor."""
    factors = [
        _factor("Intel Xeon", "xeon", 0.5, priority=10),
        _factor("Default", "*", 1.0, is_default=True),
    ]
    matched = match_core_factor("Some Future CPU", factors)
    assert matched is not None
    assert matched.is_default is True
    assert matched.core_factor == 1.0


def test_oracle_core_factor_seed_loads_full_table() -> None:
    """Oracle 070634 seed includes the default and common families."""
    rows = load_core_factor_seed_rows()
    assert len(rows) >= 50
    defaults = [row for row in rows if row["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["core_factor"] == 1.0
    assert defaults[0]["name"] == "All Other Multicore chips"


def test_oracle_core_factor_table_matches_common_cpus() -> None:
    """Common CPU model strings resolve to Oracle table factors."""
    factors = _seed_factors()
    cases = [
        ("Intel(R) Xeon(R) Gold 6248 CPU @ 2.50GHz", 0.5, "Gold 62"),
        ("Intel(R) Xeon(R) CPU E5-2690 v4 @ 2.60GHz", 0.5, "E5-26"),
        ("AMD EPYC 7742 64-Core Processor", 0.5, "EPYC 700"),
        ("AMD EPYC 9654 96-Core Processor", 0.5, "EPYC 900"),
        ("Ampere Altra", 0.25, "Ampere"),
        ("SPARC T5", 0.5, "SPARC T5"),
        ("SPARC T3", 0.25, "SPARC T3"),
        ("IBM POWER10", 1.0, "POWER10"),
        ("Some Future CPU", 1.0, "All Other"),
    ]
    for cpu_model, expected_factor, name_fragment in cases:
        matched = match_core_factor(cpu_model, factors)
        assert matched is not None, cpu_model
        assert matched.core_factor == expected_factor, cpu_model
        assert name_fragment.lower() in matched.name.lower(), cpu_model
