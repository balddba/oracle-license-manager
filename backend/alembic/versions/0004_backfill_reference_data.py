"""Backfill reference data when tables exist but are empty."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_backfill_reference_data"
down_revision: str | None = "0003_catalog_products"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Insert catalog and core factor rows when prior migrations created empty tables."""
    bind = op.get_bind()

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
    """Reference data backfill is not reversed on downgrade."""
