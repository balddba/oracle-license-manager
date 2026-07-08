"""Link product_entitlements and host_entitlements to catalog_products via product_id.

Revision ID: 0013_link_to_catalog_product_id
Revises: 0012_normalize_enum_values
Create Date: 2026-07-07 20:00:00.000000
"""

from collections.abc import Sequence
import uuid
import sqlalchemy as sa
from sqlalchemy import text
from alembic import op

revision: str = "0013_link_to_catalog_product_id"
down_revision: str | None = "0012_normalize_enum_values"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Refactor tables to link to catalog_products.id."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())

    # Build catalog map: (product_name, option_name) -> id
    catalog_map = {}
    if "catalog_products" in tables:
        catalog_rows = connection.execute(
            text("SELECT id, product_name, option_name FROM catalog_products")
        ).fetchall()
        for c_id, name, option in catalog_rows:
            norm_option = option or ""
            catalog_map[(name.strip().lower(), norm_option.strip().lower())] = c_id

    def get_or_create_product_id(name: str, option: str | None, now_ts) -> str:
        """Find catalog product ID or create a new catalog entry if missing."""
        name_clean = name.strip()
        option_clean = (option or "").strip()
        key = (name_clean.lower(), option_clean.lower())

        if key in catalog_map:
            return catalog_map[key]

        # Product is not in the catalog; create a custom entry to satisfy foreign key integrity
        new_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
                INSERT INTO catalog_products (
                    id, price_list_id, category, product_name, option_name,
                    supports_nup, supports_processor, created_at, updated_at
                ) VALUES (
                    :id, :price_list_id, :category, :product_name, :option_name,
                    :supports_nup, :supports_processor, :created_at, :updated_at
                )
                """
            ),
            {
                "id": new_id,
                "price_list_id": "technology-price-list-070617",
                "category": "Custom",
                "product_name": name_clean,
                "option_name": option_clean or None,
                "supports_nup": 1,
                "supports_processor": 1,
                "created_at": now_ts,
                "updated_at": now_ts,
            },
        )
        catalog_map[key] = new_id
        return new_id

    # 1. Migrate product_entitlements
    migrated_entitlements = []
    if "product_entitlements" in tables:
        ent_rows = connection.execute(
            text(
                "SELECT id, agreement_id, product_name, option_name, metric, quantity, notes, created_at, updated_at FROM product_entitlements"
            )
        ).fetchall()
        for row in ent_rows:
            p_id = get_or_create_product_id(row[2], row[3], row[7])
            migrated_entitlements.append(
                {
                    "id": row[0],
                    "agreement_id": row[1],
                    "product_id": p_id,
                    "metric": row[4],
                    "quantity": row[5],
                    "notes": row[6],
                    "created_at": row[7],
                    "updated_at": row[8],
                }
            )

    # 2. Migrate host_entitlements
    migrated_host_entitlements = []
    if "host_entitlements" in tables:
        host_ent_rows = connection.execute(
            text(
                "SELECT id, host_id, product_name, option_name, metric, notes, created_at, updated_at FROM host_entitlements"
            )
        ).fetchall()
        for row in host_ent_rows:
            p_id = get_or_create_product_id(row[2], row[3], row[6])
            migrated_host_entitlements.append(
                {
                    "id": row[0],
                    "host_id": row[1],
                    "product_id": p_id,
                    "metric": row[4],
                    "notes": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                }
            )

    # 3. Recreate product_entitlements table
    if "product_entitlements" in tables:
        op.drop_index("ix_product_entitlements_agreement_id", table_name="product_entitlements")
        op.drop_table("product_entitlements")

    op.create_table(
        "product_entitlements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agreement_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("metric", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agreement_id"], ["license_agreements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_entitlements_agreement_id",
        "product_entitlements",
        ["agreement_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_entitlements_product_id", "product_entitlements", ["product_id"], unique=False
    )

    for ent in migrated_entitlements:
        connection.execute(
            text(
                """
                INSERT INTO product_entitlements (id, agreement_id, product_id, metric, quantity, notes, created_at, updated_at)
                VALUES (:id, :agreement_id, :product_id, :metric, :quantity, :notes, :created_at, :updated_at)
                """
            ),
            ent,
        )

    # 4. Recreate host_entitlements table
    if "host_entitlements" in tables:
        op.drop_index("ix_host_entitlements_host_id", table_name="host_entitlements")
        op.drop_table("host_entitlements")

    op.create_table(
        "host_entitlements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("host_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("metric", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("host_id", "product_id", name="uq_host_entitlements"),
    )
    op.create_index("ix_host_entitlements_host_id", "host_entitlements", ["host_id"], unique=False)
    op.create_index(
        "ix_host_entitlements_product_id", "host_entitlements", ["product_id"], unique=False
    )

    seen_host_products = set()
    for hent in migrated_host_entitlements:
        # Enforce unique host_id + product_id in case legacy data has duplicate option names mapped to same product
        uq_key = (hent["host_id"], hent["product_id"])
        if uq_key in seen_host_products:
            continue
        seen_host_products.add(uq_key)

        connection.execute(
            text(
                """
                INSERT INTO host_entitlements (id, host_id, product_id, metric, notes, created_at, updated_at)
                VALUES (:id, :host_id, :product_id, :metric, :notes, :created_at, :updated_at)
                """
            ),
            hent,
        )


def downgrade() -> None:
    """Restore string-based product name and option columns."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())

    # Get product entitlements and host entitlements with joined name/option from catalog
    product_rows = []
    if "product_entitlements" in tables and "catalog_products" in tables:
        product_rows = connection.execute(
            text(
                """
                SELECT pe.id, pe.agreement_id, cp.product_name, cp.option_name, pe.metric, pe.quantity, pe.notes, pe.created_at, pe.updated_at
                FROM product_entitlements pe
                JOIN catalog_products cp ON pe.product_id = cp.id
                """
            )
        ).fetchall()

    host_rows = []
    if "host_entitlements" in tables and "catalog_products" in tables:
        host_rows = connection.execute(
            text(
                """
                SELECT he.id, he.host_id, cp.product_name, cp.option_name, he.metric, he.notes, he.created_at, he.updated_at
                FROM host_entitlements he
                JOIN catalog_products cp ON he.product_id = cp.id
                """
            )
        ).fetchall()

    # Recreate tables with legacy schema
    if "product_entitlements" in tables:
        op.drop_index("ix_product_entitlements_agreement_id", table_name="product_entitlements")
        op.drop_table("product_entitlements")

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

    for row in product_rows:
        connection.execute(
            text(
                """
                INSERT INTO product_entitlements (id, agreement_id, product_name, option_name, metric, quantity, notes, created_at, updated_at)
                VALUES (:id, :agreement_id, :product_name, :option_name, :metric, :quantity, :notes, :created_at, :updated_at)
                """
            ),
            {
                "id": row[0],
                "agreement_id": row[1],
                "product_name": row[2],
                "option_name": row[3],
                "metric": row[4],
                "quantity": row[5],
                "notes": row[6],
                "created_at": row[7],
                "updated_at": row[8],
            },
        )

    if "host_entitlements" in tables:
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

    for row in host_rows:
        connection.execute(
            text(
                """
                INSERT INTO host_entitlements (id, host_id, product_name, option_name, metric, notes, created_at, updated_at)
                VALUES (:id, :host_id, :product_name, :option_name, :metric, :notes, :created_at, :updated_at)
                """
            ),
            {
                "id": row[0],
                "host_id": row[1],
                "product_name": row[2],
                "option_name": row[3] or "",
                "metric": row[4],
                "notes": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            },
        )
