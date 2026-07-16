#!/usr/bin/env python3
"""Automated screenshot generator for Oracle License Manager documentation.

Runs FastAPI, React (Vite), seeds data, highlights elements, and captures screenshots.
"""

from __future__ import annotations

import os
import re
import sys
import time
import socket
import subprocess
import urllib.request
import urllib.error
import json
from pathlib import Path


# Ensure dependencies are installed
def setup_playwright():
    """Ensure playwright is installed and configured."""
    print("Checking for playwright Python package...")
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("Installing playwright Python package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])

    print("Checking for Playwright browser binaries...")
    # Try running playwright install chromium
    try:
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install", "chromium"]
        )
    except subprocess.CalledProcessError:
        print("Playwright browser installation failed. Trying fallback...")
        subprocess.check_call(["playwright", "install", "chromium"])


def wait_for_url(url: str, timeout: float = 30.0) -> bool:
    """Poll a URL until it returns 200 OK or timeout is reached."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    return True
        except urllib.error.URLError:
            pass
        time.sleep(0.5)
    return False


def pick_free_ports(count: int = 2) -> list[int]:
    """Reserve distinct unused TCP ports for local dev servers.

    Args:
        count (int): Number of unique ports to allocate.

    Returns:
        list[int]: Available port numbers.
    """
    ports: list[int] = []
    sockets: list[socket.socket] = []
    try:
        while len(ports) < count:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("", 0))
            port = sock.getsockname()[1]
            if port not in ports:
                ports.append(port)
                sockets.append(sock)
    finally:
        for sock in sockets:
            sock.close()
    return ports


def start_managed_process(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    name: str,
) -> subprocess.Popen[str]:
    """Start a child process and fail fast when it exits immediately.

    Args:
        cmd (list[str]): Command and arguments to execute.
        cwd (Path): Working directory for the child process.
        env (dict[str, str]): Environment variables for the child process.
        name (str): Human-readable process label for error messages.

    Returns:
        subprocess.Popen[str]: Running child process handle.

    Raises:
        RuntimeError: If the process exits before becoming ready.
    """
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(0.75)
    if proc.poll() is not None:
        output = proc.stdout.read() if proc.stdout is not None else ""
        raise RuntimeError(f"{name} failed to start:\n{output}")
    return proc


def read_process_output(proc: subprocess.Popen[str]) -> str:
    """Read accumulated stdout/stderr from a managed child process.

    Args:
        proc (subprocess.Popen[str]): Child process handle.

    Returns:
        str: Captured process output, if any.
    """
    if proc.stdout is None:
        return ""
    try:
        return proc.stdout.read()
    except Exception:
        return ""


def make_post_request(url: str, data: dict) -> dict:
    """Send a JSON POST request and return the parsed JSON response."""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def make_get_request(url: str) -> dict | list:
    """Send a GET request and return the parsed JSON response."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_or_create_product_id(
    api_base_url: str, name: str, option: str | None = None
) -> str:
    """Find a catalog product ID by name and option, or create a custom one if missing."""
    import urllib.parse

    search_query = urllib.parse.urlencode({"search": name})
    products = make_get_request(f"{api_base_url}/catalog/products?{search_query}")
    for p in products:
        if p["product_name"].strip().lower() == name.strip().lower():
            p_opt = p.get("option_name") or ""
            o_opt = option or ""
            if p_opt.strip().lower() == o_opt.strip().lower():
                return p["id"]

    # If not found, create a custom product
    payload = {
        "price_list_id": "technology-price-list-070617",
        "category": "Custom",
        "product_name": name,
        "option_name": option,
        "supports_nup": True,
        "supports_processor": True,
    }
    created = make_post_request(f"{api_base_url}/catalog/products", payload)
    return created["id"]


