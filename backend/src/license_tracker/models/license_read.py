"""License read model."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from license_tracker.domain.enums import LicenseStatus


class LicenseRead(BaseModel):
    """License agreement API response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    csi: str
    customer_name: str
    support_level: str | None
    start_date: date | None
    renewal_date: date | None
    status: LicenseStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime
