"""Unit tests for Apache ECharts PNG rendering."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from license_tracker.charts.report_options import (
    build_compliance_chart_option,
    compliance_chart_size,
)
from license_tracker.models import (
    DashboardSummary,
    LicenseTrackerReport,
    ProductLicenseSummary,
)
from license_tracker.services.echarts_render import EChartsRenderError, render_echarts_option
from license_tracker.services.report_charts import generate_compliance_chart


def _renderer_ready() -> bool:
    """Return whether the Node ECharts renderer is available.

    Returns:
        bool: True when node and renderer dependencies are installed.
    """
    renderer_dir = Path(__file__).resolve().parents[1] / "scripts" / "echarts-renderer"
    return shutil.which("node") is not None and (renderer_dir / "node_modules").is_dir()


@pytest.mark.skipif(not _renderer_ready(), reason="Node ECharts renderer is not installed")
def test_render_echarts_option_returns_png() -> None:
    """Renderer returns PNG bytes for a valid option payload."""
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
                nups_licensed=0,
                cores_in_use=8,
                nups_in_use=0,
                balance=2,
            )
        ],
    )
    option = build_compliance_chart_option(report)
    assert option is not None
    width, height = compliance_chart_size(len(option["yAxis"]["data"]))

    png_bytes = render_echarts_option(option, width=width, height=height)

    assert png_bytes.startswith(b"\x89PNG")


@pytest.mark.skipif(not _renderer_ready(), reason="Node ECharts renderer is not installed")
def test_generate_compliance_chart_returns_png() -> None:
    """Compliance chart helper returns a PNG buffer when data exists."""
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
                nups_licensed=0,
                cores_in_use=8,
                nups_in_use=0,
                balance=2,
            )
        ],
    )

    buffer = generate_compliance_chart(report)

    assert buffer is not None
    assert buffer.read(8).startswith(b"\x89PNG")


def test_generate_charts_return_none_without_data() -> None:
    """Chart helpers return None when there is nothing to plot."""
    empty_report = LicenseTrackerReport(
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
        summary=DashboardSummary(
            agreement_count=0,
            product_count=0,
            host_count=0,
            total_physical_cores=0,
            renewals_30_days=0,
            renewals_60_days=0,
            renewals_90_days=0,
        ),
        agreements=[],
        hosts=[],
        product_compliance=[],
    )

    assert generate_compliance_chart(empty_report) is None


def test_render_echarts_option_requires_node(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing Node raises a clear render error."""

    def raise_not_found(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError()

    monkeypatch.setattr("license_tracker.services.echarts_render.subprocess.run", raise_not_found)

    with pytest.raises(EChartsRenderError, match="Node.js is required"):
        render_echarts_option({"series": []}, width=100, height=100)
