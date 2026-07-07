"""API v1 reporting routes."""

from __future__ import annotations

from enum import StrEnum

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse, Response

from license_tracker.api.deps import ReportServiceDep
from license_tracker.models import LicenseTrackerReport
from license_tracker.services.report_export import report_to_csv
from license_tracker.services.report_pdf import report_to_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportFormat(StrEnum):
    """Supported report output formats."""

    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


@router.get("/full", response_model=None)
async def get_full_report(
    service: ReportServiceDep,
    format: ReportFormat = Query(ReportFormat.JSON, description="Output format"),
    shortfalls_only: bool = Query(
        False,
        description="When true, product compliance lists only under-licensed products",
    ),
) -> LicenseTrackerReport | PlainTextResponse | Response:
    """Return a full report of contracts, licenses, and usage.

    Args:
        service (ReportService): Report service.
        format (ReportFormat): JSON body, CSV download, or PDF download.
        shortfalls_only (bool): Filter product compliance to shortfalls only.

    Returns:
        LicenseTrackerReport | PlainTextResponse | Response: Report payload or file download.
    """
    report = await service.get_full_report(shortfalls_only=shortfalls_only)
    timestamp = report.generated_at.strftime("%Y%m%d-%H%M%S")
    if format == ReportFormat.CSV:
        csv_text = report_to_csv(report)
        filename = f"license-tracker-report-{timestamp}.csv"
        return PlainTextResponse(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    if format == ReportFormat.PDF:
        filename = f"license-tracker-report-{timestamp}.pdf"
        return Response(
            content=report_to_pdf(report),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return report
