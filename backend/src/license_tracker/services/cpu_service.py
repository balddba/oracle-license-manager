"""Host CPU profile service."""

from __future__ import annotations

import uuid

from license_tracker.db.models.host_cpu_profile import HostCpuProfile
from license_tracker.db.queries.base import Database
from license_tracker.domain.enums import CpuProfileSource
from license_tracker.models import CpuProfileUpsert
from license_tracker.services.core_factor_service import CoreFactorService


class CpuService:
    """Data access for host CPU profiles."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database
        self._core_factors = CoreFactorService(database)

    async def get_cpus(self, host_id: uuid.UUID) -> HostCpuProfile | None:
        """Return the latest CPU profile for a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            HostCpuProfile | None: Latest profile if any exist.
        """
        return await self._db.get_latest_cpu_profile(host_id)

    async def get_cpu_history(self, host_id: uuid.UUID) -> list[HostCpuProfile]:
        """Return all CPU profile snapshots for a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            list[HostCpuProfile]: Profiles newest first.
        """
        return await self._db.list_cpu_profiles(host_id)

    async def upsert_cpu(
        self,
        host_id: uuid.UUID,
        data: CpuProfileUpsert,
        *,
        source: CpuProfileSource = CpuProfileSource.MANUAL,
    ) -> HostCpuProfile:
        """Append a new CPU profile snapshot for a host.

        Args:
            host_id (uuid.UUID): Host primary key.
            data (CpuProfileUpsert): CPU inventory values.
            source (CpuProfileSource): How the data was collected.

        Returns:
            HostCpuProfile: Persisted profile row.
        """
        # Derive logical processors using CPU topology if not explicitly provided
        logical = data.logical_processor_count
        if logical is None:
            # Formula: sockets * cores/socket * threads/core
            logical = data.socket_count * data.cores_per_socket * data.threads_per_core

        # Resolve core factor multiplier from database match rules if not provided
        core_factor = data.core_factor
        matched_factor = None
        if core_factor is None:
            # Query the core factors lookup service using the reported CPU model string
            core_factor, matched_factor = await self._core_factors.resolve_for_cpu_model(
                data.cpu_model
            )

        # Persist the newly resolved CPU profile snapshot in the database
        return await self._db.create_cpu_profile(
            host_id,
            data,
            source=source,
            core_factor=core_factor,
            core_factor_id=matched_factor.id if matched_factor is not None else None,
            logical_processor_count=logical,
        )
