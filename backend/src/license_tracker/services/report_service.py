"""Full license tracker reporting."""

from __future__ import annotations

from datetime import UTC, datetime

from license_tracker.db.queries.base import Database
from license_tracker.models import (
    HostListRead,
    LicenseDetailRead,
    LicenseRead,
    LicenseTrackerReport,
    ProductRead,
)
from license_tracker.services.compliance_service import ComplianceService
from license_tracker.services.cpu_service import CpuService
from license_tracker.services.dashboard_service import DashboardService
from license_tracker.services.host_entitlement_service import HostEntitlementService
from license_tracker.services.host_list_builder import build_host_list_read
from license_tracker.services.host_service import HostService
from license_tracker.services.license_service import LicenseService


class ReportService:
    """Compose contracts, license inventory, and host usage into one report."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database
        self._license_service = LicenseService(database)
        self._host_service = HostService(database)
        self._cpu_service = CpuService(database)
        self._entitlement_service = HostEntitlementService(database)
        self._dashboard_service = DashboardService(database)
        self._compliance_service = ComplianceService(database)

    async def get_full_report(
        self,
        *,
        shortfalls_only: bool = False,
    ) -> LicenseTrackerReport:
        """Build a report covering all agreements, entitlements, hosts, and compliance.

        Args:
            shortfalls_only (bool): When True, product_compliance lists only
                under-licensed products.

        Returns:
            LicenseTrackerReport: Full organization report.
        """
        summary = await self._dashboard_service.get_dashboard_summary()
        agreements = await self._load_all_agreements()
        hosts = await self._load_all_hosts()
        product_compliance = summary.license_inventory
        if shortfalls_only:
            product_compliance = [row for row in product_compliance if row.balance < 0]

        return LicenseTrackerReport(
            generated_at=datetime.now(UTC),
            summary=summary,
            agreements=agreements,
            hosts=hosts,
            product_compliance=product_compliance,
        )

    async def _load_all_agreements(self) -> list[LicenseDetailRead]:
        """Load every license agreement with nested entitlements.

        Returns:
            list[LicenseDetailRead]: All agreements ordered as returned by the database.
        """
        agreement_count = await self._db.count_licenses()
        if agreement_count == 0:
            return []
        rows = await self._license_service.get_licenses(offset=0, limit=agreement_count)
        return [
            LicenseDetailRead(
                **LicenseRead.model_validate(row).model_dump(),
                products=[ProductRead.model_validate(product) for product in row.products],
            )
            for row in rows
        ]

    async def _load_all_hosts(self) -> list[HostListRead]:
        """Load every host with usage and license requirement details.

        Returns:
            list[HostListRead]: Enriched host rows.
        """
        host_count = await self._db.count_hosts()
        if host_count == 0:
            return []
        hosts = await self._host_service.get_hosts(offset=0, limit=host_count)
        return [
            await build_host_list_read(
                host,
                cpu_service=self._cpu_service,
                entitlement_service=self._entitlement_service,
            )
            for host in hosts
        ]
