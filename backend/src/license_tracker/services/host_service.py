"""Host inventory service."""

from __future__ import annotations

import uuid

from license_tracker.db.models.host import Host
from license_tracker.db.queries.base import Database
from license_tracker.models import HostCreate, HostUpdate
from license_tracker.services.host_entitlement_service import HostEntitlementService


class HostService:
    """Data access for host inventory."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database
        self._entitlements = HostEntitlementService(database)

    async def get_hosts(self, *, offset: int = 0, limit: int = 50) -> list[Host]:
        """List hosts with pagination.

        Args:
            offset (int): Row offset.
            limit (int): Maximum rows.

        Returns:
            list[Host]: Host records.
        """
        return await self._db.list_hosts(offset=offset, limit=limit)

    async def get_host(self, host_id: uuid.UUID) -> Host | None:
        """Fetch a host by id.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            Host | None: Host if found.
        """
        return await self._db.get_host(host_id)

    async def create_host(self, data: HostCreate) -> Host:
        """Create a host record.

        Args:
            data (HostCreate): Creation payload.

        Returns:
            Host: Persisted host.
        """
        return await self._db.create_host(data)

    async def update_host(self, host_id: uuid.UUID, data: HostUpdate) -> Host | None:
        """Update a host record.

        When license_type changes, assignment metrics are realigned so every
        product on the server uses the same CPU or NUP type.

        Args:
            host_id (uuid.UUID): Host primary key.
            data (HostUpdate): Fields to update.

        Returns:
            Host | None: Updated host if found.
        """
        host = await self.get_host(host_id)
        if host is None:
            return None

        updates = data.model_dump(exclude_unset=True)
        new_license_type = updates.get("license_type")
        if new_license_type is not None and new_license_type != host.license_type:
            await self._entitlements.realign_assignments_to_license_type(host_id, new_license_type)

        return await self._db.update_host(host_id, data)

    async def delete_host(self, host_id: uuid.UUID) -> bool:
        """Delete a host and its CPU profiles.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            bool: True if a row was deleted.
        """
        return await self._db.delete_host(host_id)
