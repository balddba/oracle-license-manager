"""Host product assign model."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class HostProductAssign(BaseModel):
    """Payload to assign a pooled product license to a host.

    License type is taken from the host (server-level CPU or NUP).
    """

    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=4000)
