"""Database seed data loaded during migrations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from license_tracker.config import find_project_root

CATALOG_YAML_NAME = "oracle-technology-price-list-070617.yaml"
CORE_FACTOR_YAML_NAME = "processor-core-factor-table-070634.yaml"


def catalog_yaml_path() -> Path:
    """Return the committed Oracle catalog YAML path.

    Returns:
        Path: Catalog YAML file path.
    """
    return find_project_root() / "data" / CATALOG_YAML_NAME


def core_factor_yaml_path() -> Path:
    """Return the committed Oracle processor core factor YAML path.

    Returns:
        Path: Core factor YAML file path.
    """
    return find_project_root() / "data" / CORE_FACTOR_YAML_NAME


def load_catalog_seed_rows() -> list[dict[str, Any]]:
    """Load Oracle catalog rows from the committed YAML file.

    Returns:
        list[dict[str, Any]]: Catalog rows without primary keys or timestamps.
    """
    yaml_path = catalog_yaml_path()
    if not yaml_path.is_file():
        return []

    with yaml_path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    price_list_id = str(payload.get("price_list_id", "technology-price-list-070617"))
    rows: list[dict[str, Any]] = []
    for row in payload.get("products", []):
        rows.append(
            {
                "price_list_id": price_list_id,
                "category": str(row["category"]),
                "product_name": str(row["product_name"]),
                "option_name": row.get("option_name"),
                "list_price_nup_usd": row.get("list_price_nup_usd"),
                "list_price_nup_support_usd": row.get("list_price_nup_support_usd"),
                "list_price_processor_usd": row.get("list_price_processor_usd"),
                "list_price_processor_support_usd": row.get("list_price_processor_support_usd"),
                "supports_nup": bool(row.get("supports_nup")),
                "supports_processor": bool(row.get("supports_processor")),
            }
        )
    return rows


def catalog_product_insert_rows() -> list[dict[str, Any]]:
    """Build catalog product rows for Alembic bulk insert.

    Returns:
        list[dict[str, Any]]: Rows including ids and timestamps.
    """
    now = datetime.now(UTC)
    return [
        {
            "id": str(uuid.uuid4()),
            "created_at": now,
            "updated_at": now,
            **row,
        }
        for row in load_catalog_seed_rows()
    ]


def load_core_factor_seed_rows() -> list[dict[str, Any]]:
    """Load Oracle processor core factor rows from the committed YAML file.

    Returns:
        list[dict[str, Any]]: Core factor rows without primary keys or timestamps.
    """
    yaml_path = core_factor_yaml_path()
    if not yaml_path.is_file():
        return []

    with yaml_path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    source_url = payload.get("source_url")
    rows: list[dict[str, Any]] = []
    for row in payload.get("factors", []):
        notes = row.get("notes")
        if notes is None and source_url:
            notes = f"Source: {source_url}"
        rows.append(
            {
                "name": str(row["name"]),
                "match_pattern": str(row["match_pattern"]),
                "core_factor": float(row["core_factor"]),
                "priority": int(row.get("priority", 0)),
                "is_default": bool(row.get("is_default", False)),
                "notes": notes,
            }
        )
    return rows


def processor_core_factor_insert_rows() -> list[dict[str, Any]]:
    """Build processor core factor rows for Alembic bulk insert.

    Returns:
        list[dict[str, Any]]: Rows including ids and timestamps.
    """
    now = datetime.now(UTC)
    return [
        {
            "id": str(uuid.uuid4()),
            "created_at": now,
            "updated_at": now,
            **row,
        }
        for row in load_core_factor_seed_rows()
    ]