def seed_data(api_base_url: str):
    """Seed the database with realistic mock data using REST API endpoints."""
    print(f"Seeding mock data via API at {api_base_url}...")

    # Pre-resolve product IDs
    db_ee_id = get_or_create_product_id(
        api_base_url, "Database Enterprise Edition", "Enterprise Edition"
    )
    diag_pack_id = get_or_create_product_id(
        api_base_url, "Diagnostics Pack", "Diagnostics Pack"
    )
    tuning_pack_id = get_or_create_product_id(
        api_base_url, "Tuning Pack", "Tuning Pack"
    )
    weblogic_suite_id = get_or_create_product_id(
        api_base_url, "WebLogic Suite", "WebLogic Suite"
    )

    # CSI 1: Global Finance Corp (CPU)
    csi1 = make_post_request(
        f"{api_base_url}/agreements",
        {
            "csi": "CSI-10020030",
            "customer_name": "Global Finance Corp",
            "support_level": "Gold",
            "start_date": "2025-01-01",
            "renewal_date": "2027-01-01",
            "status": "active",
            "notes": "Primary database server licensing agreement",
        },
    )
    csi1_id = csi1["id"]

    # Entitlements for CSI 1 (DB EE is 12 -> causes shortfall of 4 cores)
    make_post_request(
        f"{api_base_url}/agreements/{csi1_id}/entitlements",
        {
            "product_id": db_ee_id,
            "metric": "processor",
            "quantity": 12,
            "notes": "Core database servers",
        },
    )
    make_post_request(
        f"{api_base_url}/agreements/{csi1_id}/entitlements",
        {
            "product_id": diag_pack_id,
            "metric": "processor",
            "quantity": 16,
            "notes": "Diagnostics performance tuning",
        },
    )
    make_post_request(
        f"{api_base_url}/agreements/{csi1_id}/entitlements",
        {
            "product_id": tuning_pack_id,
            "metric": "processor",
            "quantity": 16,
            "notes": "SQL tuning package",
        },
    )

    # CSI 2: Global Finance Corp (Middleware CPU)
    csi2 = make_post_request(
        f"{api_base_url}/agreements",
        {
            "csi": "CSI-40050060",
            "customer_name": "Global Finance Corp",
            "support_level": "Standard",
            "start_date": "2025-06-01",
            "renewal_date": "2026-06-01",
            "status": "active",
            "notes": "Middleware systems",
        },
    )
    csi2_id = csi2["id"]

    make_post_request(
        f"{api_base_url}/agreements/{csi2_id}/entitlements",
        {"product_id": weblogic_suite_id, "metric": "processor", "quantity": 8},
    )

    # CSI 3: Retail Solutions Inc (NUP)
    csi3 = make_post_request(
        f"{api_base_url}/agreements",
        {
            "csi": "CSI-70080090",
            "customer_name": "Retail Solutions Inc",
            "support_level": "Premier",
            "start_date": "2024-01-01",
            "renewal_date": "2026-08-01",
            "status": "active",
            "notes": "Legacy retail app database",
        },
    )
    csi3_id = csi3["id"]

    make_post_request(
        f"{api_base_url}/agreements/{csi3_id}/entitlements",
        {"product_id": db_ee_id, "metric": "named_user_plus", "quantity": 100},
    )

    # Host 1: db-prod-01 (CPU, DB EE, Diag, Tuning)
    h1 = make_post_request(
        f"{api_base_url}/hosts",
        {
            "hostname": "db-prod-01.global.corp",
            "fqdn": "db-prod-01.global.corp",
            "ip_address": "10.0.1.10",
            "environment": "production",
            "license_type": "cpu",
            "ssh_enabled": False,
        },
    )
    h1_id = h1["id"]
    make_post_request(
        f"{api_base_url}/hosts/{h1_id}/cpu-profile",
        {
            "cpu_model": "Intel(R) Xeon(R) Platinum 8268 CPU @ 2.90GHz",
            "socket_count": 2,
            "cores_per_socket": 8,
            "threads_per_core": 2,
        },
    )
    make_post_request(
        f"{api_base_url}/hosts/{h1_id}/entitlements", {"product_id": db_ee_id}
    )
    make_post_request(
        f"{api_base_url}/hosts/{h1_id}/entitlements", {"product_id": diag_pack_id}
    )
    make_post_request(
        f"{api_base_url}/hosts/{h1_id}/entitlements", {"product_id": tuning_pack_id}
    )

    # Host 2: db-prod-02 (CPU, DB EE, Diag)
    h2 = make_post_request(
        f"{api_base_url}/hosts",
        {
            "hostname": "db-prod-02.global.corp",
            "fqdn": "db-prod-02.global.corp",
            "ip_address": "10.0.1.11",
            "environment": "production",
            "license_type": "cpu",
            "ssh_enabled": False,
        },
    )
    h2_id = h2["id"]
    make_post_request(
        f"{api_base_url}/hosts/{h2_id}/cpu-profile",
        {
            "cpu_model": "Intel(R) Xeon(R) Platinum 8268 CPU @ 2.90GHz",
            "socket_count": 2,
            "cores_per_socket": 8,
            "threads_per_core": 2,
        },
    )
    make_post_request(
        f"{api_base_url}/hosts/{h2_id}/entitlements", {"product_id": db_ee_id}
    )
    make_post_request(
        f"{api_base_url}/hosts/{h2_id}/entitlements", {"product_id": diag_pack_id}
    )

    # Host 3: app-prod-01 (CPU, WebLogic Suite)
    h3 = make_post_request(
        f"{api_base_url}/hosts",
        {
            "hostname": "app-prod-01.global.corp",
            "fqdn": "app-prod-01.global.corp",
            "ip_address": "10.0.2.10",
            "environment": "production",
            "license_type": "cpu",
            "ssh_enabled": False,
        },
    )
    h3_id = h3["id"]
    make_post_request(
        f"{api_base_url}/hosts/{h3_id}/cpu-profile",
        {
            "cpu_model": "Intel(R) Xeon(R) Platinum 8268 CPU @ 2.90GHz",
            "socket_count": 1,
            "cores_per_socket": 8,
            "threads_per_core": 2,
        },
    )
    make_post_request(
        f"{api_base_url}/hosts/{h3_id}/entitlements", {"product_id": weblogic_suite_id}
    )

    # Host 4: db-dev-01 (NUP, DB EE)
    h4 = make_post_request(
        f"{api_base_url}/hosts",
        {
            "hostname": "db-dev-01.global.corp",
            "fqdn": "db-dev-01.global.corp",
            "ip_address": "10.0.5.10",
            "environment": "non_production",
            "license_type": "nup",
            "ssh_enabled": False,
        },
    )
    h4_id = h4["id"]
    make_post_request(
        f"{api_base_url}/hosts/{h4_id}/cpu-profile",
        {
            "cpu_model": "Intel(R) Xeon(R) Silver 4214Y CPU @ 2.20GHz",
            "socket_count": 1,
            "cores_per_socket": 4,
            "threads_per_core": 2,
        },
    )
    make_post_request(
        f"{api_base_url}/hosts/{h4_id}/entitlements", {"product_id": db_ee_id}
    )

    # Host 5: app-prod-02 (CPU, WebLogic Suite)
    h5 = make_post_request(
        f"{api_base_url}/hosts",
        {
            "hostname": "app-prod-02.global.corp",
            "fqdn": "app-prod-02.global.corp",
            "ip_address": "10.0.2.11",
            "environment": "production",
            "license_type": "cpu",
            "ssh_enabled": False,
        },
    )
    h5_id = h5["id"]
    make_post_request(
        f"{api_base_url}/hosts/{h5_id}/cpu-profile",
        {
            "cpu_model": "Intel(R) Xeon(R) Platinum 8268 CPU @ 2.90GHz",
            "socket_count": 1,
            "cores_per_socket": 8,
            "threads_per_core": 2,
        },
    )
    make_post_request(
        f"{api_base_url}/hosts/{h5_id}/entitlements", {"product_id": weblogic_suite_id}
    )
    print("Mock data seeded successfully.")
    return csi1_id, h1_id


