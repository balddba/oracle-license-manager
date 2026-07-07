"""Add processor core factors and host CPU licensing fields."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision: str = "0002_processor_core_factors"
down_revision: str | None = "0001_initial"
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
    """Create processor core factor table and extend host CPU profiles."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "processor_core_factors" not in inspector.get_table_names():
        op.create_table(
            "processor_core_factors",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=256), nullable=False),
            sa.Column("match_pattern", sa.String(length=256), nullable=False),
            sa.Column("core_factor", sa.Float(), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False),
            sa.Column("is_default", sa.Boolean(), nullable=False),
            sa.Column("notes", sa.String(length=4000), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    core_factor_count = bind.execute(
        sa.text("SELECT COUNT(*) FROM processor_core_factors")
    ).scalar_one()
    if core_factor_count == 0:
        from license_tracker.db.seed import processor_core_factor_insert_rows

        core_factor_table = sa.table(
            "processor_core_factors",
            sa.column("id", sa.String(length=36)),
            sa.column("name", sa.String(length=256)),
            sa.column("match_pattern", sa.String(length=256)),
            sa.column("core_factor", sa.Float()),
            sa.column("priority", sa.Integer()),
            sa.column("is_default", sa.Boolean()),
            sa.column("notes", sa.String(length=4000)),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(core_factor_table, processor_core_factor_insert_rows())

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
    """Drop processor core factor table and host CPU licensing fields."""
    with op.batch_alter_table("host_cpu_profiles") as batch_op:
        batch_op.drop_constraint(
            "fk_host_cpu_profiles_core_factor_id",
            type_="foreignkey",
        )
        batch_op.drop_column("core_factor_id")
        batch_op.drop_column("core_factor")

    with op.batch_alter_table("hosts") as batch_op:
        batch_op.drop_constraint("fk_hosts_agreement_id", type_="foreignkey")
        batch_op.drop_index("ix_hosts_agreement_id")
        batch_op.drop_column("agreement_id")

    op.drop_table("processor_core_factors")
