"""Product update model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import LicenseMetric


class ProductUpdate(BaseModel):
    """Payload to update a product entitlement."""

    model_config = ConfigDict(extra="forbid")

    product_name: str | None = Field(default=None, max_length=256)
    option_name: str | None = Field(default=None, max_length=256)
    metric: LicenseMetric | None = None
    quantity: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=4000)
