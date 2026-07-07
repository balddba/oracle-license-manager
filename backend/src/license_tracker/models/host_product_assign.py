"""Host product assign model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HostProductAssign(BaseModel):
    """Payload to assign a pooled product license to a host.

    License type is taken from the host (server-level CPU or NUP).
    """

    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(max_length=256)
    option_name: str | None = Field(default=None, max_length=256)
    notes: str | None = Field(default=None, max_length=4000)
