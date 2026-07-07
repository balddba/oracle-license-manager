"""Normalize legacy uppercase enum member names to StrEnum values."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from license_tracker.domain.enums import (
    CpuProfileSource,
    HostEnvironment,
    HostLicenseType,
    LicenseMetric,
    LicenseStatus,
)

revision: str = "0012_normalize_enum_values"
down_revision: str | None = "0011_oracle_processor_core_factors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ENUM_COLUMNS: tuple[tuple[str, str, type], ...] = (
    ("license_agreements", "status", LicenseStatus),
    ("product_entitlements", "metric", LicenseMetric),
    ("host_cpu_profiles", "source", CpuProfileSource),
    ("hosts", "environment", HostEnvironment),
    ("hosts", "license_type", HostLicenseType),
    ("host_entitlements", "metric", LicenseMetric),
)


def _normalize_enum_column(table: str, column: str, enum_cls: type) -> None:
    """Rewrite legacy enum member names to StrEnum values for one column.

    Args:
        table (str): Table name.
        column (str): Column name.
        enum_cls (type): StrEnum class for the column.
    """
    bind = op.get_bind()
    for member in enum_cls:
        if member.name == member.value:
            continue
        bind.execute(
            sa.text(
                f"""
                UPDATE {table}
                SET {column} = :value
                WHERE {column} = :legacy_name
                """
            ),
            {"value": member.value, "legacy_name": member.name},
        )


def upgrade() -> None:
    """Rewrite legacy enum member names to StrEnum values."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table, column, enum_cls in _ENUM_COLUMNS:
        if table not in inspector.get_table_names():
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        if column not in columns:
            continue
        _normalize_enum_column(table, column, enum_cls)


def downgrade() -> None:
    """Enum normalization is not reversed on downgrade."""
