"""Theme constants and asset helpers for executive PDF reports."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

_FONT = "Helvetica"

# Typography (points)
_TITLE_SIZE = 16
_SUBTITLE_SIZE = 8
_SECTION_SIZE = 11
_SECTION_SIZE_COMPACT = 10
_SECTION_DESC_SIZE = 7
_KPI_VALUE_SIZE = 12
_KPI_LABEL_SIZE = 7
_RENEWAL_VALUE_SIZE = 10
_BODY_SIZE = 8
_HEADER_SIZE = 8
_FOOTER_SIZE = 7

# Layout (millimeters)
_PAGE_BOTTOM_MARGIN = 18
_HEADER_HEIGHT = 14
_COVER_LOGO_HEIGHT = 14
_RUNNING_LOGO_HEIGHT = 12
_KPI_CARD_HEIGHT = 18
_KPI_CARD_GAP = 3
_RENEWAL_STRIP_HEIGHT = 9
_ACCENT_BAR_HEIGHT = 2

# Brand palette (RGB tuples)
_COLOR_PRIMARY = (30, 58, 95)  # #1E3A5F navy
_COLOR_ACCENT = (59, 130, 246)  # #3B82F6
_COLOR_SUCCESS = (16, 185, 129)  # #10B981
_COLOR_DANGER = (239, 68, 68)  # #EF4444
_COLOR_WARNING = (245, 158, 11)  # #F59E0B
_COLOR_CARD_FILL = (248, 250, 252)  # #F8FAFC
_COLOR_BORDER = (226, 232, 240)  # #E2E8F0
_COLOR_HEADER_FILL = (241, 245, 249)  # #F1F5F9
_COLOR_MUTED = (100, 116, 139)  # #64748B
_COLOR_ZEBRA = (248, 250, 252)
_COLOR_WHITE = (255, 255, 255)

REPORT_TITLE = "Oracle License Compliance Report"
REPORT_SUBTITLE = "Contracts, entitlements, host usage, and compliance"


def resolve_report_logo_path() -> Path | None:
    """Return the path to the bundled report logo PNG.

    Returns:
        Path | None: Absolute path to logo_report.png, or None if unavailable.
    """
    try:
        ref = importlib.resources.files("license_tracker.assets").joinpath("logo_report.png")
        with importlib.resources.as_file(ref) as path:
            if path.is_file():
                return path
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        pass
    return None
