"""Add Oracle catalog products table."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision: str = "0003_catalog_products"
down_revision: str | None = "0002_processor_core_factors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create catalog products table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "catalog_products" not in inspector.get_table_names():
        op.create_table(
            "catalog_products",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("price_list_id", sa.String(length=64), nullable=False),
            sa.Column("category", sa.String(length=128), nullable=False),
            sa.Column("product_name", sa.String(length=256), nullable=False),
            sa.Column("option_name", sa.String(length=256), nullable=True),
            sa.Column("list_price_nup_usd", sa.Float(), nullable=True),
            sa.Column("list_price_nup_support_usd", sa.Float(), nullable=True),
            sa.Column("list_price_processor_usd", sa.Float(), nullable=True),
            sa.Column("list_price_processor_support_usd", sa.Float(), nullable=True),
            sa.Column("supports_nup", sa.Boolean(), nullable=False),
            sa.Column("supports_processor", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_catalog_products_price_list_id", "catalog_products", ["price_list_id"])
        op.create_index("ix_catalog_products_category", "catalog_products", ["category"])
        op.create_index("ix_catalog_products_product_name", "catalog_products", ["product_name"])

    catalog_count = bind.execute(sa.text("SELECT COUNT(*) FROM catalog_products")).scalar_one()
    if catalog_count == 0:
        from license_tracker.db.seed import catalog_product_insert_rows

        catalog_table = sa.table(
            "catalog_products",
            sa.column("id", sa.String(length=36)),
            sa.column("price_list_id", sa.String(length=64)),
            sa.column("category", sa.String(length=128)),
            sa.column("product_name", sa.String(length=256)),
            sa.column("option_name", sa.String(length=256)),
            sa.column("list_price_nup_usd", sa.Float()),
            sa.column("list_price_nup_support_usd", sa.Float()),
            sa.column("list_price_processor_usd", sa.Float()),
            sa.column("list_price_processor_support_usd", sa.Float()),
            sa.column("supports_nup", sa.Boolean()),
            sa.column("supports_processor", sa.Boolean()),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(catalog_table, catalog_product_insert_rows())


def downgrade() -> None:
    """Drop catalog products table."""
    op.drop_index("ix_catalog_products_product_name", table_name="catalog_products")
    op.drop_index("ix_catalog_products_category", table_name="catalog_products")
    op.drop_index("ix_catalog_products_price_list_id", table_name="catalog_products")
    op.drop_table("catalog_products")
