"""Processor core factor service."""

from __future__ import annotations

import uuid

from license_tracker.db.models.processor_core_factor import ProcessorCoreFactor
from license_tracker.db.queries.base import Database
from license_tracker.domain.license_calc import match_core_factor
from license_tracker.models import CoreFactorCreate, CoreFactorUpdate


class CoreFactorService:
    """Data access for processor core factor reference rows."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database

    async def get_core_factors(self) -> list[ProcessorCoreFactor]:
        """List all processor core factor rows.

        Returns:
            list[ProcessorCoreFactor]: Core factor rows ordered by priority.
        """
        return await self._db.list_core_factors()

    async def get_core_factor(self, factor_id: uuid.UUID) -> ProcessorCoreFactor | None:
        """Fetch a processor core factor by id.

        Args:
            factor_id (uuid.UUID): Core factor primary key.

        Returns:
            ProcessorCoreFactor | None: Row if found.
        """
        return await self._db.get_core_factor(factor_id)

    async def create_core_factor(self, data: CoreFactorCreate) -> ProcessorCoreFactor:
        """Create a processor core factor row.

        Args:
            data (CoreFactorCreate): Creation payload.

        Returns:
            ProcessorCoreFactor: Persisted row.
        """
        return await self._db.create_core_factor(data)

    async def update_core_factor(
        self,
        factor_id: uuid.UUID,
        data: CoreFactorUpdate,
    ) -> ProcessorCoreFactor | None:
        """Update a processor core factor row.

        Args:
            factor_id (uuid.UUID): Core factor primary key.
            data (CoreFactorUpdate): Fields to update.

        Returns:
            ProcessorCoreFactor | None: Updated row if found.
        """
        return await self._db.update_core_factor(factor_id, data)

    async def delete_core_factor(self, factor_id: uuid.UUID) -> bool:
        """Delete a processor core factor row.

        Args:
            factor_id (uuid.UUID): Core factor primary key.

        Returns:
            bool: True if a row was deleted.
        """
        return await self._db.delete_core_factor(factor_id)

    async def resolve_for_cpu_model(
        self,
        cpu_model: str | None,
    ) -> tuple[float | None, ProcessorCoreFactor | None]:
        """Resolve the core factor for a CPU model string.

        Args:
            cpu_model (str | None): Reported CPU model name.

        Returns:
            tuple[float | None, ProcessorCoreFactor | None]: Factor value and matched row.
        """
        factors = await self.get_core_factors()
        matched = match_core_factor(cpu_model, factors)
        if matched is None:
            return None, None
        return matched.core_factor, matched
