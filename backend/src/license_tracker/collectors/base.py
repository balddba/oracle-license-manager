"""Host CPU probe protocol and snapshot types."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict

from license_tracker.db.models.host import Host


class SshCredentials(BaseModel):
    """SSH credentials supplied at probe time (never persisted)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    user: str
    password: str | None = None
    key_path: str | None = None


class HostCpuSnapshot(BaseModel):
    """CPU inventory collected from a remote host."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cpu_model: str | None
    socket_count: int
    cores_per_socket: int
    threads_per_core: int
    logical_processor_count: int


class HostProbe(Protocol):
    """Protocol for on-demand host CPU collection."""

    async def collect_cpu(
        self,
        host: Host,
        credentials: SshCredentials,
    ) -> HostCpuSnapshot:
        """Collect CPU inventory from a remote host.

        Args:
            host (Host): Target host record.
            credentials (SshCredentials): SSH authentication material.

        Returns:
            HostCpuSnapshot: Parsed CPU inventory.
        """
        ...
