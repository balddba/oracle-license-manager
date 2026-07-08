"""Render license tracker reports as PDF."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from fpdf import FPDF
from fpdf.fonts import FontFace
from PIL import Image

from license_tracker.domain.enums import HostEnvironment, LicenseMetric
from license_tracker.models import LicenseTrackerReport
from license_tracker.services.report_charts import generate_compliance_chart
from license_tracker.services.report_pdf_theme import (
    _ACCENT_BAR_HEIGHT,
    _BODY_SIZE,
    _COLOR_BORDER,
    _COLOR_CARD_FILL,
    _COLOR_DANGER,
    _COLOR_HEADER_FILL,
    _COLOR_MUTED,
    _COLOR_PRIMARY,
    _COLOR_SUCCESS,
    _COLOR_WARNING,
    _COLOR_WHITE,
    _COLOR_ZEBRA,
    _COVER_LOGO_HEIGHT,
    _FONT,
    _FOOTER_SIZE,
    _HEADER_SIZE,
    _KPI_CARD_GAP,
    _KPI_CARD_HEIGHT,
    _KPI_LABEL_SIZE,
    _KPI_VALUE_SIZE,
    _PAGE_BOTTOM_MARGIN,
    _RENEWAL_STRIP_HEIGHT,
    _RENEWAL_VALUE_SIZE,
    _RUNNING_LOGO_HEIGHT,
    _SECTION_DESC_SIZE,
    _SECTION_SIZE,
    _SECTION_SIZE_COMPACT,
    _SUBTITLE_SIZE,
    _TITLE_SIZE,
    REPORT_SUBTITLE,
    REPORT_TITLE,
    resolve_report_logo_path,
)

CellStyleFn = Callable[[int, int, str], FontFace | None]

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


def _balance_text_color(value: str) -> tuple[int, int, int]:
    """Return text color for a compliance balance label.

    Args:
        value (str): Formatted balance label.

    Returns:
        tuple[int, int, int]: RGB color tuple.
    """
    if value.startswith("Shortfall"):
        return _COLOR_DANGER
    if value.startswith("Surplus"):
        return _COLOR_WARNING
    return _COLOR_SUCCESS


def _status_text_color(status: str) -> tuple[int, int, int]:
    """Return text color for an agreement status label.

    Args:
        status (str): Agreement status value.

    Returns:
        tuple[int, int, int]: RGB color tuple.
    """
    if status.lower() == "active":
        return _COLOR_SUCCESS
    return _COLOR_MUTED


class _ReportPdf(FPDF):
    """PDF document with branded header, footer, and page numbers."""

    def __init__(self, *, generated_at: datetime) -> None:
        """Initialize the report PDF document.

        Args:
            generated_at (datetime): Report generation timestamp for footers.
        """
        super().__init__(orientation="landscape")
        self.generated_at = generated_at
        self.show_running_header = False
        self._logo_path = resolve_report_logo_path()

    def add_page(self, *args: object, **kwargs: object) -> None:
        """Add a page and enable the running header after the cover page.

        Args:
            *args (object): Positional arguments forwarded to FPDF.add_page.
            **kwargs (object): Keyword arguments forwarded to FPDF.add_page.
        """
        if self.page_no() >= 1:
            self.show_running_header = True
            self.set_top_margin(_ACCENT_BAR_HEIGHT + _RUNNING_LOGO_HEIGHT + 8)
        super().add_page(*args, **kwargs)

    def header(self) -> None:
        """Draw the branded running header on non-cover pages."""
        if not self.show_running_header:
            return

        self.set_fill_color(*_COLOR_PRIMARY)
        self.rect(0, 0, self.w, _ACCENT_BAR_HEIGHT, style="F")

        header_y = _ACCENT_BAR_HEIGHT + 2
        if self._logo_path is not None:
            self.image(str(self._logo_path), x=self.l_margin, y=header_y, h=_RUNNING_LOGO_HEIGHT)

        self.set_font(_FONT, "", _BODY_SIZE)
        self.set_text_color(*_COLOR_MUTED)
        title_x = self.w - self.r_margin - 90
        self.set_xy(title_x, header_y + 2)
        self.cell(90, 5, _safe_text(REPORT_TITLE), align="R")

        rule_y = header_y + _RUNNING_LOGO_HEIGHT + 2
        self.set_draw_color(*_COLOR_BORDER)
        self.set_line_width(0.2)
        self.line(self.l_margin, rule_y, self.w - self.r_margin, rule_y)
        self.set_y(rule_y + 2)

    def footer(self) -> None:
        """Draw the branded footer with timestamp, page numbers, and label."""
        self.set_y(-14)
        self.set_draw_color(*_COLOR_BORDER)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

        footer_y = self.get_y()
        third = self.epw / 3

        self.set_font(_FONT, "", _FOOTER_SIZE)
        self.set_text_color(*_COLOR_MUTED)
        self.set_xy(self.l_margin, footer_y)
        timestamp = self.generated_at.strftime("%Y-%m-%d %H:%M:%S %Z")
        self.cell(third, 5, _safe_text(timestamp), align="L")

        self.set_xy(self.l_margin + third, footer_y)
        self.cell(third, 5, _safe_text(f"Page {self.page_no()} of {{nb}}"), align="C")

        self.set_xy(self.l_margin + 2 * third, footer_y)
        self.cell(third, 5, "Confidential", align="R")


def _draw_section_title(
    pdf: FPDF,
    title: str,
    *,
    description: str | None = None,
    compact: bool = False,
) -> None:
    """Draw a section heading with optional description.

    Args:
        pdf (FPDF): Active PDF document.
        title (str): Section title.
        description (str | None): Optional muted description below the title.
        compact (bool): Use tighter spacing for the first-page summary layout.
    """
    if compact:
        pdf.ln(2)
        title_size = _SECTION_SIZE_COMPACT
        title_height = 5
        desc_height = 4
    else:
        pdf.ln(4)
        title_size = _SECTION_SIZE
        title_height = 7
        desc_height = 5

    pdf.set_font(_FONT, "B", title_size)
    pdf.set_text_color(*_COLOR_PRIMARY)
    pdf.cell(0, title_height, _safe_text(title), new_x="LMARGIN", new_y="NEXT")
    if description:
        pdf.set_font(_FONT, "", _SECTION_DESC_SIZE)
        pdf.set_text_color(*_COLOR_MUTED)
        pdf.cell(0, desc_height, _safe_text(description), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)


def _draw_cover(pdf: _ReportPdf) -> None:
    """Draw the executive cover block with logo, title, and accent bar.

    Args:
        pdf (_ReportPdf): Active PDF document.
    """
    if pdf._logo_path is not None:
        pdf.image(str(pdf._logo_path), x=pdf.l_margin, y=pdf.get_y(), h=_COVER_LOGO_HEIGHT)
        pdf.ln(_COVER_LOGO_HEIGHT + 3)
    else:
        pdf.ln(2)

    pdf.set_font(_FONT, "B", _TITLE_SIZE)
    pdf.set_text_color(*_COLOR_PRIMARY)
    pdf.cell(0, 7, _safe_text(REPORT_TITLE), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(_FONT, "", _SUBTITLE_SIZE)
    pdf.set_text_color(*_COLOR_MUTED)
    pdf.cell(0, 4, _safe_text(REPORT_SUBTITLE), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(_FONT, "", _BODY_SIZE)
    generated = pdf.generated_at.strftime("%Y-%m-%d %H:%M:%S %Z")
    pdf.cell(0, 4, _safe_text(f"Generated {generated}"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_fill_color(*_COLOR_PRIMARY)
    pdf.rect(pdf.l_margin, pdf.get_y(), pdf.epw, _ACCENT_BAR_HEIGHT, style="F")
    pdf.ln(_ACCENT_BAR_HEIGHT + 3)
    pdf.set_text_color(0, 0, 0)


def _draw_kpi_card(
    pdf: FPDF,
    x: float,
    y: float,
    width: float,
    label: str,
    value: str,
) -> None:
    """Draw a single KPI summary card.

    Args:
        pdf (FPDF): Active PDF document.
        x (float): Left edge in millimeters.
        y (float): Top edge in millimeters.
        width (float): Card width in millimeters.
        label (str): Metric label.
        value (str): Metric value.
    """
    pdf.set_fill_color(*_COLOR_CARD_FILL)
    pdf.set_draw_color(*_COLOR_BORDER)
    pdf.set_line_width(0.3)
    pdf.rect(x, y, width, _KPI_CARD_HEIGHT, style="DF")

    pdf.set_xy(x, y + 3)
    pdf.set_font(_FONT, "", _KPI_LABEL_SIZE)
    pdf.set_text_color(*_COLOR_MUTED)
    pdf.cell(width, 4, _safe_text(label), align="C")

    pdf.set_xy(x, y + 8)
    pdf.set_font(_FONT, "B", _KPI_VALUE_SIZE)
    pdf.set_text_color(*_COLOR_PRIMARY)
    pdf.cell(width, 7, _safe_text(value), align="C")
    pdf.set_text_color(0, 0, 0)


def _draw_executive_summary(pdf: FPDF, report: LicenseTrackerReport) -> None:
    """Draw KPI cards, renewal callouts, and compliance snapshot.

    Args:
        pdf (FPDF): Active PDF document.
        report (LicenseTrackerReport): The full license tracker report.
    """
    summary = report.summary
    _draw_section_title(pdf, "Executive summary", compact=True)

    card_count = 4
    card_width = (pdf.epw - _KPI_CARD_GAP * (card_count - 1)) / card_count
    y = pdf.get_y()
    cards = [
        ("Agreements", str(summary.agreement_count)),
        ("Products", str(summary.product_count)),
        ("Hosts", str(summary.host_count)),
        ("Physical cores", str(summary.total_physical_cores)),
    ]
    for index, (label, value) in enumerate(cards):
        x = pdf.l_margin + index * (card_width + _KPI_CARD_GAP)
        _draw_kpi_card(pdf, x, y, card_width, label, value)

    pdf.set_y(y + _KPI_CARD_HEIGHT + 3)

    renewal_y = pdf.get_y()
    renewal_width = (pdf.epw - _KPI_CARD_GAP * 2) / 3
    renewals = [
        ("30 days", summary.renewals_30_days),
        ("60 days", summary.renewals_60_days),
        ("90 days", summary.renewals_90_days),
    ]
    for index, (period, count) in enumerate(renewals):
        x = pdf.l_margin + index * (renewal_width + _KPI_CARD_GAP)
        pdf.set_fill_color(*_COLOR_CARD_FILL)
        pdf.set_draw_color(*_COLOR_BORDER)
        pdf.rect(x, renewal_y, renewal_width, _RENEWAL_STRIP_HEIGHT, style="DF")

        pdf.set_xy(x + 3, renewal_y + 2)
        pdf.set_font(_FONT, "", _KPI_LABEL_SIZE)
        pdf.set_text_color(*_COLOR_MUTED)
        pdf.cell(renewal_width / 2, 4, _safe_text(period))

        value_color = _COLOR_DANGER if period == "30 days" and count > 0 else _COLOR_PRIMARY
        pdf.set_font(_FONT, "B", _RENEWAL_VALUE_SIZE)
        pdf.set_text_color(*value_color)
        pdf.cell(renewal_width / 2 - 3, 4, str(count), align="R")

    pdf.set_y(renewal_y + _RENEWAL_STRIP_HEIGHT + 3)

    total_products = len(report.product_compliance)
    shortfall_count = sum(1 for row in report.product_compliance if row.balance < 0)
    if total_products == 0:
        snapshot = "No product compliance data available."
    elif shortfall_count == 0:
        snapshot = f"All {total_products} tracked products are compliant."
    else:
        snapshot = (
            f"{shortfall_count} of {total_products} products have license "
            "shortfalls requiring attention."
        )

    pdf.set_font(_FONT, "", _KPI_LABEL_SIZE)
    snapshot_color = _COLOR_DANGER if shortfall_count > 0 else _COLOR_SUCCESS
    pdf.set_text_color(*snapshot_color)
    pdf.cell(0, 4, _safe_text(snapshot), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def _draw_table(
    pdf: FPDF,
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[float],
    aligns: list[str] | None = None,
    cell_style: CellStyleFn | None = None,
) -> None:
    """Draw a bordered table with zebra striping and optional per-cell styling.

    Args:
        pdf (FPDF): Active PDF document.
        headers (list[str]): Column headings.
        rows (list[list[str]]): Table body rows.
        col_widths (list[float]): Column widths in millimeters.
        aligns (list[str] | None): Optional horizontal alignments per column.
        cell_style (CellStyleFn | None): Optional per-cell FontFace factory.
    """
    aligns_tuple = tuple(aligns) if aligns else ("LEFT",) * len(headers)

    with pdf.table(
        col_widths=tuple(col_widths),
        width=pdf.epw,
        text_align=aligns_tuple,
        line_height=pdf.font_size * 1.4,
    ) as table:
        header_row = table.row()
        header_style = FontFace(
            family=_FONT,
            emphasis="B",
            size_pt=_HEADER_SIZE,
            fill_color=_COLOR_HEADER_FILL,
            color=_COLOR_PRIMARY,
        )
        for header in headers:
            header_row.cell(_safe_text(header), style=header_style)

        for row_idx, row in enumerate(rows):
            stripe = _COLOR_ZEBRA if row_idx % 2 == 0 else _COLOR_WHITE
            data_row = table.row()
            for col_idx, value in enumerate(row):
                style = FontFace(
                    family=_FONT,
                    size_pt=_BODY_SIZE,
                    fill_color=stripe,
                )
                if cell_style is not None:
                    override = cell_style(row_idx, col_idx, value)
                    if override is not None:
                        style = override
                data_row.cell(_safe_text(value), style=style)


def _agreement_cell_style(row_idx: int, col_idx: int, value: str) -> FontFace | None:
    """Apply status coloring to agreement table cells.

    Args:
        row_idx (int): Zero-based row index.
        col_idx (int): Zero-based column index.
        value (str): Cell text.

    Returns:
        FontFace | None: Style override for status column cells.
    """
    if col_idx != 2:
        return None
    stripe = _COLOR_ZEBRA if row_idx % 2 == 0 else _COLOR_WHITE
    return FontFace(
        family=_FONT,
        size_pt=_BODY_SIZE,
        fill_color=stripe,
        color=_status_text_color(value),
    )


def _compliance_cell_style(row_idx: int, col_idx: int, value: str) -> FontFace | None:
    """Apply balance coloring to compliance table cells.

    Args:
        row_idx (int): Zero-based row index.
        col_idx (int): Zero-based column index.
        value (str): Cell text.

    Returns:
        FontFace | None: Style override for balance column cells.
    """
    if col_idx != 5:
        return None
    stripe = _COLOR_ZEBRA if row_idx % 2 == 0 else _COLOR_WHITE
    return FontFace(
        family=_FONT,
        size_pt=_BODY_SIZE,
        fill_color=stripe,
        color=_balance_text_color(value),
        emphasis="B",
    )


def _draw_visual_insights(pdf: FPDF, report: LicenseTrackerReport) -> None:
    """Draw the compliance chart in a full-width card layout.

    Args:
        pdf (FPDF): Active PDF document.
        report (LicenseTrackerReport): The full license tracker report.
    """
    comp_buf = generate_compliance_chart(report)
    if comp_buf is None:
        return

    _draw_section_title(
        pdf,
        "Visual insights",
        description="Licensed versus in-use counts by product.",
        compact=True,
    )

    card_x = pdf.l_margin
    card_y = pdf.get_y() + 1
    padding = 2
    chart_w = pdf.epw - 2 * padding
    image_x = card_x + padding
    image_y = card_y + padding
    max_chart_h = pdf.h - pdf.b_margin - image_y - padding - 2
    max_chart_h = max(35, max_chart_h)

    comp_buf.seek(0)
    with Image.open(comp_buf) as chart_image:
        px_width, px_height = chart_image.size
    comp_buf.seek(0)
    chart_h_at_full_w = chart_w * (px_height / px_width)
    if chart_h_at_full_w <= max_chart_h:
        rendered_h = chart_h_at_full_w
    else:
        rendered_h = max_chart_h

    card_h = rendered_h + 2 * padding
    pdf.set_fill_color(*_COLOR_CARD_FILL)
    pdf.rect(card_x, card_y, pdf.epw, card_h, style="F")

    comp_buf.seek(0)
    if chart_h_at_full_w <= max_chart_h:
        pdf.image(comp_buf, x=image_x, y=image_y, w=chart_w)
    else:
        pdf.image(comp_buf, x=image_x, y=image_y, h=max_chart_h)

    pdf.set_draw_color(*_COLOR_BORDER)
    pdf.set_line_width(0.3)
    pdf.rect(card_x, card_y, pdf.epw, card_h, style="D")

    pdf.set_y(card_y + card_h + 2)


def report_to_pdf(report: LicenseTrackerReport) -> bytes:
    """Serialize a full report to a PDF document.

    Args:
        report (LicenseTrackerReport): Report payload.

    Returns:
        bytes: PDF file bytes.
    """
    pdf = _ReportPdf(generated_at=report.generated_at)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=_PAGE_BOTTOM_MARGIN)
    pdf.add_page()

    _draw_cover(pdf)
    _draw_executive_summary(pdf, report)
    _draw_visual_insights(pdf, report)

    _draw_section_title(
        pdf,
        "Contracts and entitlements",
        description="All CSI agreements with purchased product entitlements.",
    )
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
        pdf.set_text_color(*_COLOR_MUTED)
        pdf.cell(0, 5, "No license agreements recorded.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
    else:
        _draw_table(
            pdf,
            ["CSI", "Customer", "Status", "Renewal", "Product", "License type", "License count"],
            agreement_rows,
            [25.0, 45.0, 18.0, 25.0, 100.0, 40.0, 24.0],
            aligns=["LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "RIGHT"],
            cell_style=_agreement_cell_style,
        )

    _draw_section_title(
        pdf,
        "Host usage",
        description="Server inventory with assigned products and calculated license requirements.",
    )
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
        pdf.set_text_color(*_COLOR_MUTED)
        pdf.cell(0, 5, "No hosts in inventory.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
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

    _draw_section_title(
        pdf,
        "Product compliance",
        description="Pooled license inventory compared to in-use counts across all hosts.",
    )
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
        pdf.set_text_color(*_COLOR_MUTED)
        pdf.cell(
            0,
            5,
            "No product compliance rows match the current filter.",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_text_color(0, 0, 0)
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
            cell_style=_compliance_cell_style,
        )

    return bytes(pdf.output())
