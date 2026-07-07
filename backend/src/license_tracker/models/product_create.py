"""Product create model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import LicenseMetric


class ProductCreate(BaseModel):
    """Payload to create a product entitlement."""

    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(max_length=256)
    option_name: str | None = Field(default=None, max_length=256)
    metric: LicenseMetric = LicenseMetric.PROCESSOR
    quantity: int = Field(ge=0)
    notes: str | None = Field(default=None, max_length=4000)
