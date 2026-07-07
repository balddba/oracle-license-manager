"""Tests for database factory and domain mappers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import SecretStr

from license_tracker.config import Settings
from license_tracker.db.mappers import map_host
from license_tracker.db.queries.factory import create_database
from license_tracker.db.queries.oracle import OracleDatabase
from license_tracker.db.queries.sqlite import SqliteDatabase
from license_tracker.domain.enums import HostLicenseType


def test_create_database_sqlite(test_settings: Settings) -> None:
    """SQLite settings produce a SqliteDatabase instance."""
    database = create_database(test_settings)
    assert isinstance(database, SqliteDatabase)


def test_create_database_oracle(tmp_path: Path) -> None:
    """Oracle settings produce an OracleDatabase instance."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "database_backend: oracle\n"
        "oracle:\n"
        "  host: db.example.com\n"
        "  port: 1521\n"
        "  service_name: XEPDB1\n"
        "  user: license_tracker\n"
    )
    settings = Settings(config_path=config_path, oracle_password=SecretStr("secret"))
    database = create_database(settings)
    assert isinstance(database, OracleDatabase)


def test_create_database_oracle_requires_password(tmp_path: Path) -> None:
    """Oracle backend fails fast when the password secret is missing."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("database_backend: oracle\n")
    settings = Settings(config_path=config_path)
    with pytest.raises(ValueError, match="LICENSE_TRACKER_ORACLE_PASSWORD"):
        create_database(settings)


def test_create_database_unsupported(tmp_path: Path) -> None:
    """Unsupported backends raise ValueError."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("database_backend: postgresql\n")
    settings = Settings(config_path=config_path, postgresql_password=SecretStr("secret"))
    with pytest.raises(ValueError, match="Unsupported database_backend"):
        create_database(settings)


def test_map_host_coerces_uuid_and_bool() -> None:
    """Host mapper coerces UUID strings and integer booleans."""
    host_id = uuid.uuid4()
    now = datetime.now(UTC)
    host = map_host(
        {
            "id": str(host_id),
            "hostname": "db1",
            "fqdn": None,
            "ip_address": None,
            "environment": None,
            "license_type": "cpu",
            "named_users_required": None,
            "os_name": None,
            "notes": None,
            "ssh_enabled": 1,
            "ssh_port": 22,
            "ssh_user": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert host.id == host_id
    assert host.ssh_enabled is True
    assert host.license_type == HostLicenseType.CPU


@pytest.mark.asyncio
async def test_sqlite_get_host_not_found(database) -> None:
    """Missing hosts return None."""
    assert await database.get_host(uuid.uuid4()) is None
