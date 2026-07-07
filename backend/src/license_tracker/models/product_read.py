"""Product read model."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from license_tracker.domain.enums import LicenseMetric


class ProductRead(BaseModel):
    """Product entitlement API response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agreement_id: uuid.UUID
    product_name: str
    option_name: str | None
    metric: LicenseMetric
    quantity: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
