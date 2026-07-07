"""Catalog product create model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CatalogProductCreate(BaseModel):
    """Payload to create an Oracle catalog product row."""

    model_config = ConfigDict(extra="forbid")

    price_list_id: str = Field(max_length=64)
    category: str = Field(max_length=128)
    product_name: str = Field(max_length=256)
    option_name: str | None = Field(default=None, max_length=256)
    list_price_nup_usd: float | None = None
    list_price_nup_support_usd: float | None = None
    list_price_processor_usd: float | None = None
    list_price_processor_support_usd: float | None = None
    supports_nup: bool = False
    supports_processor: bool = False
