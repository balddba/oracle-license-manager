"""Host create model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from license_tracker.domain.enums import HostEnvironment, HostLicenseType


class HostCreate(BaseModel):
    """Payload to create a host."""

    model_config = ConfigDict(extra="forbid")

    hostname: str = Field(max_length=256)
    fqdn: str | None = Field(default=None, max_length=512)
    ip_address: str | None = Field(default=None, max_length=45)
    environment: HostEnvironment | None = None
    license_type: HostLicenseType = HostLicenseType.CPU
    os_name: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=4000)
    ssh_enabled: bool = False
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_user: str | None = Field(default=None, max_length=128)
