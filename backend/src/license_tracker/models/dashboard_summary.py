"""Dashboard summary model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from license_tracker.models.product_license_summary import ProductLicenseSummary


class DashboardSummary(BaseModel):
    """Dashboard aggregate counts."""

    agreement_count: int
    product_count: int
    host_count: int
    total_physical_cores: int
    renewals_30_days: int
    renewals_60_days: int
    renewals_90_days: int
    license_inventory: list[ProductLicenseSummary] = Field(default_factory=list)
