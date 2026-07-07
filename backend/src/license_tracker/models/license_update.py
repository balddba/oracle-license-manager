"""License update model."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import LicenseStatus


class LicenseUpdate(BaseModel):
    """Payload to update a license agreement."""

    model_config = ConfigDict(extra="forbid")

    csi: str | None = Field(default=None, max_length=64)
    customer_name: str | None = Field(default=None, max_length=256)
    support_level: str | None = Field(default=None, max_length=128)
    start_date: date | None = None
    renewal_date: date | None = None
    status: LicenseStatus | None = None
    notes: str | None = Field(default=None, max_length=4000)
