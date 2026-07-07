"""Database URL construction for Alembic migrations."""

from __future__ import annotations

from urllib.parse import quote_plus

from license_tracker.config import Settings, get_settings, resolve_sqlite_path


def build_database_url(settings: Settings | None = None) -> str:
    """Build a SQLAlchemy database URL for the configured backend.

    Used by Alembic migrations only. Runtime queries use Database backends.

    Args:
        settings (Settings | None): Application settings. Defaults to cached settings.

    Returns:
        str: SQLAlchemy connection URL.

    Raises:
        ValueError: If database_backend is not supported or required secrets are missing.
    """
    settings = settings or get_settings()
    app = settings.app
    backend = app.database_backend

    if backend == "oracle":
        password = settings.oracle_password
        if password is None:
            raise ValueError("LICENSE_TRACKER_ORACLE_PASSWORD is required for Oracle backend")
        oracle = app.oracle
        user = quote_plus(oracle.user)
        pwd = quote_plus(password.get_secret_value())
        service = quote_plus(oracle.service_name)
        return f"oracle+oracledb://{user}:{pwd}@{oracle.host}:{oracle.port}/?service_name={service}"

    if backend == "postgresql":
        password = settings.postgresql_password
        if password is None:
            raise ValueError(
                "LICENSE_TRACKER_POSTGRESQL_PASSWORD is required for PostgreSQL backend"
            )
        pg = app.postgresql
        user = quote_plus(pg.user)
        pwd = quote_plus(password.get_secret_value())
        return f"postgresql+asyncpg://{user}:{pwd}@{pg.host}:{pg.port}/{pg.database}"

    if backend == "sqlite":
        sqlite_path = resolve_sqlite_path(settings)
        if sqlite_path == ":memory:":
            return "sqlite+aiosqlite:///:memory:"
        return f"sqlite+aiosqlite:///{sqlite_path}"

    raise ValueError(f"Unsupported database_backend: {backend!r}")
