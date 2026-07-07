"""Add server-level license type and unique product assignments per host."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision: str = "0009_host_license_type"
down_revision: str | None = "0008_host_product_assignments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NUP_METRICS = ("named_user_plus", "named_user", "concurrent_user", "application_user")


def upgrade() -> None:
    """Store license type on hosts and enforce one product assignment per host."""
    op.add_column(
        "hosts",
        sa.Column(
            "license_type",
            sa.String(length=32),
            nullable=False,
            server_default="cpu",
        ),
    )

    connection = op.get_bind()
    hosts = connection.execute(text("SELECT id FROM hosts")).fetchall()
    for (host_id,) in hosts:
        metrics = connection.execute(
            text("SELECT DISTINCT metric FROM host_entitlements WHERE host_id = :host_id"),
            {"host_id": host_id},
        ).fetchall()
        metric_values = {row[0] for row in metrics}
        if metric_values and metric_values.issubset(set(_NUP_METRICS)):
            connection.execute(
                text("UPDATE hosts SET license_type = 'nup' WHERE id = :host_id"),
                {"host_id": host_id},
            )
            connection.execute(
                text(
                    "UPDATE host_entitlements SET metric = 'named_user_plus' "
                    "WHERE host_id = :host_id"
                ),
                {"host_id": host_id},
            )
        else:
            connection.execute(
                text("UPDATE hosts SET license_type = 'cpu' WHERE id = :host_id"),
                {"host_id": host_id},
            )
            connection.execute(
                text(
                    "DELETE FROM host_entitlements WHERE host_id = :host_id "
                    "AND metric IN ('named_user_plus', 'named_user', "
                    "'concurrent_user', 'application_user')"
                ),
                {"host_id": host_id},
            )
            connection.execute(
                text("UPDATE host_entitlements SET metric = 'processor' WHERE host_id = :host_id"),
                {"host_id": host_id},
            )

    rows = connection.execute(
        text(
            "SELECT id, host_id, product_name, option_name, metric, notes, "
            "created_at, updated_at FROM host_entitlements"
        )
    ).fetchall()

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
            name="uq_host_entitlements",
        ),
    )
    op.create_index("ix_host_entitlements_host_id", "host_entitlements", ["host_id"], unique=False)

    for row in rows:
        connection.execute(
            text(
                "INSERT INTO host_entitlements "
                "(id, host_id, product_name, option_name, metric, notes, created_at, updated_at) "
                "VALUES (:id, :host_id, :product_name, :option_name, :metric, :notes, "
                ":created_at, :updated_at)"
            ),
            {
                "id": row[0],
                "host_id": row[1],
                "product_name": row[2],
                "option_name": row[3],
                "metric": row[4],
                "notes": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            },
        )


def downgrade() -> None:
    """Remove host license type and restore metric in the unique constraint."""
    connection = op.get_bind()
    rows = connection.execute(
        text(
            "SELECT id, host_id, product_name, option_name, metric, notes, "
            "created_at, updated_at FROM host_entitlements"
        )
    ).fetchall()

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

    for row in rows:
        connection.execute(
            text(
                "INSERT INTO host_entitlements "
                "(id, host_id, product_name, option_name, metric, notes, created_at, updated_at) "
                "VALUES (:id, :host_id, :product_name, :option_name, :metric, :notes, "
                ":created_at, :updated_at)"
            ),
            {
                "id": row[0],
                "host_id": row[1],
                "product_name": row[2],
                "option_name": row[3],
                "metric": row[4],
                "notes": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            },
        )

    op.drop_column("hosts", "license_type")
