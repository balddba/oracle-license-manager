"""Pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from license_tracker.config import Settings, get_settings
from license_tracker.db.queries.base import Database
from license_tracker.db.queries.factory import create_database
from license_tracker.db.session import get_database, init_db, reset_session_state
from license_tracker.main import create_app


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Build settings pointing at a file-backed SQLite database."""
    config_path = tmp_path / "config.yaml"
    db_path = tmp_path / "test.db"
    config_path.write_text(
        f"database_backend: sqlite\nsqlite:\n  path: '{db_path}'\n",
    )
    reset_session_state()
    get_settings.cache_clear()
    return Settings(config_path=config_path)


@pytest_asyncio.fixture
async def database(test_settings: Settings) -> AsyncGenerator[Database]:
    """Yield a connected SQLite database for direct service tests."""
    await init_db(test_settings)
    db = create_database(test_settings)
    async with db:
        yield db
        await db.commit()


@pytest_asyncio.fixture
async def client(test_settings: Settings) -> AsyncGenerator[AsyncClient]:
    """HTTP client with overridden settings and database."""
    get_settings.cache_clear()
    await init_db(test_settings)
    app = create_app()

    async def override_database() -> AsyncGenerator[Database]:
        db = create_database(test_settings)
        async with db:
            try:
                yield db
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    app.dependency_overrides[get_database] = override_database

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client

    app.dependency_overrides.clear()
    reset_session_state()
    get_settings.cache_clear()
