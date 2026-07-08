"""Tests for database row mappers."""

from __future__ import annotations

import uuid

from license_tracker.db.mappers import coerce_row, map_cpu_profile, map_product
from license_tracker.domain.enums import CpuProfileSource, LicenseMetric


def test_coerce_row_normalizes_legacy_enum_member_names() -> None:
    """Legacy uppercase enum member names map to StrEnum values."""
    row = coerce_row({"source": "MANUAL", "metric": "PROCESSOR"})
    assert row["source"] == "manual"
    assert row["metric"] == "processor"


def test_map_cpu_profile_accepts_legacy_source_value() -> None:
    """CPU profiles with legacy source values deserialize correctly."""
    profile = map_cpu_profile(
        {
            "id": str(uuid.uuid4()),
            "host_id": str(uuid.uuid4()),
            "socket_count": 2,
            "cores_per_socket": 8,
            "threads_per_core": 2,
            "logical_processor_count": 32,
            "source": "MANUAL",
        }
    )
    assert profile.source == CpuProfileSource.MANUAL


def test_map_product_accepts_legacy_metric_value() -> None:
    """Product entitlements with legacy metric values deserialize correctly."""
    product = map_product(
        {
            "id": str(uuid.uuid4()),
            "agreement_id": str(uuid.uuid4()),
            "product_id": str(uuid.uuid4()),
            "product_name": "Database Enterprise Edition",
            "metric": "PROCESSOR",
            "quantity": 10,
        }
    )
    assert product.metric == LicenseMetric.PROCESSOR
