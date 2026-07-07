"""Full license tracker report models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from license_tracker.models.dashboard_summary import DashboardSummary
from license_tracker.models.host_list_read import HostListRead
from license_tracker.models.license_detail_read import LicenseDetailRead
from license_tracker.models.product_license_summary import ProductLicenseSummary


class LicenseTrackerReport(BaseModel):
    """Comprehensive report of contracts, licenses, and usage."""

    generated_at: datetime
    summary: DashboardSummary
    agreements: list[LicenseDetailRead] = Field(default_factory=list)
    hosts: list[HostListRead] = Field(default_factory=list)
    product_compliance: list[ProductLicenseSummary] = Field(default_factory=list)
