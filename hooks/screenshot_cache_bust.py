"""MkDocs hooks that append cache-busting query params to regenerated screenshots."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_IMAGE_MARKDOWN_RE = re.compile(r"(!\[[^\]]*\]\()([^)#]+)(\))")


def _read_screenshot_version(config: Any) -> str | None:
    """Load the screenshot generation stamp from docs/images.

    Args:
        config (Any): MkDocs configuration object.

    Returns:
        str | None: Version stamp when present, otherwise None.
    """
    version_path = Path(config.docs_dir) / "images" / ".screenshot-version"
    if not version_path.is_file():
        return None
    version = version_path.read_text(encoding="utf-8").strip()
    return version or None


def _append_version(url: str, version: str) -> str:
    """Append a cache-busting query parameter to a relative image URL.

    Args:
        url (str): Markdown image target.
        version (str): Screenshot generation stamp.

    Returns:
        str: URL with a `v` query parameter when applicable.
    """
    if url.startswith(("http://", "https://", "data:")):
        return url
    if "?" in url:
        return url
    return f"{url}?v={version}"


def on_config(config: Any, **kwargs: Any) -> Any:
    """Append cache-busting query params to the theme logo when screenshots refresh.

    Args:
        config (Any): MkDocs configuration object.
        **kwargs (Any): Unused MkDocs hook arguments.

    Returns:
        Any: Updated MkDocs configuration object.
    """
    version = _read_screenshot_version(config)
    if not version:
        return config

    theme = config.get("theme")
    if isinstance(theme, dict):
        logo = theme.get("logo")
        if isinstance(logo, str):
            theme["logo"] = _append_version(logo, version)
    return config


def on_page_markdown(markdown: str, page: Any, config: Any, **kwargs: Any) -> str:
    """Append cache-busting query params to local markdown image links.

    Args:
        markdown (str): Page markdown source.
        page (Any): MkDocs page metadata.
        config (Any): MkDocs configuration object.
        **kwargs (Any): Unused MkDocs hook arguments.

    Returns:
        str: Markdown with versioned image URLs.
    """
    version = _read_screenshot_version(config)
    if not version:
        return markdown

    def replace_image(match: re.Match[str]) -> str:
        prefix, url, suffix = match.group(1), match.group(2), match.group(3)
        return f"{prefix}{_append_version(url, version)}{suffix}"

    return _IMAGE_MARKDOWN_RE.sub(replace_image, markdown)
