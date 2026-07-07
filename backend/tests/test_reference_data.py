"""Tests for reference data seeding."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from license_tracker.config import Settings, resolve_sqlite_path
from license_tracker.db.migrate import run_migrations_async
from license_tracker.db.reference_data import ensure_reference_data
from license_tracker.db.session import reset_session_state


@pytest.mark.asyncio
async def test_ensure_reference_data_loads_catalog_when_empty(
    test_settings: Settings,
) -> None:
    """Empty catalog tables are populated from the committed YAML file."""
    await run_migrations_async(test_settings)
    reset_session_state()

    await ensure_reference_data(test_settings)

    db_path = resolve_sqlite_path(test_settings)
    verify_engine = create_engine(f"sqlite:///{db_path}")
    with verify_engine.connect() as connection:
        catalog_count = connection.execute(
            text("SELECT COUNT(*) FROM catalog_products")
        ).scalar_one()
        core_factor_count = connection.execute(
            text("SELECT COUNT(*) FROM processor_core_factors")
        ).scalar_one()
        default_count = connection.execute(
            text("SELECT COUNT(*) FROM processor_core_factors WHERE is_default = 1")
        ).scalar_one()
    verify_engine.dispose()

    assert catalog_count > 0
    assert core_factor_count >= 50
    assert default_count == 1