def inject_highlight_helper(page):
    """Inject javascript helper for UI element highlighting."""
    page.evaluate("""() => {
        window.highlightElement = (selector, label, color = "#f59e0b") => {
            let el;
            if (selector.includes(":has-text(")) {
                const parts = selector.split(":has-text(");
                const tag = parts[0] || "*";
                const text = parts[1].replace(/^["']/, "").replace(/["']\\)$/, "");
                const matches = Array.from(document.querySelectorAll(tag)).filter(
                    (candidate) => candidate.textContent.includes(text),
                );
                el = matches.sort(
                    (left, right) => left.textContent.length - right.textContent.length,
                )[0];
            } else {
                el = document.querySelector(selector);
            }
            if (!el) {
                console.error("Element not found: " + selector);
                return;
            }
            el.style.outline = "3px solid " + color;
            el.style.outlineOffset = "3px";
            el.style.position = "relative";
            
            if (label) {
                const badge = document.createElement("div");
                badge.innerText = label;
                badge.style.position = "fixed";
                badge.style.backgroundColor = color;
                badge.style.color = "white";
                badge.style.padding = "2px 6px";
                badge.style.borderRadius = "4px";
                badge.style.fontSize = "11px";
                badge.style.fontWeight = "bold";
                badge.style.zIndex = "10000";
                badge.style.fontFamily = "system-ui, sans-serif";
                badge.style.boxShadow = "0 2px 4px rgba(0,0,0,0.2)";
                
                const rect = el.getBoundingClientRect();
                badge.style.left = rect.left + "px";
                badge.style.top = Math.max(8, rect.top - 20) + "px";
                document.body.appendChild(badge);
            }
        };
    }""")


