"""Factory for database backends."""

from __future__ import annotations

from license_tracker.config import Settings, get_settings, resolve_sqlite_path
from license_tracker.db.queries.base import Database
from license_tracker.db.queries.oracle import OracleDatabase
from license_tracker.db.queries.sqlite import SqliteDatabase


def create_database(settings: Settings | None = None) -> Database:
    """Create a database backend for the configured driver.

    Args:
        settings (Settings | None): Application settings.

    Returns:
        Database: Backend instance (not yet connected).

    Raises:
        ValueError: If the backend is unsupported or required secrets are missing.
    """
    settings = settings or get_settings()
    backend = settings.app.database_backend

    if backend == "sqlite":
        return SqliteDatabase(resolve_sqlite_path(settings))

    if backend == "oracle":
        password = settings.oracle_password
        if password is None:
            raise ValueError("LICENSE_TRACKER_ORACLE_PASSWORD is required for Oracle backend")
        oracle = settings.app.oracle
        return OracleDatabase(
            user=oracle.user,
            password=password,
            host=oracle.host,
            port=oracle.port,
            service_name=oracle.service_name,
        )

    raise ValueError(f"Unsupported database_backend: {backend!r}")
