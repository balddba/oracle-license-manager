"""Serialize license tracker reports for download."""

from __future__ import annotations

import csv
import io

from license_tracker.models import LicenseTrackerReport


def report_to_csv(report: LicenseTrackerReport) -> str:
    """Serialize a full report to CSV with labeled sections.

    Args:
        report (LicenseTrackerReport): Report payload.

    Returns:
        str: UTF-8 CSV text with summary, agreements, hosts, and compliance sections.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["Section", "Generated at", report.generated_at.isoformat()])
    writer.writerow([])

    writer.writerow(["Summary"])
    summary = report.summary
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Agreements", summary.agreement_count])
    writer.writerow(["Products", summary.product_count])
    writer.writerow(["Hosts", summary.host_count])
    writer.writerow(["Physical cores", summary.total_physical_cores])
    writer.writerow(["Renewals (30 days)", summary.renewals_30_days])
    writer.writerow(["Renewals (60 days)", summary.renewals_60_days])
    writer.writerow(["Renewals (90 days)", summary.renewals_90_days])
    writer.writerow([])

    writer.writerow(["Agreements and entitlements"])
    writer.writerow(
        [
            "CSI",
            "Customer",
            "Status",
            "Renewal date",
            "Product",
            "Option",
            "Metric",
            "Quantity",
        ]
    )
    for agreement in report.agreements:
        if not agreement.products:
            writer.writerow(
                [
                    agreement.csi,
                    agreement.customer_name,
                    agreement.status.value,
                    agreement.renewal_date.isoformat() if agreement.renewal_date else "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
            continue
        for product in agreement.products:
            writer.writerow(
                [
                    agreement.csi,
                    agreement.customer_name,
                    agreement.status.value,
                    agreement.renewal_date.isoformat() if agreement.renewal_date else "",
                    product.product_name,
                    product.option_name or "",
                    product.metric.value,
                    product.quantity,
                ]
            )
    writer.writerow([])

    writer.writerow(["Host usage"])
    writer.writerow(
        [
            "Hostname",
            "Environment",
            "License type",
            "Assigned products",
            "CPU model",
            "Physical cores",
            "Core factor",
            "Processor licenses",
            "Named users required",
            "Licenses required",
        ]
    )
    for host in report.hosts:
        writer.writerow(
            [
                host.hostname,
                host.environment.value if host.environment is not None else "",
                host.license_type.value,
                "; ".join(host.assigned_products),
                host.cpu_model or "",
                host.physical_cores if host.physical_cores is not None else "",
                host.core_factor if host.core_factor is not None else "",
                host.processor_licenses_required
                if host.processor_licenses_required is not None
                else "",
                host.named_users_required if host.named_users_required is not None else "",
                host.licenses_required_label or "",
            ]
        )
    writer.writerow([])

    writer.writerow(["Product compliance"])
    writer.writerow(
        [
            "Product",
            "Cores licensed",
            "NUPs licensed",
            "Cores in use",
            "NUPs in use",
            "Balance",
        ]
    )
    for row in report.product_compliance:
        writer.writerow(
            [
                row.product_name,
                row.cores_licensed,
                row.nups_licensed,
                row.cores_in_use,
                row.nups_in_use if row.nups_in_use is not None else "",
                row.balance,
            ]
        )

    return buffer.getvalue()
