"""Unit tests for Apache ECharts report option builders."""

from __future__ import annotations

from datetime import UTC, datetime

from license_tracker.charts.report_options import build_compliance_chart_option
from license_tracker.models import (
    DashboardSummary,
    LicenseTrackerReport,
    ProductLicenseSummary,
)


def test_build_compliance_chart_option_includes_series() -> None:
    """Compliance option includes licensed and in-use bar series."""
    report = LicenseTrackerReport(
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
        summary=DashboardSummary(
            agreement_count=0,
            product_count=1,
            host_count=0,
            total_physical_cores=0,
            renewals_30_days=0,
            renewals_60_days=0,
            renewals_90_days=0,
        ),
        agreements=[],
        hosts=[],
        product_compliance=[
            ProductLicenseSummary(
                product_name="Database Enterprise Edition",
                cores_licensed=10,
                nups_licensed=5,
                cores_in_use=12,
                nups_in_use=3,
                balance=-2,
            )
        ],
    )

    option = build_compliance_chart_option(report)

    assert option is not None
    assert len(option["yAxis"]["data"]) == 2
    assert option["series"][0]["data"] == [5, 10]
    assert option["series"][1]["data"][0]["value"] == 3
    assert option["series"][1]["data"][1]["value"] == 12
