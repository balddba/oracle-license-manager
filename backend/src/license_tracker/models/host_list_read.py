"""Host list read model."""

from __future__ import annotations

from pydantic import Field

from license_tracker.models.host_read import HostRead


class HostListRead(HostRead):
    """Host list row with assigned products and license requirement."""

    assigned_products: list[str] = Field(default_factory=list)
    cpu_model: str | None = None
    socket_count: int | None = None
    cores_per_socket: int | None = None
    physical_cores: int | None = None
    core_factor: float | None = None
    core_factor_name: str | None = None
    processor_licenses_required: int | None = None
    licenses_required_label: str | None = None
    licenses_required_detail: list[str] = Field(default_factory=list)
