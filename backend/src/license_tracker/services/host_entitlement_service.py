"""Host product assignment service."""

from __future__ import annotations

import uuid

from license_tracker.db.models.host_entitlement import HostEntitlement
from license_tracker.db.queries.base import Database
from license_tracker.domain.enums import HostLicenseType
from license_tracker.domain.license_type import (
    license_type_for_metric,
    metric_for_license_type,
)
from license_tracker.models import HostProductAssign, HostProductRead, PooledProductRead


def _normalize_option_name(option_name: str | None) -> str:
    """Normalize option name for storage and comparison.

    Args:
        option_name (str | None): Raw option name.

    Returns:
        str: Normalized option name.
    """
    return option_name or ""


class HostEntitlementService:
    """Data access for host-to-product assignments."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database

    async def list_for_host(self, host_id: uuid.UUID) -> list[HostEntitlement]:
        """List product licenses assigned to a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            list[HostEntitlement]: Assigned products ordered by product name.
        """
        return await self._db.list_host_entitlements(host_id)

    async def list_pooled_products(self) -> list[PooledProductRead]:
        """List distinct products available across all CSI agreements.

        Products are pooled by name and license type (CPU or NUP).

        Returns:
            list[PooledProductRead]: Pooled products ordered by name.
        """
        # Fetch all product entitlements active across database agreements
        entitlements = await self._db.list_all_products()

        # Track total quantities grouped by product, option, and host license type
        totals: dict[tuple[str, str, HostLicenseType], int] = {}
        for entitlement in entitlements:
            # Map metric type (PROCESSOR, NAMED_USER_PLUS, etc.) to host type
            license_type = license_type_for_metric(entitlement.metric)
            if license_type is None:
                continue

            # Form unique key, converting None option names to empty string
            key = (
                entitlement.product_name,
                _normalize_option_name(entitlement.option_name),
                license_type,
            )
            # Accumulate quantity count
            totals[key] = totals.get(key, 0) + entitlement.quantity

        # Map grouped totals to read models, sorted alphabetically by product, option, and type
        return [
            PooledProductRead(
                product_name=product_name,
                option_name=option_name or None,
                license_type=license_type,
                total_quantity=quantity,
            )
            for (product_name, option_name, license_type), quantity in sorted(
                totals.items(),
                key=lambda item: (item[0][0], item[0][1], item[0][2].value),
            )
        ]

    async def assign_product(
        self,
        host_id: uuid.UUID,
        data: HostProductAssign,
    ) -> HostEntitlement:
        """Associate a product license with a host.

        Uses the host license type so every product on the server is CPU or NUP.
        Assignments are allowed even when the product is not in the pooled
        inventory so compliance views can surface license shortfalls.

        Args:
            host_id (uuid.UUID): Host primary key.
            data (HostProductAssign): Assignment payload.

        Returns:
            HostEntitlement: Created assignment row.

        Raises:
            ValueError: If validation fails.
        """
        # Load host profile to determine its primary licensing model
        host = await self._db.get_host(host_id)
        if host is None:
            raise ValueError("Host not found")

        option_name = _normalize_option_name(data.option_name)
        # Determine the database metric required (e.g. processor vs user)
        metric = metric_for_license_type(host.license_type)

        # Confirm the product is not already assigned to avoid duplicates
        existing = await self._db.find_host_entitlement(
            host_id,
            data.product_name,
            option_name,
        )
        if existing is not None:
            raise ValueError("Product is already assigned to this host")

        # Create new host product entitlement assignment
        return await self._db.create_host_entitlement(
            host_id,
            data,
            metric=metric,
            option_name=option_name,
        )

    async def unassign_product(self, host_id: uuid.UUID, assignment_id: uuid.UUID) -> bool:
        """Remove a product assignment from a host.

        Args:
            host_id (uuid.UUID): Host primary key.
            assignment_id (uuid.UUID): Assignment primary key.

        Returns:
            bool: True if an assignment was removed.
        """
        return await self._db.delete_host_entitlement(host_id, assignment_id)

    async def realign_assignments_to_license_type(
        self,
        host_id: uuid.UUID,
        license_type: HostLicenseType,
    ) -> None:
        """Update assignment metrics to match a host license type.

        Assignments are retained even when the product is not in the pool for
        the new type so compliance views can surface license shortfalls.

        Args:
            host_id (uuid.UUID): Host primary key.
            license_type (HostLicenseType): Target CPU or NUP type.
        """
        # Get all existing product assignments for the target host
        assignments = await self.list_for_host(host_id)
        if not assignments:
            return

        # Convert license type target to matching metric type
        metric = metric_for_license_type(license_type)
        # Update metrics across all host assignments in a single query
        await self._db.update_host_entitlement_metrics(host_id, metric)

    @staticmethod
    def to_product_reads(
        rows: list[HostEntitlement],
        license_type: HostLicenseType,
    ) -> list[HostProductRead]:
        """Map assignment rows to API read models.

        Args:
            rows (list[HostEntitlement]): Assignment rows.
            license_type (HostLicenseType): Host license type applied to all products.

        Returns:
            list[HostProductRead]: API response payloads.
        """
        return [
            HostProductRead(
                id=row.id,
                host_id=row.host_id,
                product_name=row.product_name,
                option_name=row.option_name or None,
                license_type=license_type,
                metric=row.metric,
                notes=row.notes,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    @staticmethod
    def format_assignment_label(row: HostEntitlement) -> str:
        """Format an assignment for host list display.

        Args:
            row (HostEntitlement): Assignment row.

        Returns:
            str: Product label.
        """
        if row.option_name:
            return f"{row.product_name} — {row.option_name}"
        return row.product_name
