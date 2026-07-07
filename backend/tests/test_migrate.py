"""Tests for database migration helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from license_tracker.config import Settings, resolve_sqlite_path
from license_tracker.db.migrate import (
    _has_legacy_unversioned_schema,
    _infer_legacy_stamp_revision,
    _run_alembic_upgrade,
)
from license_tracker.db.session import reset_session_state


def _create_partial_legacy_schema(db_path: Path) -> None:
    """Create a pre-0002 schema matching older create_all databases.

    Args:
        db_path (Path): SQLite database file path.
    """
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE license_agreements (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    csi VARCHAR(64) NOT NULL,
                    customer_name VARCHAR(256) NOT NULL,
                    support_level VARCHAR(128),
                    start_date DATE,
                    renewal_date DATE,
                    status VARCHAR(32) NOT NULL,
                    notes VARCHAR(4000),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE hosts (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    hostname VARCHAR(256) NOT NULL,
                    fqdn VARCHAR(512),
                    ip_address VARCHAR(45),
                    environment VARCHAR(64),
                    os_name VARCHAR(128),
                    notes VARCHAR(4000),
                    ssh_enabled BOOLEAN NOT NULL,
                    ssh_port INTEGER NOT NULL,
                    ssh_user VARCHAR(128),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE host_cpu_profiles (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    host_id VARCHAR(36) NOT NULL,
                    cpu_model VARCHAR(256),
                    socket_count INTEGER NOT NULL,
                    cores_per_socket INTEGER NOT NULL,
                    threads_per_core INTEGER NOT NULL,
                    logical_processor_count INTEGER NOT NULL,
                    source VARCHAR(32) NOT NULL,
                    collected_at DATETIME NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE processor_core_factors (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    name VARCHAR(256) NOT NULL,
                    match_pattern VARCHAR(256) NOT NULL,
                    core_factor FLOAT NOT NULL,
                    priority INTEGER NOT NULL,
                    is_default BOOLEAN NOT NULL,
                    notes VARCHAR(4000),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE catalog_products (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    price_list_id VARCHAR(64) NOT NULL,
                    category VARCHAR(128) NOT NULL,
                    product_name VARCHAR(256) NOT NULL,
                    option_name VARCHAR(256),
                    list_price_nup_usd FLOAT,
                    list_price_nup_support_usd FLOAT,
                    list_price_processor_usd FLOAT,
                    list_price_processor_support_usd FLOAT,
                    supports_nup BOOLEAN NOT NULL,
                    supports_processor BOOLEAN NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
    engine.dispose()


def test_infer_legacy_stamp_revision_stamps_0001_for_partial_schema(
    test_settings: Settings,
) -> None:
    """Legacy schemas missing 0002 columns stamp at 0001, not 0003."""
    db_path = resolve_sqlite_path(test_settings)
    _create_partial_legacy_schema(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        assert _infer_legacy_stamp_revision(engine) == "0001_initial"
    finally:
        engine.dispose()
        reset_session_state()


def test_infer_legacy_stamp_revision_returns_none_without_agreements(tmp_path) -> None:
    """Databases without license tables are not legacy-stamped."""
    db_path = tmp_path / "empty.db"
    engine = create_engine(f"sqlite:///{db_path}")
    try:
        assert _infer_legacy_stamp_revision(engine) is None
    finally:
        engine.dispose()


def test_has_legacy_unversioned_schema_detects_old_database(tmp_path) -> None:
    """Legacy databases without alembic_version are detected."""
    db_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE license_agreements (
                    id VARCHAR(36) NOT NULL PRIMARY KEY
                )
                """
            )
        )
    try:
        assert _has_legacy_unversioned_schema(engine) is True
    finally:
        engine.dispose()


def test_partial_legacy_schema_upgrades_through_head(test_settings: Settings) -> None:
    """Partial legacy schemas upgrade through head with required columns."""
    db_path = resolve_sqlite_path(test_settings)
    _create_partial_legacy_schema(db_path)

    _run_alembic_upgrade(test_settings)

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        host_columns = {column["name"] for column in inspect(engine).get_columns("hosts")}
        assert "agreement_id" not in host_columns
        tables = set(inspect(engine).get_table_names())
        assert "host_entitlements" in tables

        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
        assert revision == "0012_normalize_enum_values"
    finally:
        engine.dispose()
        reset_session_state()


def test_repair_migration_adds_missing_host_columns(test_settings: Settings) -> None:
    """Stamped legacy databases missing 0002 columns are repaired at head."""
    db_path = resolve_sqlite_path(test_settings)
    _create_partial_legacy_schema(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(
            text(
                "INSERT INTO alembic_version (version_num) VALUES ('0004_backfill_reference_data')"
            )
        )
    engine.dispose()

    _run_alembic_upgrade(test_settings)

    verify_engine = create_engine(f"sqlite:///{db_path}")
    try:
        host_columns = {column["name"] for column in inspect(verify_engine).get_columns("hosts")}
        assert "agreement_id" not in host_columns
        tables = set(inspect(verify_engine).get_table_names())
        assert "host_entitlements" in tables
        with verify_engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
        assert revision == "0012_normalize_enum_values"
    finally:
        verify_engine.dispose()
        reset_session_state()
