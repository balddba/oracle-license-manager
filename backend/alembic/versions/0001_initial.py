"""Initial schema for license tracker."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create core tables."""
    op.create_table(
        "license_agreements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("csi", sa.String(length=64), nullable=False),
        sa.Column("customer_name", sa.String(length=256), nullable=False),
        sa.Column("support_level", sa.String(length=128), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_license_agreements_csi", "license_agreements", ["csi"], unique=True)
    op.create_index(
        "ix_license_agreements_renewal_date",
        "license_agreements",
        ["renewal_date"],
        unique=False,
    )

    op.create_table(
        "product_entitlements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agreement_id", sa.String(length=36), nullable=False),
        sa.Column("product_name", sa.String(length=256), nullable=False),
        sa.Column("option_name", sa.String(length=256), nullable=True),
        sa.Column("metric", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agreement_id"], ["license_agreements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_entitlements_agreement_id",
        "product_entitlements",
        ["agreement_id"],
        unique=False,
    )

    op.create_table(
        "hosts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("hostname", sa.String(length=256), nullable=False),
        sa.Column("fqdn", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("environment", sa.String(length=64), nullable=True),
        sa.Column("os_name", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("ssh_enabled", sa.Boolean(), nullable=False),
        sa.Column("ssh_port", sa.Integer(), nullable=False),
        sa.Column("ssh_user", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hosts_hostname", "hosts", ["hostname"], unique=True)

    op.create_table(
        "host_cpu_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("host_id", sa.String(length=36), nullable=False),
        sa.Column("cpu_model", sa.String(length=256), nullable=True),
        sa.Column("socket_count", sa.Integer(), nullable=False),
        sa.Column("cores_per_socket", sa.Integer(), nullable=False),
        sa.Column("threads_per_core", sa.Integer(), nullable=False),
        sa.Column("logical_processor_count", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_host_cpu_profiles_host_id",
        "host_cpu_profiles",
        ["host_id"],
        unique=False,
    )
    op.create_index(
        "ix_host_cpu_profiles_collected_at",
        "host_cpu_profiles",
        ["collected_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop core tables."""
    op.drop_index("ix_host_cpu_profiles_collected_at", table_name="host_cpu_profiles")
    op.drop_index("ix_host_cpu_profiles_host_id", table_name="host_cpu_profiles")
    op.drop_table("host_cpu_profiles")
    op.drop_index("ix_hosts_hostname", table_name="hosts")
    op.drop_table("hosts")
    op.drop_index("ix_product_entitlements_agreement_id", table_name="product_entitlements")
    op.drop_table("product_entitlements")
    op.drop_index("ix_license_agreements_renewal_date", table_name="license_agreements")
    op.drop_index("ix_license_agreements_csi", table_name="license_agreements")
    op.drop_table("license_agreements")
