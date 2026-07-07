"""Run Alembic migrations with optional settings override."""

from __future__ import annotations

import asyncio

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command
from license_tracker.config import Settings, find_project_root, get_settings
from license_tracker.db.engine import build_database_url

_settings_override: Settings | None = None


def _column_names(engine, table_name: str) -> set[str]:
    """Return column names for a table.

    Args:
        engine: Sync SQLAlchemy engine.
        table_name (str): Table to inspect.

    Returns:
        set[str]: Column names present on the table.
    """
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _schema_matches_revision(engine, revision: str) -> bool:
    """Return whether the live schema includes columns for a revision.

    Args:
        engine: Sync SQLAlchemy engine.
        revision (str): Alembic revision id.

    Returns:
        bool: True when required columns for the revision are present.
    """
    # Revision 0003 requires catalog_products table, agreement_id on hosts, and core cpu columns
    if revision == "0003_catalog_products":
        tables = set(inspect(engine).get_table_names())
        host_columns = _column_names(engine, "hosts")
        cpu_columns = _column_names(engine, "host_cpu_profiles")
        return (
            "catalog_products" in tables
            and "agreement_id" in host_columns
            and {"core_factor", "core_factor_id"}.issubset(cpu_columns)
        )
    # Revision 0002 checks if core factor reference table and host agreement columns exist
    if revision == "0002_processor_core_factors":
        tables = set(inspect(engine).get_table_names())
        host_columns = _column_names(engine, "hosts")
        cpu_columns = _column_names(engine, "host_cpu_profiles")
        return (
            "processor_core_factors" in tables
            and "agreement_id" in host_columns
            and {"core_factor", "core_factor_id"}.issubset(cpu_columns)
        )
    return True


def _infer_legacy_stamp_revision(engine) -> str | None:
    """Infer which Alembic revision matches an existing legacy schema.

    Args:
        engine: Sync SQLAlchemy engine.

    Returns:
        str | None: Revision id to stamp, or None when not a legacy database.
    """
    tables = set(inspect(engine).get_table_names())
    # If the base table is not found, this is a clean DB install, not a legacy upgrade path
    if "license_agreements" not in tables:
        return None
    # Inspect tables sequentially from latest down to initial revision to find matches
    if _schema_matches_revision(engine, "0003_catalog_products"):
        return "0003_catalog_products"
    if _schema_matches_revision(engine, "0002_processor_core_factors"):
        return "0002_processor_core_factors"
    return "0001_initial"


def get_migration_settings() -> Settings:
    """Return settings used for the current migration run.

    Returns:
        Settings: Active migration settings.
    """
    return _settings_override or get_settings()


def _alembic_config() -> Config:
    """Build the Alembic config for this project.

    Returns:
        Config: Alembic configuration object.
    """
    root = find_project_root()
    cfg = Config(str(root / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "backend" / "alembic"))
    return cfg


def _sync_database_url(settings: Settings) -> str:
    """Convert the async SQLAlchemy URL to a sync URL for inspection.

    Args:
        settings (Settings): Application settings.

    Returns:
        str: Sync SQLAlchemy database URL.
    """
    url = build_database_url(settings)
    # Convert standard aiosqlite async protocol prefix to sync sqlite prefix
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    # Convert asyncpg Postgres prefix to sync psycopg prefix
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def _current_alembic_revision(engine) -> str | None:
    """Return the stored Alembic revision for a database.

    Args:
        engine: Sync SQLAlchemy engine.

    Returns:
        str | None: Current revision id when recorded.
    """
    inspector = inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        return None
    with engine.connect() as connection:
        row = connection.execute(text("SELECT version_num FROM alembic_version")).first()
    if row is None:
        return None
    return str(row[0])


def _has_legacy_unversioned_schema(engine) -> bool:
    """Return whether the database has pre-Alembic tables without a revision.

    Args:
        engine: Sync SQLAlchemy engine.

    Returns:
        bool: True when legacy tables exist and Alembic has not been stamped.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    return "license_agreements" in tables and _current_alembic_revision(engine) is None


def _stamp_revision(settings: Settings, revision: str) -> None:
    """Stamp the database with an Alembic revision without running migrations.

    Args:
        settings (Settings): Application settings.
        revision (str): Alembic revision id.
    """
    global _settings_override

    _settings_override = settings
    try:
        command.stamp(_alembic_config(), revision)
    finally:
        _settings_override = None


def _prepare_legacy_database(settings: Settings) -> None:
    """Stamp legacy SQLite databases created before Alembic was introduced.

    Args:
        settings (Settings): Application settings.
    """
    if settings.app.database_backend != "sqlite":
        return

    engine = create_engine(_sync_database_url(settings))
    try:
        if _current_alembic_revision(engine) is not None:
            return
        revision = _infer_legacy_stamp_revision(engine)
        if revision is not None:
            _stamp_revision(settings, revision)
    finally:
        engine.dispose()


def _run_alembic_upgrade(settings: Settings) -> None:
    """Execute Alembic upgrade head in a synchronous context.

    Args:
        settings (Settings): Settings to use for the database URL.
    """
    global _settings_override

    # Stamp legacy (unversioned) databases to prevent Alembic from re-creating tables
    _prepare_legacy_database(settings)

    # Set override so that Alembic's env.py loads the correct database connection configurations
    _settings_override = settings
    try:
        command.upgrade(_alembic_config(), "head")
    finally:
        # Reset override to prevent polluting context on subsequent DB interactions
        _settings_override = None


async def run_migrations_async(settings: Settings | None = None) -> None:
    """Apply all Alembic migrations through head from async code.

    Args:
        settings (Settings | None): Settings to use for the database URL.
    """
    resolved = settings or get_settings()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_alembic_upgrade, resolved)


def run_migrations(settings: Settings | None = None) -> None:
    """Apply all Alembic migrations through head.

    Args:
        settings (Settings | None): Settings to use for the database URL.
    """
    _run_alembic_upgrade(settings or get_settings())
