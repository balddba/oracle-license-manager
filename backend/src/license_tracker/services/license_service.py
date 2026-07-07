"""License agreement service."""

from __future__ import annotations

import uuid

from license_tracker.db.models.license_agreement import LicenseAgreement
from license_tracker.db.queries.base import Database
from license_tracker.models import LicenseCreate, LicenseUpdate


class LicenseService:
    """Data access and business logic for license agreements."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database

    async def get_licenses(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        renewal_within_days: int | None = None,
    ) -> list[LicenseAgreement]:
        """List license agreements with optional renewal window filter.

        Args:
            offset (int): Row offset for pagination.
            limit (int): Maximum rows to return.
            renewal_within_days (int | None): Only agreements renewing within N days.

        Returns:
            list[LicenseAgreement]: Matching license agreements.
        """
        return await self._db.list_licenses(
            offset=offset,
            limit=limit,
            renewal_within_days=renewal_within_days,
        )

    async def get_license(self, license_id: uuid.UUID) -> LicenseAgreement | None:
        """Fetch a license agreement by id.

        Args:
            license_id (uuid.UUID): Agreement primary key.

        Returns:
            LicenseAgreement | None: Agreement if found.
        """
        return await self._db.get_license(license_id)

    async def create_license(self, data: LicenseCreate) -> LicenseAgreement:
        """Create a new license agreement.

        Args:
            data (LicenseCreate): Creation payload.

        Returns:
            LicenseAgreement: Persisted agreement.
        """
        return await self._db.create_license(data)

    async def update_license(
        self,
        license_id: uuid.UUID,
        data: LicenseUpdate,
    ) -> LicenseAgreement | None:
        """Update an existing license agreement.

        Args:
            license_id (uuid.UUID): Agreement primary key.
            data (LicenseUpdate): Fields to update.

        Returns:
            LicenseAgreement | None: Updated agreement if found.
        """
        return await self._db.update_license(license_id, data)

    async def delete_license(self, license_id: uuid.UUID) -> bool:
        """Delete a license agreement and its entitlements.

        Args:
            license_id (uuid.UUID): Agreement primary key.

        Returns:
            bool: True if a row was deleted.
        """
        return await self._db.delete_license(license_id)
