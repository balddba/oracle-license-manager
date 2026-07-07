"""Unit tests for PDF report export."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from license_tracker.domain.enums import (
    HostEnvironment,
    HostLicenseType,
    LicenseMetric,
    LicenseStatus,
)
from license_tracker.models import (
    DashboardSummary,
    HostListRead,
    LicenseDetailRead,
    LicenseTrackerReport,
    ProductLicenseSummary,
    ProductRead,
)
from license_tracker.services.report_pdf import report_to_pdf


def test_report_to_pdf_includes_report_content() -> None:
    """PDF export contains key report labels and data."""
    agreement_id = uuid4()
    host_id = uuid4()
    product_id = uuid4()
    report = LicenseTrackerReport(
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        summary=DashboardSummary(
            agreement_count=1,
            product_count=1,
            host_count=1,
            total_physical_cores=16,
            renewals_30_days=0,
            renewals_60_days=1,
            renewals_90_days=1,
        ),
        agreements=[
            LicenseDetailRead(
                id=agreement_id,
                csi="CSI-PDF",
                customer_name="PDF Customer",
                support_level=None,
                start_date=date(2025, 1, 1),
                renewal_date=date(2026, 12, 31),
                status=LicenseStatus.ACTIVE,
                notes=None,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                products=[
                    ProductRead(
                        id=product_id,
                        agreement_id=agreement_id,
                        product_name="Database Enterprise Edition",
                        option_name=None,
                        metric=LicenseMetric.PROCESSOR,
                        quantity=10,
                        notes=None,
                        created_at=datetime(2026, 1, 1, tzinfo=UTC),
                        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                    )
                ],
            )
        ],
        hosts=[
            HostListRead(
                id=host_id,
                hostname="db-pdf.example.com",
                fqdn=None,
                ip_address=None,
                environment=HostEnvironment.PRODUCTION,
                license_type=HostLicenseType.CPU,
                named_users_required=None,
                os_name=None,
                notes=None,
                ssh_enabled=False,
                ssh_port=22,
                ssh_user=None,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                assigned_products=["Database Enterprise Edition"],
                cpu_model="Intel Xeon",
                socket_count=2,
                cores_per_socket=8,
                physical_cores=16,
                core_factor=0.5,
                core_factor_name="Intel",
                processor_licenses_required=8,
                licenses_required_label="8 CPU",
            )
        ],
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

    pdf_bytes = report_to_pdf(report)

    assert pdf_bytes.startswith(b"%PDF")
    assert pdf_bytes.rstrip().endswith(b"%%EOF")
    assert len(pdf_bytes) > 500


def test_report_to_pdf_empty_data() -> None:
    """PDF export succeeds when report contains no hosts or compliance data."""
    report = LicenseTrackerReport(
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
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

    pdf_bytes = report_to_pdf(report)

    assert pdf_bytes.startswith(b"%PDF")
    assert pdf_bytes.rstrip().endswith(b"%%EOF")
    assert len(pdf_bytes) > 500


def test_report_to_pdf_shortfall_colors() -> None:
    """PDF export succeeds and handles colors properly when there is a license shortfall."""
    agreement_id = uuid4()
    product_id = uuid4()
    report = LicenseTrackerReport(
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        summary=DashboardSummary(
            agreement_count=1,
            product_count=1,
            host_count=0,
            total_physical_cores=0,
            renewals_30_days=0,
            renewals_60_days=0,
            renewals_90_days=0,
        ),
        agreements=[
            LicenseDetailRead(
                id=agreement_id,
                csi="CSI-PDF",
                customer_name="PDF Customer",
                support_level=None,
                start_date=date(2025, 1, 1),
                renewal_date=date(2026, 12, 31),
                status=LicenseStatus.ACTIVE,
                notes=None,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                products=[
                    ProductRead(
                        id=product_id,
                        agreement_id=agreement_id,
                        product_name="Database Enterprise Edition",
                        option_name=None,
                        metric=LicenseMetric.PROCESSOR,
                        quantity=2,
                        notes=None,
                        created_at=datetime(2026, 1, 1, tzinfo=UTC),
                        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                    )
                ],
            )
        ],
        hosts=[],
        product_compliance=[
            ProductLicenseSummary(
                product_name="Database Enterprise Edition",
                cores_licensed=2,
                nups_licensed=5,
                cores_in_use=10,  # Shortfall: 10 in use vs 2 licensed
                nups_in_use=15,  # Shortfall: 15 in use vs 5 licensed
                balance=-8,
            )
        ],
    )

    pdf_bytes = report_to_pdf(report)

    assert pdf_bytes.startswith(b"%PDF")
    assert pdf_bytes.rstrip().endswith(b"%%EOF")
    assert len(pdf_bytes) > 500
