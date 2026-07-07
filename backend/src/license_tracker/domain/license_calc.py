"""Oracle processor and named-user license calculations."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from license_tracker.db.models.processor_core_factor import ProcessorCoreFactor

NUP_USERS_PER_LICENSE = 25


def calculate_processor_licenses(physical_cores: int, core_factor: float) -> int:
    """Calculate required processor licenses from physical cores and core factor.

    Oracle rounds up fractional processor license requirements.

    Args:
        physical_cores (int): Total physical CPU cores.
        core_factor (float): Processor core factor multiplier.

    Returns:
        int: Required processor license count.
    """
    # Guard against invalid configuration or physical layouts with zero/negative counts
    if physical_cores < 1 or core_factor <= 0:
        return 0
    # Oracle licensing terms require rounding any fractional processor license requirement
    # UP to the nearest whole integer (e.g. 1.5 rounded to 2).
    return math.ceil(physical_cores * core_factor)


def calculate_named_users_required(licensable_cores: int | None) -> int | None:
    """Calculate required Named User Plus licenses from licensable cores.

    Oracle requires a minimum of 25 NUPs per processor license.

    Args:
        licensable_cores (int | None): Processor licenses required (licensable cores).

    Returns:
        int | None: Required NUP count, or None when licensable cores are unknown.
    """
    # If the host processor core profile is not yet available, we cannot compute NUP requirements
    if licensable_cores is None or licensable_cores < 1:
        return None
    # Named User Plus (NUP) minimum standard metric rule: 25 users per processor license
    return licensable_cores * NUP_USERS_PER_LICENSE


def match_core_factor(
    cpu_model: str | None,
    factors: list[ProcessorCoreFactor],
) -> ProcessorCoreFactor | None:
    """Select the best matching processor core factor for a CPU model string.

    Args:
        cpu_model (str | None): Reported CPU model name.
        factors (list[ProcessorCoreFactor]): Available core factor rows.

    Returns:
        ProcessorCoreFactor | None: Best match, or the default row if configured.
    """
    # If core factor reference tables are completely empty, no match can be established
    if not factors:
        return None

    # Normalize CPU model descriptor to simplify case-insensitive matching
    normalized = (cpu_model or "").strip().lower()

    # Locate the fallback row marked as default to use when no patterns match
    default_factor = next((factor for factor in factors if factor.is_default), None)

    # If the input model string is empty, immediately return the default fallback core factor
    if not normalized:
        return default_factor

    # Sort matching factors by priority (descending) so more specific rules match first
    ranked = sorted(factors, key=lambda factor: factor.priority, reverse=True)
    for factor in ranked:
        # Ignore the default factor entry in pattern-matching scan
        if factor.is_default:
            continue

        # Perform substring matching against the normalized CPU model string
        pattern = factor.match_pattern.strip().lower()
        if pattern and pattern in normalized:
            return factor

    # Fallback if no matching pattern was found in the CPU model string
    return default_factor
