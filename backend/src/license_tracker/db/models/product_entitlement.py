"""Product entitlement domain model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import LicenseMetric


def _utcnow() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


class ProductEntitlement(BaseModel):
    """Licensed product entitlement under an agreement."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    agreement_id: uuid.UUID
    product_name: str
    option_name: str | None = None
    metric: LicenseMetric = LicenseMetric.PROCESSOR
    quantity: int
    notes: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
