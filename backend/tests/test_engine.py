"""Tests for database URL builder."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import SecretStr

from license_tracker.config import Settings, get_settings, resolve_sqlite_path
from license_tracker.db.engine import build_database_url
from license_tracker.db.session import reset_session_state


def test_build_sqlite_url(tmp_path: Path) -> None:
    """SQLite backend returns aiosqlite URL with resolved absolute path."""
    db_path = tmp_path / "test.db"
    config_path = tmp_path / "cfg.yaml"
    config_path.write_text(f"database_backend: sqlite\nsqlite:\n  path: {db_path}\n")
    reset_session_state()
    get_settings.cache_clear()
    settings = Settings(config_path=config_path)
    assert build_database_url(settings) == f"sqlite+aiosqlite:///{db_path}"


def test_resolve_sqlite_path_uses_project_data_dir() -> None:
    """Default config resolves SQLite file under project data/."""
    get_settings.cache_clear()
    settings = Settings()
    resolved = Path(resolve_sqlite_path(settings))
    assert resolved.name == "license_tracker.db"
    assert resolved.parent.name == "db"
    assert resolved.parent.parent.name == "data"


def test_build_oracle_requires_password(tmp_path: Path) -> None:
    """Oracle backend fails without password."""
    config_path = tmp_path / "cfg.yaml"
    config_path.write_text("database_backend: oracle\n")
    settings = Settings(config_path=config_path, oracle_password=None)
    with pytest.raises(ValueError, match="ORACLE_PASSWORD"):
        build_database_url(settings)


def test_build_oracle_url(tmp_path: Path) -> None:
    """Oracle backend builds oracledb URL."""
    config_path = tmp_path / "cfg.yaml"
    config_path.write_text(
        "database_backend: oracle\noracle:\n  host: dbhost\n  port: 1521\n"
        "  service_name: ORCL\n  user: appuser\n"
    )
    settings = Settings(
        config_path=config_path,
        oracle_password=SecretStr("secret"),
    )
    url = build_database_url(settings)
    assert url.startswith("oracle+oracledb://")
    assert "appuser" in url
    assert "dbhost" in url


def test_unknown_backend_raises(tmp_path: Path) -> None:
    """Invalid backend name raises ValueError."""
    from unittest.mock import Mock

    settings = Mock()
    settings.app.database_backend = "invalid"
    with pytest.raises(ValueError, match="Unsupported"):
        build_database_url(settings)


def test_resolve_sqlite_path_override() -> None:
    """Verify that settings can override the SQLite path via sqlite_path."""
    get_settings.cache_clear()
    settings = Settings(sqlite_path="/tmp/override_license_tracker.db")
    resolved = resolve_sqlite_path(settings)
    assert resolved == "/tmp/override_license_tracker.db"
