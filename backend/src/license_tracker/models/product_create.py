"""Product create model."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import LicenseMetric


class ProductCreate(BaseModel):
    """Payload to create a product entitlement."""

    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    metric: LicenseMetric = LicenseMetric.PROCESSOR
    quantity: int = Field(ge=0)
    notes: str | None = Field(default=None, max_length=4000)
