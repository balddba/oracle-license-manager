"""Oracle technology price list catalog product domain model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


class CatalogProduct(BaseModel):
    """Reference product from the Oracle technology global price list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    price_list_id: str
    category: str
    product_name: str
    option_name: str | None = None
    list_price_nup_usd: float | None = None
    list_price_nup_support_usd: float | None = None
    list_price_processor_usd: float | None = None
    list_price_processor_support_usd: float | None = None
    supports_nup: bool = False
    supports_processor: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