def capture_screenshots(frontend_url: str, csi_id: str, host_id: str, output_dir: Path):
    """Use Playwright to take screenshots of each page with elements highlighted."""
    from playwright.sync_api import sync_playwright

    print(f"Launching browser to capture screenshots from {frontend_url}...")
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Force dark mode state since the app has useTheme("dark") on mount
        context = browser.new_context(
            viewport={"width": 1280, "height": 800}, color_scheme="dark"
        )
        page = context.new_page()

        # 1. Dashboard
        print("Capturing Dashboard...")
        page.goto(frontend_url)
        # Wait for data load
        page.wait_for_selector("table tbody tr")
        # Let's wait a moment for react animations
        page.wait_for_timeout(1000)
        inject_highlight_helper(page)

        # Highlight compliance alert
        page.evaluate(
            'window.highlightElement(\'*:has-text("under-licensed")\', "Compliance Warning")'
        )
        # Highlight Shortfall cell in the compliance table for DB Enterprise Edition (first row)
        page.evaluate(
            "window.highlightElement('table tbody tr:nth-child(1) td:nth-child(6)', 'Shortfall / Surplus Balance')"
        )
        # Highlight "Shortfalls only" toggle
        page.evaluate(
            "window.highlightElement('button:has-text(\"Shortfalls only\")', 'Filter Control')"
        )

        page.screenshot(path=str(output_dir / "dashboard.png"))

        # 2. Agreements List
        print("Capturing Agreements list...")
        page.goto(f"{frontend_url}/agreements")
        page.wait_for_selector("table tbody tr")
        page.wait_for_timeout(1000)
        inject_highlight_helper(page)

        # Highlight CSI creation form card
        page.evaluate(
            'window.highlightElement(\'h3:has-text("New agreement")\', "New CSI Contract Creation")'
        )
        # Highlight first agreement entitlements cell
        page.evaluate(
            "window.highlightElement('table tbody tr:nth-child(1) td:nth-child(3)', 'Entitlements List (Wrapped)')"
        )

        page.screenshot(path=str(output_dir / "agreements.png"))

        # 3. Agreement Detail
        print(f"Capturing Agreement detail ({csi_id})...")
        page.goto(f"{frontend_url}/agreements/{csi_id}")
        page.wait_for_selector("table tbody tr")
        page.wait_for_timeout(1000)
        inject_highlight_helper(page)

        # Highlight details metadata card
        page.evaluate(
            "window.highlightElement('h2.text-2xl', \"CSI Metadata & Status\")"
        )
        # Highlight Add product card
        page.evaluate(
            'window.highlightElement(\'h3:has-text("Add product entitlement")\', "Add Product Entitlement Form")'
        )
        # Highlight entitlements table
        page.evaluate("window.highlightElement('table', 'Entitlements Database')")

        page.screenshot(path=str(output_dir / "agreement_detail.png"))

        # 4. Hosts List
        print("Capturing Hosts list...")
        page.goto(f"{frontend_url}/hosts")
        page.wait_for_selector("table tbody tr")
        page.wait_for_timeout(1000)
        inject_highlight_helper(page)

        # Highlight host creation form card
        page.evaluate(
            'window.highlightElement(\'h3:has-text("New host")\', "New Host Server Creation")'
        )
        # Highlight host compliance button
        page.evaluate(
            "window.highlightElement('table tbody tr:nth-child(1) td:nth-child(5) button', 'Compliance Calculator Detail Trigger')"
        )

        page.screenshot(path=str(output_dir / "hosts.png"))

        # 5. Host Detail
        print(f"Capturing Host detail ({host_id})...")
        page.goto(f"{frontend_url}/hosts/{host_id}")
        page.wait_for_selector('h3:has-text("CPU profile")')
        page.wait_for_timeout(1000)
        inject_highlight_helper(page)

        # Highlight CPU profile card
        page.evaluate(
            'window.highlightElement(\'h3:has-text("CPU profile")\', "Host CPU Core Inventory")'
        )
        # Highlight product assignments card
        page.evaluate(
            'window.highlightElement(\'h3:has-text("Assigned products")\', "Product Entitlements Pool Assignment")'
        )

        page.screenshot(path=str(output_dir / "host_detail.png"))

        # 6. Reports Page
        print("Capturing Reports compliance controls...")
        page.goto(f"{frontend_url}/reports")
        page.wait_for_selector("button:has-text('Export PDF')")
        page.wait_for_timeout(1000)
        inject_highlight_helper(page)

        # Highlight export buttons
        page.evaluate(
            'window.highlightElement(\'button:has-text("Export PDF")\', "Compliance Export Controls")'
        )

        page.screenshot(path=str(output_dir / "reports.png"))

        browser.close()
        print("All screenshots captured successfully.")


