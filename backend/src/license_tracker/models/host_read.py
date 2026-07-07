"""Host read model."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from license_tracker.domain.enums import HostEnvironment, HostLicenseType


class HostRead(BaseModel):
    """Host API response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hostname: str
    fqdn: str | None
    ip_address: str | None
    environment: HostEnvironment | None
    license_type: HostLicenseType
    named_users_required: int | None
    os_name: str | None
    notes: str | None
    ssh_enabled: bool
    ssh_port: int
    ssh_user: str | None
    created_at: datetime
    updated_at: datetime
