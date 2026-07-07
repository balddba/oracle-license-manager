"""Ensure reference catalog and core factor rows exist after migrations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from loguru import logger

from license_tracker.config import Settings
from license_tracker.db.queries.factory import create_database
from license_tracker.db.seed import (
    catalog_yaml_path,
    core_factor_yaml_path,
    load_catalog_seed_rows,
    processor_core_factor_insert_rows,
)


async def ensure_reference_data(settings: Settings) -> None:
    """Insert catalog and core factor rows when tables are empty.

    Args:
        settings (Settings): Application settings.
    """
    database = create_database(settings)
    async with database:
        catalog_count = await database.count_catalog_products()
        if catalog_count == 0:
            rows = load_catalog_seed_rows()
            if not rows:
                logger.warning(
                    "Catalog seed file not found at {}; catalog products were not loaded",
                    catalog_yaml_path(),
                )
            else:
                now = datetime.now(UTC)
                await database.insert_catalog_products(
                    [
                        {
                            "id": str(uuid.uuid4()),
                            "created_at": now,
                            "updated_at": now,
                            **row,
                        }
                        for row in rows
                    ]
                )
                logger.info("Loaded {} catalog products from {}", len(rows), catalog_yaml_path())

        core_factor_count = await database.count_core_factors()
        if core_factor_count == 0:
            rows = processor_core_factor_insert_rows()
            if not rows:
                logger.warning(
                    "Core factor seed file not found at {}; processor core factors were not loaded",
                    core_factor_yaml_path(),
                )
            else:
                await database.insert_core_factors(rows)
                logger.info(
                    "Loaded {} processor core factor rows from {}",
                    len(rows),
                    core_factor_yaml_path(),
                )

        await database.commit()
