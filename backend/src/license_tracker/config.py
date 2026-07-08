"""Application configuration loaded from YAML and environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class OracleConfig(BaseModel):
    """Oracle database connection settings."""

    model_config = {"extra": "forbid"}

    host: str = "localhost"
    port: int = 1521
    service_name: str = "XEPDB1"
    user: str = "license_tracker"


class PostgresConfig(BaseModel):
    """PostgreSQL database connection settings."""

    model_config = {"extra": "forbid"}

    host: str = "localhost"
    port: int = 5432
    database: str = "license_tracker"
    user: str = "license_tracker"


class SqliteConfig(BaseModel):
    """SQLite database settings (local dev and tests)."""

    model_config = {"extra": "forbid"}

    path: str = "data/db/license_tracker.db"


class SshConfig(BaseModel):
    """SSH defaults for host CPU probing (Phase 4)."""

    model_config = {"extra": "forbid"}

    default_port: int = 22
    connect_timeout_seconds: int = 15


class AppConfig(BaseModel):
    """Root YAML configuration document."""

    model_config = {"extra": "forbid"}

    database_backend: Literal["oracle", "postgresql", "sqlite"] = "sqlite"
    oracle: OracleConfig = Field(default_factory=OracleConfig)
    postgresql: PostgresConfig = Field(default_factory=PostgresConfig)
    sqlite: SqliteConfig = Field(default_factory=SqliteConfig)
    ssh: SshConfig = Field(default_factory=SshConfig)


class Settings(BaseSettings):
    """Runtime settings merged from YAML file and environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="LICENSE_TRACKER_",
        env_nested_delimiter="__",
        extra="forbid",
    )

    config_path: Path = Path("config/license-tracker.yaml")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    oracle_password: SecretStr | None = None
    postgresql_password: SecretStr | None = None
    sqlite_path: str | None = None

    @property
    def app(self) -> AppConfig:
        """Load and validate the YAML application config."""
        return load_app_config(self.config_path)


def _resolve_config_path(path: Path) -> Path:
    """Resolve config file path, checking repo-root and backend-relative locations.

    Args:
        path (Path): Requested config path.

    Returns:
        Path: Existing config file or preferred default path.
    """
    candidates = [
        path,
        Path("../config/license-tracker.yaml"),
        Path("config/license-tracker.yaml"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    example_candidates = [
        path.parent / "license-tracker.example.yaml",
        Path("../config/license-tracker.example.yaml"),
        Path("config/license-tracker.example.yaml"),
    ]
    for example in example_candidates:
        if example.is_file():
            return example
    return path


def load_app_config(path: Path) -> AppConfig:
    """Load application config from a YAML file.

    Args:
        path (Path): Path to the YAML config file.

    Returns:
        AppConfig: Validated configuration.
    """
    resolved = _resolve_config_path(path)
    if not resolved.is_file():
        return AppConfig()
    with resolved.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}
    return AppConfig.model_validate(raw)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()


def find_project_root() -> Path:
    """Locate the repository root containing config/ and backend/.

    Returns:
        Path: Project root directory, or current working directory if not found.
    """
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "config").is_dir() and (candidate / "backend").is_dir():
            return candidate
    return cwd


def resolve_sqlite_path(settings: Settings | None = None) -> str:
    """Resolve the configured SQLite database file to an absolute path.

    Args:
        settings (Settings | None): Application settings.

    Returns:
        str: Absolute or in-memory SQLite path.
    """
    settings = settings or get_settings()
    configured = settings.sqlite_path or settings.app.sqlite.path
    if configured == ":memory:":
        return configured
    path = Path(configured)
    if not path.is_absolute():
        path = find_project_root() / path
    return str(path)
