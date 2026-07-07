"""Dashboard aggregate queries."""

from __future__ import annotations

from license_tracker.db.queries.base import Database
from license_tracker.models import DashboardSummary
from license_tracker.services.compliance_service import ComplianceService


class DashboardService:
    """Aggregate metrics for the dashboard."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database
        self._compliance_service = ComplianceService(database)

    async def get_dashboard_summary(self) -> DashboardSummary:
        """Compute dashboard summary counts.

        Returns:
            DashboardSummary: Aggregate metrics.
        """
        agreement_count = await self._db.count_licenses()
        product_count = await self._db.count_products()
        host_count = await self._db.count_hosts()
        total_cores = await self._db.total_physical_cores()
        renewals_30 = await self._db.count_renewals_within(30)
        renewals_60 = await self._db.count_renewals_within(60)
        renewals_90 = await self._db.count_renewals_within(90)
        license_inventory = await self._compliance_service.list_license_inventory()
        return DashboardSummary(
            agreement_count=agreement_count,
            product_count=product_count,
            host_count=host_count,
            total_physical_cores=total_cores,
            renewals_30_days=renewals_30,
            renewals_60_days=renewals_60,
            renewals_90_days=renewals_90,
            license_inventory=license_inventory,
        )
