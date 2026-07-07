"""Replace CSI entitlement links with pooled product assignments on hosts."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_host_product_assignments"
down_revision: str | None = "0007_remove_host_agreement_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Recreate host_entitlements keyed by product instead of entitlement row."""
    op.drop_index("ix_host_entitlements_entitlement_id", table_name="host_entitlements")
    op.drop_index("ix_host_entitlements_host_id", table_name="host_entitlements")
    op.drop_table("host_entitlements")

    op.create_table(
        "host_entitlements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("host_id", sa.String(length=36), nullable=False),
        sa.Column("product_name", sa.String(length=256), nullable=False),
        sa.Column("option_name", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("metric", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "host_id",
            "product_name",
            "option_name",
            "metric",
            name="uq_host_entitlements",
        ),
    )
    op.create_index("ix_host_entitlements_host_id", "host_entitlements", ["host_id"], unique=False)


def downgrade() -> None:
    """Restore entitlement-id based host_entitlements table."""
    op.drop_index("ix_host_entitlements_host_id", table_name="host_entitlements")
    op.drop_table("host_entitlements")

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
    op.create_index("ix_host_entitlements_host_id", "host_entitlements", ["host_id"], unique=False)
    op.create_index(
        "ix_host_entitlements_entitlement_id",
        "host_entitlements",
        ["entitlement_id"],
        unique=False,
    )
