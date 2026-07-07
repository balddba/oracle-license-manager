"""License agreement domain model."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.db.models.product_entitlement import ProductEntitlement
from license_tracker.domain.enums import LicenseStatus


def _utcnow() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


class LicenseAgreement(BaseModel):
    """Oracle license agreement (CSI-level record)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    csi: str
    customer_name: str
    support_level: str | None = None
    start_date: date | None = None
    renewal_date: date | None = None
    status: LicenseStatus = LicenseStatus.ACTIVE
    notes: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    products: list[ProductEntitlement] = Field(default_factory=list)
