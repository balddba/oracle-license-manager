"""Catalog product read model."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class CatalogProductRead(BaseModel):
    """Oracle catalog product API response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    price_list_id: str
    category: str
    product_name: str
    option_name: str | None
    list_price_nup_usd: float | None
    list_price_nup_support_usd: float | None
    list_price_processor_usd: float | None
    list_price_processor_support_usd: float | None
    supports_nup: bool
    supports_processor: bool
