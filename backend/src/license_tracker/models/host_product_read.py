"""Host product read model."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from license_tracker.domain.enums import HostLicenseType, LicenseMetric


class HostProductRead(BaseModel):
    """Product license assigned to a host."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    host_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    option_name: str | None
    license_type: HostLicenseType
    metric: LicenseMetric
    notes: str | None
    created_at: datetime
    updated_at: datetime
