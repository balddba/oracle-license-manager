"""Host CPU profile domain model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from license_tracker.db.models.processor_core_factor import ProcessorCoreFactor
from license_tracker.domain.enums import CpuProfileSource
from license_tracker.domain.license_calc import calculate_processor_licenses


def _utcnow() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


class HostCpuProfile(BaseModel):
    """Versioned CPU inventory snapshot for a host."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    host_id: uuid.UUID
    cpu_model: str | None = None
    core_factor: float | None = None
    core_factor_id: uuid.UUID | None = None
    socket_count: int
    cores_per_socket: int
    threads_per_core: int = 1
    logical_processor_count: int
    source: CpuProfileSource = CpuProfileSource.MANUAL
    collected_at: datetime = Field(default_factory=_utcnow)
    created_at: datetime = Field(default_factory=_utcnow)
    matched_core_factor: ProcessorCoreFactor | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def physical_cores(self) -> int:
        """Return total physical cores (sockets * cores per socket).

        Returns:
            int: Physical core count.
        """
        return self.socket_count * self.cores_per_socket

    @computed_field  # type: ignore[prop-decorator]
    @property
    def processor_licenses_required(self) -> int | None:
        """Return required processor licenses when a core factor is known.

        Returns:
            int | None: Required processor license count.
        """
        if self.core_factor is None:
            return None
        return calculate_processor_licenses(self.physical_cores, self.core_factor)
