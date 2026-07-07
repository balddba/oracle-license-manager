"""Repair host and CPU profile columns skipped by legacy schema stamps."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision: str = "0005_repair_processor_host_columns"
down_revision: str | None = "0004_backfill_reference_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names(table_name: str) -> set[str]:
    """Return column names for a table.

    Args:
        table_name (str): Table to inspect.

    Returns:
        set[str]: Column names present on the table.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    """Add 0002 host licensing columns when a legacy stamp skipped that migration."""
    host_columns = _column_names("hosts")
    if "agreement_id" not in host_columns:
        with op.batch_alter_table("hosts") as batch_op:
            batch_op.add_column(sa.Column("agreement_id", sa.String(length=36), nullable=True))
            batch_op.create_index("ix_hosts_agreement_id", ["agreement_id"], unique=False)
            batch_op.create_foreign_key(
                "fk_hosts_agreement_id",
                "license_agreements",
                ["agreement_id"],
                ["id"],
                ondelete="SET NULL",
            )

    cpu_columns = _column_names("host_cpu_profiles")
    if "core_factor" not in cpu_columns or "core_factor_id" not in cpu_columns:
        with op.batch_alter_table("host_cpu_profiles") as batch_op:
            if "core_factor" not in cpu_columns:
                batch_op.add_column(sa.Column("core_factor", sa.Float(), nullable=True))
            if "core_factor_id" not in cpu_columns:
                batch_op.add_column(
                    sa.Column("core_factor_id", sa.String(length=36), nullable=True)
                )
            batch_op.create_foreign_key(
                "fk_host_cpu_profiles_core_factor_id",
                "processor_core_factors",
                ["core_factor_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    """Schema repair is not reversed on downgrade."""
