"""Host inventory domain model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import HostEnvironment, HostLicenseType


def _utcnow() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


class Host(BaseModel):
    """Server host inventory record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    hostname: str
    fqdn: str | None = None
    ip_address: str | None = None
    environment: HostEnvironment | None = None
    license_type: HostLicenseType = HostLicenseType.CPU
    named_users_required: int | None = None
    os_name: str | None = None
    notes: str | None = None
    ssh_enabled: bool = False
    ssh_port: int = 22
    ssh_user: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
