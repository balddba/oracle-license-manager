"""Parse Oracle Technology Global Price List PDF into catalog YAML.

Run from repo root:

    uv run --with pypdf --with pyyaml python backend/scripts/parse_oracle_price_list.py \\
        --pdf /tmp/oracle-price-list.pdf \\
        --output data/oracle-technology-price-list-070617.yaml
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml
from pypdf import PdfReader

PRICE_ROW_RE = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z0-9' /&\-\.]+?)\s+"
    r"(?P<nup>[\d,]+\.\d{2}|-)\s+"
    r"(?P<nup_support>[\d,]+\.\d{2}|-)\s+"
    r"(?P<processor>[\d,]+\.\d{2}|-)\s+"
    r"(?P<processor_support>[\d,]+\.\d{2}|-)"
)

CATEGORY_MARKERS: tuple[tuple[str, str], ...] = (
    ("Oracle Database", "Database Products"),
    ("Integration Products", "Integration Products"),
    ("Rdb Server Products", "Rdb Products"),
    ("Application Server Products", "Application Server"),
    ("Data Integration Technology", "Data Integration"),
    ("Analytics Server / Business Intelligence Technology Products", "Business Intelligence"),
    ("Hyperion Business Intelligence Technology", "Hyperion"),
    ("WebCenter Products", "WebCenter"),
    ("Identity Management Products", "Identity Management"),
    ("Database Enterprise Management", "Database Enterprise Management"),
    ("Application Server Enterprise Management", "Application Server Enterprise Management"),
    ("Business Intelligence Management", "Business Intelligence Management"),
    ("WebCenter Management", "WebCenter Management"),
    ("Identity Management Enterprise Management", "Identity Management Enterprise Management"),
    ("Other Infrastructure Management", "Infrastructure Management"),
    ("Service Management", "Service Management"),
    ("Engineered Systems Management", "Engineered Systems Management"),
    ("Application Testing", "Application Testing"),
    ("Tuxedo and Adapters", "Tuxedo"),
    ("Tools", "Tools"),
    ("Other Products", "Other Products"),
    ("TimesTen", "TimesTen"),
    ("Berkeley Database", "Berkeley Database"),
)

OPTION_PREFIXES = (
    "Enterprise Edition Options:",
    "Rdb Server Options:",
    "WebLogic Suite Options:",
    "WebLogic Server Enterprise Edition and WebLogic Suite Options:",
    "SOA Suite for Oracle Middleware Options:",
    "Analytics Server Option:",
    "WebCenter Sites Options:",
    "WebCenter Adapters:",
    "Fusion Middleware Adapters:",
)

DATABASE_EDITION_NAMES = {
    "Standard Edition 2": "Oracle Database Standard Edition 2",
    "Enterprise Edition": "Oracle Database Enterprise Edition",
    "Personal Edition": "Oracle Database Personal Edition",
    "Mobile Server": "Oracle Database Mobile Server",
    "NoSQL Database Enterprise Edition": "Oracle NoSQL Database Enterprise Edition",
}

DATABASE_OPTION_PARENT = "Oracle Database Enterprise Edition"

INVALID_NAME_FRAGMENTS = (
    "Software Update",
    "Named User Plus",
    "ProcessorLicense",
    "License & Support",
    "Licensing Metric",
    "Section ",
    "Prices in USA",
    "Oracle Technology Global Price List",
)


def _parse_price(value: str) -> float | None:
    """Convert a price-list token to a float.

    Args:
        value (str): Raw price token.

    Returns:
        float | None: Parsed amount or None when unavailable.
    """
    if value == "-":
        return None
    return float(value.replace(",", ""))


def _normalize_name(name: str) -> str:
    """Normalize extracted product names.

    Args:
        name (str): Raw product name.

    Returns:
        str: Cleaned product name.
    """
    cleaned = re.sub(r"\s+", " ", name).strip(" :")
    return cleaned


def _is_valid_name(name: str) -> bool:
    """Return whether a parsed product name should be kept.

    Args:
        name (str): Candidate product name.

    Returns:
        bool: True when the name is usable.
    """
    if len(name) < 3 or len(name) > 100:
        return False
    return not any(fragment in name for fragment in INVALID_NAME_FRAGMENTS)


def _normalize_catalog_row(
    category: str,
    name: str,
    option_group: str | None,
    nup: float | None,
    nup_support: float | None,
    processor: float | None,
    processor_support: float | None,
) -> dict[str, object] | None:
    """Normalize one parsed catalog row.

    Args:
        category (str): Product category.
        name (str): Parsed product name.
        option_group (str | None): Option group header when applicable.
        nup (float | None): Named User Plus list price.
        nup_support (float | None): Named User Plus support price.
        processor (float | None): Processor list price.
        processor_support (float | None): Processor support price.

    Returns:
        dict[str, object] | None: Normalized row or None when filtered out.
    """
    product_name = _normalize_name(name)
    option_name = option_group
    if not _is_valid_name(product_name):
        return None

    if category == "Database Products" and product_name in DATABASE_EDITION_NAMES:
        product_name = DATABASE_EDITION_NAMES[product_name]
        option_name = None
    elif category == "Database Products" and option_group == "Enterprise Edition Options":
        option_name = product_name
        product_name = DATABASE_OPTION_PARENT
    elif category == "Database Products" and product_name.startswith("Database "):
        product_name = f"Oracle {product_name}"

    return {
        "category": category,
        "product_name": product_name,
        "option_name": option_name,
        "list_price_nup_usd": nup,
        "list_price_nup_support_usd": nup_support,
        "list_price_processor_usd": processor,
        "list_price_processor_support_usd": processor_support,
        "supports_nup": nup is not None,
        "supports_processor": processor is not None,
    }


def extract_catalog(pdf_path: Path) -> list[dict[str, object]]:
    """Extract catalog rows from the Oracle technology price list PDF.

    Args:
        pdf_path (Path): Path to the Oracle PDF.

    Returns:
        list[dict[str, object]]: Parsed catalog product rows.
    """
    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    text = text.replace("\n", " ")

    category = "Uncategorized"
    seen: set[tuple[str, str, str | None]] = set()
    products: list[dict[str, object]] = []

    for marker, marker_category in CATEGORY_MARKERS:
        text = text.replace(marker, f"\n##CATEGORY##{marker_category}\n")

    for prefix in OPTION_PREFIXES:
        text = text.replace(prefix, f"\n##OPTION##{prefix.rstrip(':')}\n")

    chunks = text.split("##CATEGORY##")
    for chunk in chunks:
        if not chunk.strip():
            continue
        lines = chunk.split("##OPTION##")
        category_part = lines[0]
        category_name = category_part.split("\n", 1)[0].strip()
        if category_name:
            category = category_name
        remainder = category_part[len(category_name) :] if category_name else category_part
        segments = [remainder, *lines[1:]]
        option_group = None
        for index, segment in enumerate(segments):
            if index > 0:
                option_group = segment.split("\n", 1)[0].strip()
                segment_body = segment.split("\n", 1)[-1] if "\n" in segment else ""
            else:
                segment_body = segment
            for match in PRICE_ROW_RE.finditer(segment_body):
                row = _normalize_catalog_row(
                    category,
                    match.group("name"),
                    option_group,
                    _parse_price(match.group("nup")),
                    _parse_price(match.group("nup_support")),
                    _parse_price(match.group("processor")),
                    _parse_price(match.group("processor_support")),
                )
                if row is None:
                    continue
                key = (
                    str(row["category"]),
                    str(row["product_name"]),
                    str(row["option_name"]) if row["option_name"] else None,
                )
                if key in seen:
                    continue
                seen.add(key)
                products.append(row)

    products.sort(
        key=lambda row: (
            str(row["category"]),
            str(row["product_name"]),
            str(row["option_name"] or ""),
        )
    )
    return products


def main() -> None:
    """Parse the Oracle price list PDF and write catalog YAML."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    products = extract_catalog(args.pdf)
    payload = {
        "price_list_id": "technology-price-list-070617",
        "source_url": "https://www.oracle.com/a/ocom/docs/corporate/pricing/technology-price-list-070617.pdf",
        "currency": "USD",
        "products": products,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    print(f"Wrote {len(products)} products to {args.output}")


if __name__ == "__main__":
    main()
