"""Render license tracker reports as PDF."""

from __future__ import annotations

import io

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
from fpdf.fonts import FontFace
from matplotlib.patches import Patch

matplotlib.use("Agg")

from license_tracker.domain.enums import HostEnvironment, LicenseMetric
from license_tracker.models import LicenseTrackerReport

_FONT = "Helvetica"
_BODY_SIZE = 7
_SECTION_SIZE = 10
_TITLE_SIZE = 14
_HEADER_SIZE = 7
_PAGE_BOTTOM_MARGIN = 15


# Map common Unicode characters to Latin-1/core font-safe equivalents
_REPLACEMENTS = {
    "\u2022": chr(149),  # bullet point
    "\u2013": "-",  # en-dash
    "\u2014": "-",  # em-dash
    "\u201c": '"',  # curly double quote left
    "\u201d": '"',  # curly double quote right
    "\u2018": "'",  # curly single quote left
    "\u2019": "'",  # curly single quote right
    "\u2122": "TM",  # trademark
}


def _safe_text(value: object) -> str:
    """Encode text for PDF core fonts.

    Args:
        value (object): Value to render.

    Returns:
        str: Latin-1-safe string for Helvetica output.
    """
    text = "" if value is None else str(value)
    for uni_char, replacement in _REPLACEMENTS.items():
        text = text.replace(uni_char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _format_environment(environment: HostEnvironment | None) -> str:
    """Return a display label for a host environment.

    Args:
        environment (HostEnvironment | None): Host environment enum.

    Returns:
        str: Human-readable environment label.
    """
    if environment == HostEnvironment.PRODUCTION:
        return "Production"
    if environment == HostEnvironment.NON_PRODUCTION:
        return "Non-production"
    return ""


def _format_metric(metric: LicenseMetric) -> str:
    """Return a display label for a license metric.

    Args:
        metric (LicenseMetric): License metric enum.

    Returns:
        str: Human-readable metric label.
    """
    if metric == LicenseMetric.NAMED_USER_PLUS:
        return "Named User Plus"
    if metric == LicenseMetric.NAMED_USER:
        return "Named User"
    if metric == LicenseMetric.CONCURRENT_USER:
        return "Concurrent User"
    if metric == LicenseMetric.APPLICATION_USER:
        return "Application User"
    if metric == LicenseMetric.OCPU:
        return "OCPU"
    return metric.value.title()


def _format_balance(balance: int) -> str:
    """Return a surplus or shortfall label for compliance rows.

    Args:
        balance (int): Licensed cores minus cores in use.

    Returns:
        str: Balance description.
    """
    if balance < 0:
        return f"Shortfall of {abs(balance)}"
    if balance > 0:
        return f"Surplus of {balance}"
    return "Balanced"


class _ReportPdf(FPDF):
    """PDF document with page numbers."""

    def footer(self) -> None:
        """Draw the centered page number footer."""
        self.set_y(-12)
        self.set_font(_FONT, "I", 7)
        self.cell(0, 10, _safe_text(f"Page {self.page_no()}/{{nb}}"), align="C")


def _draw_section_title(pdf: FPDF, title: str) -> None:
    """Draw a section heading with spacing.

    Args:
        pdf (FPDF): Active PDF document.
        title (str): Section title.
    """
    pdf.ln(3)
    pdf.set_font(_FONT, "B", _SECTION_SIZE)
    pdf.cell(0, 6, _safe_text(title), new_x="LMARGIN", new_y="NEXT")


def _draw_table(
    pdf: FPDF,
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[float],
    aligns: list[str] | None = None,
) -> None:
    """Draw a bordered table with repeated headers on page breaks.

    Args:
        pdf (FPDF): Active PDF document.
        headers (list[str]): Column headings.
        rows (list[list[str]]): Table body rows.
        col_widths (list[float]): Column widths in millimeters.
        aligns (list[str] | None): Optional horizontal alignments per column.
    """
    aligns_tuple = tuple(aligns) if aligns else ("LEFT",) * len(headers)

    with pdf.table(
        col_widths=tuple(col_widths),
        width=pdf.epw,
        text_align=aligns_tuple,
        line_height=pdf.font_size * 1.3,
    ) as table:
        header_row = table.row()
        header_style = FontFace(
            family=_FONT, emphasis="B", size_pt=_HEADER_SIZE, fill_color=(230, 230, 230)
        )
        for header in headers:
            header_row.cell(_safe_text(header), style=header_style)

        body_style = FontFace(family=_FONT, size_pt=_BODY_SIZE)
        for row in rows:
            data_row = table.row()
            for value in row:
                data_row.cell(_safe_text(value), style=body_style)


def _generate_compliance_chart(report: LicenseTrackerReport) -> io.BytesIO | None:
    """Generate a horizontal bar chart of product license compliance.

    Args:
        report (LicenseTrackerReport): The full license tracker report.

    Returns:
        io.BytesIO | None: Buffer containing PNG image bytes, or None if no compliance data.
    """
    labels = []
    licensed = []
    in_use = []
    colors_in_use = []

    for item in report.product_compliance:
        if item.cores_licensed > 0 or item.cores_in_use > 0:
            labels.append(f"{item.product_name} (Cores)")
            licensed.append(item.cores_licensed)
            in_use.append(item.cores_in_use)
            if item.cores_in_use > item.cores_licensed:
                colors_in_use.append("#EF4444")
            else:
                colors_in_use.append("#10B981")

        if item.nups_licensed > 0 or (item.nups_in_use is not None and item.nups_in_use > 0):
            labels.append(f"{item.product_name} (NUPs)")
            licensed.append(item.nups_licensed)
            in_use.append(item.nups_in_use or 0)
            if (item.nups_in_use or 0) > item.nups_licensed:
                colors_in_use.append("#EF4444")
            else:
                colors_in_use.append("#10B981")

    if not labels:
        return None

    # Reverse order so the first item appears at the top
    labels = labels[::-1]
    licensed = licensed[::-1]
    in_use = in_use[::-1]
    colors_in_use = colors_in_use[::-1]

    y = np.arange(len(labels))
    height = 0.35

    # Grouped horizontal bar chart
    fig, ax = plt.subplots(figsize=(6.5, 3.5), layout="constrained")
    rects1 = ax.barh(y + height / 2, licensed, height, label="Licensed", color="#3B82F6")
    rects2 = ax.barh(y - height / 2, in_use, height, label="In Use", color=colors_in_use)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title(
        "Product License Compliance (Licensed vs In Use)", fontsize=10, fontweight="bold", pad=10
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")
    ax.xaxis.grid(True, linestyle="--", alpha=0.6, color="#e0e0e0")
    ax.set_axisbelow(True)

    legend_elements = [
        Patch(facecolor="#3B82F6", label="Licensed"),
        Patch(facecolor="#10B981", label="In Use (Compliant)"),
        Patch(facecolor="#EF4444", label="In Use (Shortfall)"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=8, framealpha=0.9)

    for rect in rects1:
        width = rect.get_width()
        ax.annotate(
            f"{width}",
            xy=(width, rect.get_y() + rect.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=7,
            color="#333333",
        )

    for rect in rects2:
        width = rect.get_width()
        ax.annotate(
            f"{width}",
            xy=(width, rect.get_y() + rect.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=7,
            color="#333333",
        )

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


def _generate_host_env_chart(report: LicenseTrackerReport) -> io.BytesIO | None:
    """Generate a donut chart of host environment distribution.

    Args:
        report (LicenseTrackerReport): The full license tracker report.

    Returns:
        io.BytesIO | None: Buffer containing PNG image bytes, or None if no hosts data.
    """
    prod_count = 0
    non_prod_count = 0
    for host in report.hosts:
        if host.environment == HostEnvironment.PRODUCTION:
            prod_count += 1
        elif host.environment == HostEnvironment.NON_PRODUCTION:
            non_prod_count += 1

    if prod_count == 0 and non_prod_count == 0:
        return None

    labels = []
    sizes = []
    colors = []

    if prod_count > 0:
        labels.append(f"Production ({prod_count})")
        sizes.append(prod_count)
        colors.append("#1E3A8A")
    if non_prod_count > 0:
        labels.append(f"Non-production ({non_prod_count})")
        sizes.append(non_prod_count)
        colors.append("#0D9488")

    fig, ax = plt.subplots(figsize=(4.5, 3.5), layout="constrained")
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        textprops=dict(color="#333333", fontsize=8),
        wedgeprops=dict(width=0.4, edgecolor="w"),
    )

    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_weight("bold")
        autotext.set_color("white")

    ax.set_title("Host Environment Distribution", fontsize=10, fontweight="bold", pad=10)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


def _draw_visual_insights(pdf: FPDF, report: LicenseTrackerReport) -> None:
    """Draw the visual insights section with charts in the PDF.

    Args:
        pdf (FPDF): Active PDF document.
        report (LicenseTrackerReport): The full license tracker report.
    """
    comp_buf = _generate_compliance_chart(report)
    env_buf = _generate_host_env_chart(report)

    if not comp_buf and not env_buf:
        return

    pdf.add_page()
    _draw_section_title(pdf, "Visual insights")

    y_start = pdf.get_y() + 5

    if comp_buf and env_buf:
        pdf.image(comp_buf, x=10, y=y_start, w=135)
        pdf.image(env_buf, x=150, y=y_start, w=135)
        pdf.set_y(y_start + 85)
    elif comp_buf:
        pdf.image(comp_buf, x=78, y=y_start, w=140)
        pdf.set_y(y_start + 85)
    elif env_buf:
        pdf.image(env_buf, x=78, y=y_start, w=140)
        pdf.set_y(y_start + 115)


def report_to_pdf(report: LicenseTrackerReport) -> bytes:
    """Serialize a full report to a PDF document.

    Args:
        report (LicenseTrackerReport): Report payload.

    Returns:
        bytes: PDF file bytes.
    """
    pdf = _ReportPdf(orientation="landscape")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=_PAGE_BOTTOM_MARGIN)
    pdf.add_page()

    pdf.set_font(_FONT, "B", _TITLE_SIZE)
    pdf.cell(0, 8, "Oracle License Tracker Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(_FONT, "", _BODY_SIZE)
    pdf.cell(
        0,
        5,
        _safe_text(f"Generated {report.generated_at.strftime('%Y-%m-%d %H:%M:%S %Z')}"),
        new_x="LMARGIN",
        new_y="NEXT",
    )

    summary = report.summary
    _draw_section_title(pdf, "Summary")
    _draw_table(
        pdf,
        ["Metric", "Value"],
        [
            ["Agreements", str(summary.agreement_count)],
            ["Products", str(summary.product_count)],
            ["Hosts", str(summary.host_count)],
            ["Physical cores", str(summary.total_physical_cores)],
            ["Renewals (30 days)", str(summary.renewals_30_days)],
            ["Renewals (60 days)", str(summary.renewals_60_days)],
            ["Renewals (90 days)", str(summary.renewals_90_days)],
        ],
        [180.0, 97.0],
        aligns=["LEFT", "LEFT"],
    )

    _draw_visual_insights(pdf, report)

    _draw_section_title(pdf, "Contracts and entitlements")
    agreement_rows = []
    for agreement in report.agreements:
        csi = agreement.csi
        customer = agreement.customer_name
        status = agreement.status.value
        renewal = agreement.renewal_date.isoformat() if agreement.renewal_date else ""

        if not agreement.products:
            agreement_rows.append([csi, customer, status, renewal, "No products", "", ""])
            continue

        for i, product in enumerate(agreement.products):
            prod_name = product.product_name
            if product.option_name:
                prod_name = f"{prod_name} ({product.option_name})"

            if i == 0:
                agreement_rows.append(
                    [
                        csi,
                        customer,
                        status,
                        renewal,
                        prod_name,
                        _format_metric(product.metric),
                        str(product.quantity),
                    ]
                )
            else:
                agreement_rows.append(
                    [
                        "",
                        "",
                        "",
                        "",
                        prod_name,
                        _format_metric(product.metric),
                        str(product.quantity),
                    ]
                )

    if not agreement_rows:
        pdf.set_font(_FONT, "", _BODY_SIZE)
        pdf.cell(0, 5, "No license agreements recorded.", new_x="LMARGIN", new_y="NEXT")
    else:
        _draw_table(
            pdf,
            ["CSI", "Customer", "Status", "Renewal", "Product", "License type", "License count"],
            agreement_rows,
            [25.0, 45.0, 18.0, 25.0, 100.0, 40.0, 24.0],
            aligns=["LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "RIGHT"],
        )

    _draw_section_title(pdf, "Host usage")
    host_rows = []
    for host in report.hosts:
        hostname = host.hostname
        env = _format_environment(host.environment)
        lic_type = host.license_type.value.upper()
        cores = str(host.physical_cores) if host.physical_cores is not None else ""
        lic_req = host.licenses_required_label or ""

        if not host.assigned_products:
            host_rows.append([hostname, env, lic_type, "None", cores, lic_req])
        else:
            for i, product in enumerate(host.assigned_products):
                if i == 0:
                    host_rows.append([hostname, env, lic_type, product, cores, lic_req])
                else:
                    host_rows.append(["", "", "", product, "", lic_req])

    if not host_rows:
        pdf.set_font(_FONT, "", _BODY_SIZE)
        pdf.cell(0, 5, "No hosts in inventory.", new_x="LMARGIN", new_y="NEXT")
    else:
        _draw_table(
            pdf,
            [
                "Hostname",
                "Environment",
                "Type",
                "Product",
                "Physical cores",
                "Licenses required",
            ],
            host_rows,
            [55.0, 28.0, 12.0, 80.0, 72.0, 30.0],
            aligns=["LEFT", "LEFT", "LEFT", "LEFT", "RIGHT", "LEFT"],
        )

    _draw_section_title(pdf, "Product compliance")
    compliance_rows = [
        [
            row.product_name,
            str(row.cores_licensed),
            str(row.nups_licensed),
            str(row.cores_in_use),
            str(row.nups_in_use) if row.nups_in_use is not None else "",
            _format_balance(row.balance),
        ]
        for row in report.product_compliance
    ]
    if not compliance_rows:
        pdf.set_font(_FONT, "", _BODY_SIZE)
        pdf.cell(
            0,
            5,
            "No product compliance rows match the current filter.",
            new_x="LMARGIN",
            new_y="NEXT",
        )
    else:
        _draw_table(
            pdf,
            [
                "Product",
                "Cores licensed",
                "NUPs licensed",
                "Cores in use",
                "NUPs in use",
                "Surplus / shortfall",
            ],
            compliance_rows,
            [117.0, 30.0, 30.0, 30.0, 30.0, 40.0],
            aligns=["LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
        )

    return bytes(pdf.output())
