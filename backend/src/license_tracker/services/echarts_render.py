"""Render Apache ECharts options to PNG via Node canvas."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from loguru import logger

_DEFAULT_RENDERER_DIR = Path(__file__).resolve().parents[3] / "scripts" / "echarts-renderer"
_RENDER_SCRIPT = "render.mjs"


class EChartsRenderError(RuntimeError):
    """Raised when an ECharts option cannot be rendered to PNG."""


def _renderer_dir() -> Path:
    """Resolve the Node renderer directory.

    Returns:
        Path: Directory containing render.mjs and node_modules.
    """
    configured = os.environ.get("LICENSE_TRACKER_ECHARTS_RENDERER")
    if configured:
        return Path(configured)
    return _DEFAULT_RENDERER_DIR


def render_echarts_option(option: dict, *, width: int, height: int) -> bytes:
    """Render an ECharts option object to PNG bytes.

    Args:
        option (dict): ECharts option payload.
        width (int): Image width in pixels.
        height (int): Image height in pixels.

    Returns:
        bytes: PNG image bytes.

    Raises:
        EChartsRenderError: If Node is missing or rendering fails.
    """
    renderer_dir = _renderer_dir()
    script_path = renderer_dir / _RENDER_SCRIPT
    if not script_path.is_file():
        msg = f"ECharts renderer script not found at {script_path}"
        raise EChartsRenderError(msg)

    payload = json.dumps({"width": width, "height": height, "option": option})
    try:
        completed = subprocess.run(
            ["node", str(script_path)],
            input=payload.encode("utf-8"),
            capture_output=True,
            check=False,
            cwd=renderer_dir,
        )
    except FileNotFoundError as exc:
        msg = "Node.js is required to render Apache ECharts report charts."
        raise EChartsRenderError(msg) from exc

    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        logger.error("ECharts render failed: {}", stderr or "unknown error")
        msg = "Failed to render Apache ECharts chart image."
        raise EChartsRenderError(msg)

    if not completed.stdout.startswith(b"\x89PNG"):
        msg = "ECharts renderer did not return a valid PNG image."
        raise EChartsRenderError(msg)

    return completed.stdout
