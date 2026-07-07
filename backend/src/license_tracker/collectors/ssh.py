"""SSH-based host CPU probe (Phase 4 stub)."""

from __future__ import annotations

from fastapi import HTTPException, status

from license_tracker.collectors.base import HostCpuSnapshot, SshCredentials
from license_tracker.db.models.host import Host


class SshHostProbe:
    """SSH host CPU collector; not implemented in v1."""

    async def collect_cpu(
        self,
        host: Host,
        credentials: SshCredentials,
    ) -> HostCpuSnapshot:
        """Collect CPU data via SSH.

        Args:
            host (Host): Target host.
            credentials (SshCredentials): SSH credentials.

        Raises:
            HTTPException: SSH probe is not enabled in v1.
        """
        # Explicitly discard parameters to suppress unused variable lint warnings in this stub
        _ = host, credentials
        # Raise standard 501 exception since active SSH probing is planned for Phase 4
        raise self.not_implemented_error()

    @staticmethod
    def not_implemented_error() -> HTTPException:
        """Return the standard 501 response for the probe stub.

        Returns:
            HTTPException: Not implemented error.
        """
        # Return 501 Not Implemented response to signal API clients that SSH probing is disabled
        return HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SSH CPU probe is not enabled yet",
        )
