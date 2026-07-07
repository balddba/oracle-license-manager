"""Add host-to-entitlement association table."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_host_entitlements"
down_revision: str | None = "0005_repair_processor_host_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create host_entitlements join table."""
    op.create_table(
        "host_entitlements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("host_id", sa.String(length=36), nullable=False),
        sa.Column("entitlement_id", sa.String(length=36), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["entitlement_id"], ["product_entitlements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("host_id", "entitlement_id", name="uq_host_entitlements"),
    )
    op.create_index(
        "ix_host_entitlements_host_id",
        "host_entitlements",
        ["host_id"],
        unique=False,
    )
    op.create_index(
        "ix_host_entitlements_entitlement_id",
        "host_entitlements",
        ["entitlement_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop host_entitlements join table."""
    op.drop_index("ix_host_entitlements_entitlement_id", table_name="host_entitlements")
    op.drop_index("ix_host_entitlements_host_id", table_name="host_entitlements")
    op.drop_table("host_entitlements")
