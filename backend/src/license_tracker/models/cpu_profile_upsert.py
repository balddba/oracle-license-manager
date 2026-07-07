"""CPU profile upsert model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CpuProfileUpsert(BaseModel):
    """Payload to create or update a host CPU profile."""

    model_config = ConfigDict(extra="forbid")

    cpu_model: str | None = Field(default=None, max_length=256)
    core_factor: float | None = Field(default=None, gt=0)
    socket_count: int = Field(ge=1)
    cores_per_socket: int = Field(ge=1)
    threads_per_core: int = Field(default=1, ge=1)
    logical_processor_count: int | None = Field(default=None, ge=1)
