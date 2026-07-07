"""Host update model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import HostEnvironment, HostLicenseType


class HostUpdate(BaseModel):
    """Payload to update a host."""

    model_config = ConfigDict(extra="forbid")

    hostname: str | None = Field(default=None, max_length=256)
    fqdn: str | None = Field(default=None, max_length=512)
    ip_address: str | None = Field(default=None, max_length=45)
    environment: HostEnvironment | None = None
    license_type: HostLicenseType | None = None
    os_name: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=4000)
    ssh_enabled: bool | None = None
    ssh_port: int | None = Field(default=None, ge=1, le=65535)
    ssh_user: str | None = Field(default=None, max_length=128)
