"""Generate Apache ECharts chart images for PDF report exports."""

from __future__ import annotations

import io

from license_tracker.charts.report_options import (
    build_compliance_chart_option,
    compliance_chart_size,
)
from license_tracker.models import LicenseTrackerReport
from license_tracker.services.echarts_render import render_echarts_option


def _render_option(option: dict, *, width: int, height: int) -> io.BytesIO:
    """Render an ECharts option to a seekable PNG buffer.

    Args:
        option (dict): ECharts option payload.
        width (int): Image width in pixels.
        height (int): Image height in pixels.

    Returns:
        io.BytesIO: PNG image bytes positioned at the start of the buffer.
    """
    png_bytes = render_echarts_option(option, width=width, height=height)
    buffer = io.BytesIO(png_bytes)
    buffer.seek(0)
    return buffer


def generate_compliance_chart(report: LicenseTrackerReport) -> io.BytesIO | None:
    """Generate a horizontal bar chart of product license compliance.

    Args:
        report (LicenseTrackerReport): The full license tracker report.

    Returns:
        io.BytesIO | None: Buffer containing PNG image bytes, or None if no compliance data.
    """
    option = build_compliance_chart_option(report)
    if option is None:
        return None

    label_count = len(option["yAxis"]["data"])
    width, height = compliance_chart_size(label_count)
    return _render_option(option, width=width, height=height)
