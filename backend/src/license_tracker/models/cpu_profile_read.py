"""CPU profile read model."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from license_tracker.domain.enums import CpuProfileSource


class CpuProfileRead(BaseModel):
    """CPU profile API response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    host_id: uuid.UUID
    cpu_model: str | None
    core_factor: float | None
    core_factor_name: str | None = None
    socket_count: int
    cores_per_socket: int
    threads_per_core: int
    logical_processor_count: int
    physical_cores: int
    processor_licenses_required: int | None
    source: CpuProfileSource
    collected_at: datetime
    created_at: datetime
