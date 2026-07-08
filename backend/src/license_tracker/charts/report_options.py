"""Build Apache ECharts option payloads for report charts."""

from __future__ import annotations

from license_tracker.models import LicenseTrackerReport

_COLOR_LICENSED = "#3B82F6"
_COLOR_COMPLIANT = "#10B981"
_COLOR_SHORTFALL = "#EF4444"


def build_compliance_chart_option(report: LicenseTrackerReport) -> dict | None:
    """Build an ECharts option for license compliance bars.

    Args:
        report (LicenseTrackerReport): Full report payload.

    Returns:
        dict | None: ECharts option object, or None when there is no data.
    """
    labels: list[str] = []
    licensed: list[int] = []
    in_use: list[dict[str, object]] = []

    for item in report.product_compliance:
        if item.cores_licensed > 0 or item.cores_in_use > 0:
            labels.append(f"{item.product_name} (Cores)")
            licensed.append(item.cores_licensed)
            in_use.append(
                {
                    "value": item.cores_in_use,
                    "itemStyle": {
                        "color": (
                            _COLOR_SHORTFALL
                            if item.cores_in_use > item.cores_licensed
                            else _COLOR_COMPLIANT
                        )
                    },
                }
            )

        if item.nups_licensed > 0 or (item.nups_in_use is not None and item.nups_in_use > 0):
            nups_in_use = item.nups_in_use or 0
            labels.append(f"{item.product_name} (NUPs)")
            licensed.append(item.nups_licensed)
            in_use.append(
                {
                    "value": nups_in_use,
                    "itemStyle": {
                        "color": (
                            _COLOR_SHORTFALL
                            if nups_in_use > item.nups_licensed
                            else _COLOR_COMPLIANT
                        )
                    },
                }
            )

    if not labels:
        return None

    labels = labels[::-1]
    licensed = licensed[::-1]
    in_use = in_use[::-1]

    return {
        "title": {
            "text": "Product License Compliance (Licensed vs In Use)",
            "left": "center",
            "textStyle": {"fontSize": 14, "color": "#333333", "fontWeight": "bold"},
        },
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "top": 28,
            "data": ["Licensed", "In Use (Compliant)", "In Use (Shortfall)"],
        },
        "grid": {"left": 130, "right": 48, "top": 72, "bottom": 32},
        "xAxis": {
            "type": "value",
            "splitLine": {"lineStyle": {"type": "dashed", "color": "#e0e0e0"}},
        },
        "yAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"fontSize": 10, "color": "#333333"},
        },
        "series": [
            {
                "name": "Licensed",
                "type": "bar",
                "data": licensed,
                "itemStyle": {"color": _COLOR_LICENSED},
                "label": {"show": True, "position": "right", "fontSize": 9, "color": "#333333"},
                "barGap": "20%",
            },
            {
                "name": "In Use",
                "type": "bar",
                "data": in_use,
                "label": {"show": True, "position": "right", "fontSize": 9, "color": "#333333"},
            },
            {
                "name": "In Use (Compliant)",
                "type": "bar",
                "data": [],
                "itemStyle": {"color": _COLOR_COMPLIANT},
            },
            {
                "name": "In Use (Shortfall)",
                "type": "bar",
                "data": [],
                "itemStyle": {"color": _COLOR_SHORTFALL},
            },
        ],
    }


def compliance_chart_size(label_count: int) -> tuple[int, int]:
    """Return PNG dimensions for the compliance chart.

    Args:
        label_count (int): Number of product rows in the chart.

    Returns:
        tuple[int, int]: Width and height in pixels.
    """
    return 780, max(350, label_count * 35 + 120)
