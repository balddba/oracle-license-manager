"""Product update model."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import LicenseMetric


class ProductUpdate(BaseModel):
    """Payload to update a product entitlement."""

    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID | None = None
    metric: LicenseMetric | None = None
    quantity: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=4000)
