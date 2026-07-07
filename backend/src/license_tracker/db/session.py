"""Request-scoped database lifecycle."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from loguru import logger

from license_tracker.config import Settings, get_settings, resolve_sqlite_path
from license_tracker.db.migrate import run_migrations_async
from license_tracker.db.queries.base import Database
from license_tracker.db.queries.factory import create_database
from license_tracker.db.reference_data import ensure_reference_data

_settings: Settings | None = None


def configure_database(settings: Settings | None = None) -> None:
    """Set the settings used to create request-scoped databases.

    Args:
        settings (Settings | None): Application settings override.
    """
    global _settings
    _settings = settings


def reset_session_state() -> None:
    """Reset cached database settings (for tests)."""
    global _settings
    _settings = None


async def get_database() -> AsyncGenerator[Database]:
    """Yield a connected database for request scope.

    Yields:
        Database: Open database; commits on success, rolls back on error.
    """
    settings = _settings or get_settings()
    database = create_database(settings)
    async with database:
        try:
            yield database
            await database.commit()
        except Exception:
            await database.rollback()
            raise


async def init_db(settings: Settings | None = None) -> None:
    """Build the SQLite schema and reference data via Alembic migrations.

    For Oracle and PostgreSQL, run Alembic separately during deployment.

    Args:
        settings (Settings | None): Application settings.
    """
    settings = settings or get_settings()
    configure_database(settings)

    if settings.app.database_backend == "sqlite":
        sqlite_path = resolve_sqlite_path(settings)
        if sqlite_path != ":memory:":
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)

    logger.info("Verifying database connectivity...")
    try:
        database = create_database(settings)
        async with database:
            await database.verify_connection()
        logger.info("Database connectivity verified successfully.")
    except Exception:
        logger.exception("Database connectivity verification failed")
        raise

    if settings.app.database_backend != "sqlite":
        return

    try:
        await run_migrations_async(settings)
        await ensure_reference_data(settings)
    except Exception:
        logger.exception("Failed to initialize SQLite database")
        raise