def write_screenshot_version(output_dir: Path) -> str:
    """Write a cache-busting stamp used by MkDocs when rendering docs pages.

    Args:
        output_dir (Path): Directory containing generated screenshot PNG files.

    Returns:
        str: Unix timestamp written to `.screenshot-version`.
    """
    version = str(int(time.time()))
    version_path = output_dir / ".screenshot-version"
    version_path.write_text(f"{version}\n", encoding="utf-8")
    return version


_README_SCREENSHOT_RE = re.compile(r"(docs/images/[^)\s\"']+\.png)(?:\?v=\d+)?")


def update_readme_screenshot_urls(readme_path: Path, version: str) -> int:
    """Refresh README screenshot links with a cache-busting query parameter.

    Args:
        readme_path (Path): Path to the repository README file.
        version (str): Screenshot generation stamp.

    Returns:
        int: Number of README image URLs updated.
    """
    content = readme_path.read_text(encoding="utf-8")
    updated = _README_SCREENSHOT_RE.sub(rf"\1?v={version}", content)
    if updated == content:
        return 0
    readme_path.write_text(updated, encoding="utf-8")
    return len(_README_SCREENSHOT_RE.findall(content))


def main():
    """Main execution orchestrator."""
    setup_playwright()

    project_root = Path(__file__).resolve().parent.parent

    # Configure temporary SQLite database paths
    temp_config_path = project_root / "config" / "license-tracker-screenshot.yaml"
    temp_db_path = project_root / "data" / "license_tracker_screenshot.db"

    # Ensure temporary DB is clean
    if temp_db_path.exists():
        temp_db_path.unlink()

    # Write temporary YAML config
    print(f"Writing temporary config file to {temp_config_path}...")
    temp_config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_config_path, "w", encoding="utf-8") as f:
        yaml_content = """database_backend: sqlite
sqlite:
  path: data/license_tracker_screenshot.db
"""
        f.write(yaml_content)

    # Pick unused ports so stale local dev servers cannot satisfy health checks.
    backend_port, frontend_port = pick_free_ports(2)
    frontend_origin = f"http://localhost:{frontend_port}"
    backend_env = os.environ.copy()
    backend_env["LICENSE_TRACKER_CONFIG_PATH"] = str(temp_config_path)
    backend_env["LICENSE_TRACKER_CORS_ORIGINS"] = f'["{frontend_origin}"]'

    temp_env_path = project_root / "frontend" / ".env.screenshot.local"
    temp_env_path.write_text(
        f"VITE_API_BASE_URL=http://localhost:{backend_port}\n",
        encoding="utf-8",
    )

    backend_proc: subprocess.Popen[str] | None = None
    frontend_proc: subprocess.Popen[str] | None = None

    try:
        print(f"Starting backend on port {backend_port}...")
        backend_proc = start_managed_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "license_tracker.main:app",
                "--port",
                str(backend_port),
            ],
            project_root / "backend",
            backend_env,
            "Backend server",
        )

        print(f"Starting frontend on port {frontend_port}...")
        frontend_env = os.environ.copy()
        frontend_env["VITE_API_BASE_URL"] = f"http://localhost:{backend_port}"
        frontend_proc = start_managed_process(
            [
                "npm",
                "run",
                "dev",
                "--",
                "--port",
                str(frontend_port),
                "--mode",
                "screenshot",
            ],
            project_root / "frontend",
            frontend_env,
            "Frontend server",
        )
    except RuntimeError as exc:
        print(exc)
        if backend_proc is not None:
            backend_proc.terminate()
        if frontend_proc is not None:
            frontend_proc.terminate()
        temp_env_path.unlink(missing_ok=True)
        sys.exit(1)

    # Wait for servers
    print("Waiting for backend API health check to pass...")
    api_base_url = f"http://localhost:{backend_port}/api/v1"
    if not wait_for_url(f"{api_base_url}/health", timeout=60):
        print("Backend server failed to start or pass health check in time.")
        print(read_process_output(backend_proc))
        backend_proc.terminate()
        frontend_proc.terminate()
        temp_env_path.unlink(missing_ok=True)
        sys.exit(1)

    print("Waiting for frontend web application server...")
    if not wait_for_url(frontend_origin, timeout=60):
        print("Frontend server failed to start in time.")
        print(read_process_output(frontend_proc))
        backend_proc.terminate()
        frontend_proc.terminate()
        temp_env_path.unlink(missing_ok=True)
        sys.exit(1)

    try:
        # Seed mock data
        csi_id, host_id = seed_data(api_base_url)

        # Capture screenshots using playwright
        output_dir = project_root / "docs" / "images"
        capture_screenshots(
            f"http://localhost:{frontend_port}", csi_id, host_id, output_dir
        )
        version = write_screenshot_version(output_dir)
        readme_updates = update_readme_screenshot_urls(
            project_root / "README.md", version
        )
        print(
            f"Updated screenshot cache buster: docs/images/.screenshot-version ({version})"
        )
        print(f"Updated {readme_updates} screenshot URL(s) in README.md")
        print(
            "Reload the docs page in your browser. If images still look stale, restart "
            "`uv run mkdocs serve` and hard-refresh (Cmd+Shift+R)."
        )
        print(
            "Commit and push docs/images/*.png, docs/images/.screenshot-version, and "
            "README.md to refresh GitHub previews."
        )

    finally:
        # Graceful shutdown
        print("Shutting down backend and frontend server processes...")
        if backend_proc is not None:
            backend_proc.terminate()
            backend_proc.wait()
        if frontend_proc is not None:
            frontend_proc.terminate()
            frontend_proc.wait()

        # Cleanup temporary files
        temp_env_path.unlink(missing_ok=True)
        if temp_config_path.exists():
            temp_config_path.unlink()
        if temp_db_path.exists():
            try:
                temp_db_path.unlink()
            except Exception:
                pass
        print("Cleanup completed.")


if __name__ == "__main__":
    main()
