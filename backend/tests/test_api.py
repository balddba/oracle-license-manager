"""API integration tests."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from license_tracker.db.session import get_database


async def _get_catalog_product_id(client: AsyncClient, name: str, option: str | None = None) -> str:
    """Helper to retrieve a catalog product ID by name and option."""
    resp = await client.get("/api/v1/catalog/products")
    assert resp.status_code == 200
    products = resp.json()
    for product in products:
        if product["product_name"].lower() == name.lower():
            p_opt = product.get("option_name") or ""
            o_opt = option or ""
            if p_opt.lower() == o_opt.lower():
                return product["id"]
    # Create custom catalog product if not found
    create_resp = await client.post(
        "/api/v1/catalog/products",
        json={
            "price_list_id": "technology-price-list-070617",
            "category": "Custom",
            "product_name": name,
            "option_name": option,
            "supports_nup": True,
            "supports_processor": True,
        },
    )
    assert create_resp.status_code == 201
    return create_resp.json()["id"]


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    """Health endpoint returns ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_hosts(client: AsyncClient) -> None:
    """Hosts list endpoint returns successfully."""
    response = await client.get("/api/v1/hosts")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_agreement_crud(client: AsyncClient) -> None:
    """Create, read, update, and delete an agreement."""
    create_resp = await client.post(
        "/api/v1/agreements",
        json={
            "csi": "CSI-12345",
            "customer_name": "Acme Corp",
            "status": "active",
        },
    )
    assert create_resp.status_code == 201
    agreement = create_resp.json()
    agreement_id = agreement["id"]

    get_resp = await client.get(f"/api/v1/agreements/{agreement_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["csi"] == "CSI-12345"

    update_resp = await client.put(
        f"/api/v1/agreements/{agreement_id}",
        json={"customer_name": "Acme International"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["customer_name"] == "Acme International"

    delete_resp = await client.delete(f"/api/v1/agreements/{agreement_id}")
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_entitlement_under_agreement(client: AsyncClient) -> None:
    """Create entitlement nested under agreement."""
    agreement = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-999", "customer_name": "Test"},
        )
    ).json()
    agreement_id = agreement["id"]
    p_id = await _get_catalog_product_id(
        client, "Database Enterprise Edition", "Enterprise Edition"
    )
    ent_resp = await client.post(
        f"/api/v1/agreements/{agreement_id}/entitlements",
        json={
            "product_id": p_id,
            "metric": "processor",
            "quantity": 8,
        },
    )
    assert ent_resp.status_code == 201
    assert ent_resp.json()["quantity"] == 8

    list_resp = await client.get("/api/v1/agreements")
    assert list_resp.status_code == 200
    row = next(item for item in list_resp.json() if item["id"] == agreement_id)
    assert row["product_count"] == 1
    assert row["products"][0]["product_name"] == "Database Enterprise Edition"
    assert row["products"][0]["metric"] == "processor"
    assert row["products"][0]["quantity"] == 8

    update_resp = await client.put(
        f"/api/v1/agreements/{agreement_id}/entitlements/{ent_resp.json()['id']}",
        json={"quantity": 10, "metric": "named_user_plus"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["quantity"] == 10
    assert update_resp.json()["metric"] == "named_user_plus"


@pytest.mark.asyncio
async def test_processor_license_calculation_from_cpu_profile(client: AsyncClient) -> None:
    """CPU profile resolves core factor and processor license count."""
    host = (
        await client.post(
            "/api/v1/hosts",
            json={"hostname": "db-proc.example.com"},
        )
    ).json()
    host_id = host["id"]

    cpu_resp = await client.post(
        f"/api/v1/hosts/{host_id}/cpu-profile",
        json={
            "cpu_model": "Intel Xeon Gold 6248",
            "socket_count": 2,
            "cores_per_socket": 16,
            "threads_per_core": 2,
        },
    )
    assert cpu_resp.status_code == 200
    body = cpu_resp.json()
    assert body["core_factor"] == 0.5
    assert body["core_factor_name"] == "Intel Xeon Gold 62xx"
    assert body["physical_cores"] == 32
    assert body["processor_licenses_required"] == 16


@pytest.mark.asyncio
async def test_core_factor_resolve_endpoint(client: AsyncClient) -> None:
    """Resolve endpoint maps CPU models using the Oracle core factor table."""
    factors_resp = await client.get("/api/v1/core-factors")
    assert factors_resp.status_code == 200
    factors = factors_resp.json()
    assert len(factors) >= 50
    assert any(row["is_default"] for row in factors)

    resolve_resp = await client.get(
        "/api/v1/core-factors/resolve",
        params={"cpu_model": "Intel(R) Xeon(R) CPU E5-2690 v4 @ 2.60GHz"},
    )
    assert resolve_resp.status_code == 200
    body = resolve_resp.json()
    assert body["core_factor"] == 0.5
    assert "E5-26" in body["name"]


@pytest.mark.asyncio
async def test_agreement_processor_compliance(client: AsyncClient) -> None:
    """CSI compliance reports purchased inventory only."""
    agreement = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-COMP", "customer_name": "Compliance Co"},
        )
    ).json()
    agreement_id = agreement["id"]

    p_id_db = await _get_catalog_product_id(client, "Database Enterprise Edition")
    await client.post(
        f"/api/v1/agreements/{agreement_id}/entitlements",
        json={
            "product_id": p_id_db,
            "metric": "processor",
            "quantity": 20,
        },
    )
    p_id_wl = await _get_catalog_product_id(client, "WebLogic Server")
    await client.post(
        f"/api/v1/agreements/{agreement_id}/entitlements",
        json={
            "product_id": p_id_wl,
            "metric": "named_user_plus",
            "quantity": 100,
        },
    )

    compliance = await client.get(f"/api/v1/agreements/{agreement_id}/compliance")
    assert compliance.status_code == 200
    body = compliance.json()
    assert body["processor_licenses_purchased"] == 20
    assert body["named_user_plus_purchased"] == 100


@pytest.mark.asyncio
async def test_catalog_products_loaded_in_database(client: AsyncClient) -> None:
    """Oracle catalog products are loaded by migration and queried from the database."""
    response = await client.get(
        "/api/v1/catalog/products", params={"search": "Database Enterprise"}
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 1
    assert any(row["product_name"] == "Oracle Database Enterprise Edition" for row in rows)

    categories = await client.get("/api/v1/catalog/categories")
    assert categories.status_code == 200
    assert "Database Products" in categories.json()


@pytest.mark.asyncio
async def test_catalog_product_crud(client: AsyncClient) -> None:
    """Create, read, update, and delete a catalog product."""
    create_resp = await client.post(
        "/api/v1/catalog/products",
        json={
            "price_list_id": "technology-price-list-070617",
            "category": "Test Category",
            "product_name": "Test Database",
            "option_name": "Enterprise",
            "list_price_processor_usd": 47500.0,
            "supports_processor": True,
        },
    )
    assert create_resp.status_code == 201
    product = create_resp.json()
    product_id = product["id"]
    assert product["product_name"] == "Test Database"

    get_resp = await client.get(f"/api/v1/catalog/products/{product_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["option_name"] == "Enterprise"

    update_resp = await client.put(
        f"/api/v1/catalog/products/{product_id}",
        json={"list_price_nup_usd": 950.0, "supports_nup": True},
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["list_price_nup_usd"] == 950.0
    assert body["supports_nup"] is True

    list_resp = await client.get(
        "/api/v1/catalog/products",
        params={"search": "Test Database"},
    )
    assert list_resp.status_code == 200
    assert any(row["id"] == product_id for row in list_resp.json())

    delete_resp = await client.delete(f"/api/v1/catalog/products/{product_id}")
    assert delete_resp.status_code == 204

    missing_resp = await client.get(f"/api/v1/catalog/products/{product_id}")
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_host_product_assignment(client: AsyncClient) -> None:
    """Assign and remove products on a host."""
    agreement = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-HOST-LIC", "customer_name": "Host License Co"},
        )
    ).json()
    agreement_id = agreement["id"]

    p_id_db = await _get_catalog_product_id(client, "Oracle Database Enterprise Edition")
    p_id_tuning = await _get_catalog_product_id(
        client, "Oracle Database Enterprise Edition", "Tuning Pack"
    )
    p_id_wl = await _get_catalog_product_id(client, "WebLogic Server")

    await client.post(
        f"/api/v1/agreements/{agreement_id}/entitlements",
        json={
            "product_id": p_id_db,
            "metric": "processor",
            "quantity": 8,
        },
    )
    await client.post(
        f"/api/v1/agreements/{agreement_id}/entitlements",
        json={
            "product_id": p_id_wl,
            "metric": "processor",
            "quantity": 4,
        },
    )

    host = (
        await client.post(
            "/api/v1/hosts",
            json={"hostname": "db-host-lic.example.com"},
        )
    ).json()
    host_id = host["id"]

    empty_resp = await client.get(f"/api/v1/hosts/{host_id}/entitlements")
    assert empty_resp.status_code == 200
    assert empty_resp.json() == []

    assign_resp = await client.post(
        f"/api/v1/hosts/{host_id}/entitlements",
        json={"product_id": p_id_db},
    )
    assert assign_resp.status_code == 201
    assert assign_resp.json()["product_name"] == "Oracle Database Enterprise Edition"
    assert assign_resp.json()["license_type"] == "cpu"
    assignment_id = assign_resp.json()["id"]

    list_resp = await client.get(f"/api/v1/hosts/{host_id}/entitlements")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    duplicate_resp = await client.post(
        f"/api/v1/hosts/{host_id}/entitlements",
        json={"product_id": p_id_db},
    )
    assert duplicate_resp.status_code == 400

    unassigned = await client.post(
        f"/api/v1/hosts/{host_id}/entitlements",
        json={"product_id": p_id_tuning},
    )
    assert unassigned.status_code == 201
    assert unassigned.json()["option_name"] == "Tuning Pack"

    await client.post(
        f"/api/v1/hosts/{host_id}/entitlements",
        json={"product_id": p_id_wl},
    )
    assert len((await client.get(f"/api/v1/hosts/{host_id}/entitlements")).json()) == 3

    delete_resp = await client.delete(
        f"/api/v1/hosts/{host_id}/entitlements/{assignment_id}",
    )
    assert delete_resp.status_code == 204
    assert len((await client.get(f"/api/v1/hosts/{host_id}/entitlements")).json()) == 2


@pytest.mark.asyncio
async def test_host_product_nup_assignment(client: AsyncClient) -> None:
    """Assign products using the host license type (server is all NUP or all CPU)."""
    agreement = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-NUP", "customer_name": "NUP Co"},
        )
    ).json()
    p_id = await _get_catalog_product_id(client, "Oracle Database Enterprise Edition")
    await client.post(
        f"/api/v1/agreements/{agreement['id']}/entitlements",
        json={
            "product_id": p_id,
            "metric": "named_user_plus",
            "quantity": 50,
        },
    )
    await client.post(
        f"/api/v1/agreements/{agreement['id']}/entitlements",
        json={
            "product_id": p_id,
            "metric": "processor",
            "quantity": 8,
        },
    )

    nup_host = (
        await client.post(
            "/api/v1/hosts",
            json={"hostname": "nup-host.example.com", "license_type": "nup"},
        )
    ).json()
    assert nup_host["license_type"] == "nup"
    assign_nup = await client.post(
        f"/api/v1/hosts/{nup_host['id']}/entitlements",
        json={"product_id": p_id},
    )
    assert assign_nup.status_code == 201
    assert assign_nup.json()["license_type"] == "nup"
    assert assign_nup.json()["metric"] == "named_user_plus"

    cpu_host = (
        await client.post(
            "/api/v1/hosts",
            json={"hostname": "cpu-host.example.com", "license_type": "cpu"},
        )
    ).json()
    assign_cpu = await client.post(
        f"/api/v1/hosts/{cpu_host['id']}/entitlements",
        json={"product_id": p_id},
    )
    assert assign_cpu.status_code == 201
    assert assign_cpu.json()["license_type"] == "cpu"
    assert assign_cpu.json()["metric"] == "processor"

    switch = await client.put(
        f"/api/v1/hosts/{nup_host['id']}",
        json={"license_type": "cpu"},
    )
    assert switch.status_code == 200
    assert switch.json()["license_type"] == "cpu"
    listed = (await client.get(f"/api/v1/hosts/{nup_host['id']}/entitlements")).json()
    assert len(listed) == 1
    assert listed[0]["license_type"] == "cpu"
    assert listed[0]["metric"] == "processor"


@pytest.mark.asyncio
async def test_host_license_type_switch_without_pool_for_target_type(
    client: AsyncClient,
) -> None:
    """Switch license type even when the pool has no entitlements for the new type."""
    agreement = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-SHORT", "customer_name": "Shortfall Co"},
        )
    ).json()
    p_id = await _get_catalog_product_id(
        client, "Oracle Database Enterprise Edition", "Tuning Pack"
    )
    await client.post(
        f"/api/v1/agreements/{agreement['id']}/entitlements",
        json={
            "product_id": p_id,
            "metric": "processor",
            "quantity": 4,
        },
    )

    host = (
        await client.post(
            "/api/v1/hosts",
            json={"hostname": "tuning-host.example.com", "license_type": "cpu"},
        )
    ).json()
    assign = await client.post(
        f"/api/v1/hosts/{host['id']}/entitlements",
        json={"product_id": p_id},
    )
    assert assign.status_code == 201

    switch = await client.put(
        f"/api/v1/hosts/{host['id']}",
        json={"license_type": "nup"},
    )
    assert switch.status_code == 200
    assert switch.json()["license_type"] == "nup"

    listed = (await client.get(f"/api/v1/hosts/{host['id']}/entitlements")).json()
    assert len(listed) == 1
    assert listed[0]["license_type"] == "nup"
    assert listed[0]["metric"] == "named_user_plus"
    assert listed[0]["option_name"] == "Tuning Pack"


@pytest.mark.asyncio
async def test_host_licenses_required_label(client: AsyncClient) -> None:
    """Hosts list shows typed license counts and calculation detail."""
    agreement = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-LABEL", "customer_name": "Label Co"},
        )
    ).json()
    p_id = await _get_catalog_product_id(client, "Database Enterprise Edition")
    await client.post(
        f"/api/v1/agreements/{agreement['id']}/entitlements",
        json={
            "product_id": p_id,
            "metric": "processor",
            "quantity": 20,
        },
    )
    await client.post(
        f"/api/v1/agreements/{agreement['id']}/entitlements",
        json={
            "product_id": p_id,
            "metric": "named_user_plus",
            "quantity": 50,
        },
    )

    cpu_host = (
        await client.post(
            "/api/v1/hosts",
            json={"hostname": "cpu-label.example.com", "license_type": "cpu"},
        )
    ).json()
    await client.post(
        f"/api/v1/hosts/{cpu_host['id']}/cpu-profile",
        json={
            "cpu_model": "Intel Xeon Gold 6248",
            "socket_count": 2,
            "cores_per_socket": 8,
            "threads_per_core": 2,
        },
    )

    nup_host = (
        await client.post(
            "/api/v1/hosts",
            json={
                "hostname": "nup-label.example.com",
                "license_type": "nup",
            },
        )
    ).json()
    await client.post(
        f"/api/v1/hosts/{nup_host['id']}/cpu-profile",
        json={
            "cpu_model": "Intel Xeon Gold 6248",
            "socket_count": 2,
            "cores_per_socket": 8,
            "threads_per_core": 2,
        },
    )

    hosts = (await client.get("/api/v1/hosts")).json()
    cpu_row = next(row for row in hosts if row["id"] == cpu_host["id"])
    nup_row = next(row for row in hosts if row["id"] == nup_host["id"])

    assert cpu_row["licenses_required_label"] == "8 CPU"
    assert any("physical cores" in line for line in cpu_row["licenses_required_detail"])
    assert nup_row["licenses_required_label"] == "200 NUPs"
    assert any(
        "licensable cores × 25 = 200 NUPs" in line for line in nup_row["licenses_required_detail"]
    )


@pytest.mark.asyncio
async def test_pooled_products_across_multiple_csis(client: AsyncClient) -> None:
    """Three CSIs can pool licenses that cover two servers."""
    product_name = "Database Enterprise Edition"
    p_id = await _get_catalog_product_id(client, product_name)
    for csi in ("CSI-1", "CSI-2", "CSI-3"):
        agreement = (
            await client.post(
                "/api/v1/agreements",
                json={"csi": csi, "customer_name": "Pool Co"},
            )
        ).json()
        await client.post(
            f"/api/v1/agreements/{agreement['id']}/entitlements",
            json={"product_id": p_id, "metric": "processor", "quantity": 10},
        )

    pooled = await client.get("/api/v1/hosts/pooled-products")
    assert pooled.status_code == 200
    row = next(item for item in pooled.json() if item["product_name"] == product_name)
    assert row["license_type"] == "cpu"
    assert row["total_quantity"] == 30

    for hostname in ("server-a.example.com", "server-b.example.com"):
        host = (await client.post("/api/v1/hosts", json={"hostname": hostname})).json()
        assign = await client.post(
            f"/api/v1/hosts/{host['id']}/entitlements",
            json={"product_id": p_id},
        )
        assert assign.status_code == 201
        await client.post(
            f"/api/v1/hosts/{host['id']}/cpu-profile",
            json={
                "cpu_model": "Intel Xeon Gold 6248",
                "socket_count": 2,
                "cores_per_socket": 8,
                "threads_per_core": 2,
            },
        )

    dashboard = await client.get("/api/v1/dashboard/summary")
    inventory_row = next(
        row for row in dashboard.json()["license_inventory"] if row["product_name"] == product_name
    )
    assert inventory_row["cores_licensed"] == 30
    assert inventory_row["cores_in_use"] == 16
    assert inventory_row["balance"] == 14


@pytest.mark.asyncio
async def test_host_and_cpu_profile(client: AsyncClient) -> None:
    """Create host and manual CPU profile."""
    host_resp = await client.post(
        "/api/v1/hosts",
        json={"hostname": "db01.example.com", "environment": "production"},
    )
    assert host_resp.status_code == 201
    host_id = host_resp.json()["id"]

    cpu_resp = await client.post(
        f"/api/v1/hosts/{host_id}/cpu-profile",
        json={
            "cpu_model": "Intel Xeon Gold 6248",
            "socket_count": 2,
            "cores_per_socket": 16,
            "threads_per_core": 2,
        },
    )
    assert cpu_resp.status_code == 200
    assert cpu_resp.json()["physical_cores"] == 32


@pytest.mark.asyncio
async def test_probe_cpu_not_implemented(client: AsyncClient) -> None:
    """SSH probe returns 501 in v1."""
    host_id = str(uuid.uuid4())
    response = await client.post(f"/api/v1/hosts/{host_id}/probe-cpu")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient) -> None:
    """Dashboard returns aggregate counts and product license inventory."""
    agreement_a = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-DASH-A", "customer_name": "Dash Co"},
        )
    ).json()
    agreement_b = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-DASH-B", "customer_name": "Dash Co"},
        )
    ).json()

    product_name = "Database Enterprise Edition"
    p_id = await _get_catalog_product_id(client, product_name)
    await client.post(
        f"/api/v1/agreements/{agreement_a['id']}/entitlements",
        json={"product_id": p_id, "metric": "processor", "quantity": 10},
    )
    await client.post(
        f"/api/v1/agreements/{agreement_b['id']}/entitlements",
        json={"product_id": p_id, "metric": "processor", "quantity": 5},
    )
    await client.post(
        f"/api/v1/agreements/{agreement_a['id']}/entitlements",
        json={"product_id": p_id, "metric": "named_user_plus", "quantity": 50},
    )

    host = (
        await client.post(
            "/api/v1/hosts",
            json={"hostname": "db-dash.example.com"},
        )
    ).json()
    await client.post(
        f"/api/v1/hosts/{host['id']}/entitlements",
        json={"product_id": p_id},
    )
    await client.post(
        f"/api/v1/hosts/{host['id']}/cpu-profile",
        json={
            "cpu_model": "Intel Xeon Gold 6248",
            "socket_count": 2,
            "cores_per_socket": 8,
            "threads_per_core": 2,
        },
    )

    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["agreement_count"] >= 2
    assert body["product_count"] == 1
    inventory_row = next(
        row for row in body["license_inventory"] if row["product_name"] == product_name
    )
    assert inventory_row["cores_licensed"] == 15
    assert inventory_row["nups_licensed"] == 50
    assert inventory_row["cores_in_use"] == 8
    assert inventory_row["nups_in_use"] == 0
    assert inventory_row["balance"] == 7


@pytest.mark.asyncio
async def test_full_report(client: AsyncClient) -> None:
    """Full report returns agreements, hosts, and product compliance."""
    agreement = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-REPORT", "customer_name": "Report Co"},
        )
    ).json()
    product_name = "Database Enterprise Edition"
    p_id = await _get_catalog_product_id(client, product_name)
    await client.post(
        f"/api/v1/agreements/{agreement['id']}/entitlements",
        json={"product_id": p_id, "metric": "processor", "quantity": 12},
    )
    host = (
        await client.post(
            "/api/v1/hosts",
            json={"hostname": "db-report.example.com"},
        )
    ).json()
    await client.post(
        f"/api/v1/hosts/{host['id']}/entitlements",
        json={"product_id": p_id},
    )
    await client.post(
        f"/api/v1/hosts/{host['id']}/cpu-profile",
        json={
            "cpu_model": "Intel Xeon Gold 6248",
            "socket_count": 2,
            "cores_per_socket": 8,
            "threads_per_core": 2,
        },
    )

    response = await client.get("/api/v1/reports/full")
    assert response.status_code == 200
    body = response.json()
    assert "generated_at" in body
    assert body["summary"]["agreement_count"] >= 1
    assert any(row["csi"] == "CSI-REPORT" for row in body["agreements"])
    assert any(row["hostname"] == "db-report.example.com" for row in body["hosts"])
    compliance = next(
        row for row in body["product_compliance"] if row["product_name"] == product_name
    )
    assert compliance["cores_licensed"] == 12
    assert compliance["cores_in_use"] == 8
    assert compliance["balance"] == 4

    csv_response = await client.get("/api/v1/reports/full?format=csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    assert "CSI-REPORT" in csv_response.text
    assert "db-report.example.com" in csv_response.text

    pdf_response = await client.get("/api/v1/reports/full?format=pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    pdf_bytes = pdf_response.content
    assert pdf_bytes.startswith(b"%PDF")
    assert pdf_bytes.rstrip().endswith(b"%%EOF")
    assert len(pdf_bytes) > 500


@pytest.mark.asyncio
async def test_global_exception_handler(client: AsyncClient) -> None:
    """Unhandled exceptions are caught and return a 500 JSON response."""
    # Retrieve the FastAPI application from client transport
    app: FastAPI = client._transport.app
    client._transport.raise_app_exceptions = False

    async def raise_error() -> AsyncGenerator[None]:
        raise RuntimeError("Simulated unhandled DB error")
        yield

    app.dependency_overrides[get_database] = raise_error
    try:
        response = await client.get("/api/v1/hosts")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
    finally:
        del app.dependency_overrides[get_database]
        client._transport.raise_app_exceptions = True


@pytest.mark.asyncio
async def test_nup_compliance_balance(client: AsyncClient) -> None:
    """Verify that Named User Plus (NUP) compliance balance is calculated correctly."""
    product_name = "Oracle Database Standard Edition 2"
    p_id = await _get_catalog_product_id(client, product_name)

    # 1. Create CSI agreement with 50 NUP licenses
    agreement = (
        await client.post(
            "/api/v1/agreements",
            json={"csi": "CSI-NUP-TEST", "customer_name": "NUP Test Corp"},
        )
    ).json()
    agreement_id = agreement["id"]

    await client.post(
        f"/api/v1/agreements/{agreement_id}/entitlements",
        json={
            "product_id": p_id,
            "metric": "named_user_plus",
            "quantity": 50,
        },
    )

    # 2. Create host requiring 35 NUP licenses and assign the product
    host = (
        await client.post(
            "/api/v1/hosts",
            json={
                "hostname": "nup-host.example.com",
                "environment": "production",
                "license_type": "nup",
            },
        )
    ).json()
    host_id = host["id"]

    # Assign product as NUP
    await client.post(
        f"/api/v1/hosts/{host_id}/entitlements",
        json={"product_id": p_id},
    )

    # Insert CPU profile manually to compute default core licensing requirements,
    # and update host named_users_required manually
    await client.post(
        f"/api/v1/hosts/{host_id}/cpu-profile",
        json={
            "cpu_model": "Intel Xeon Silver 4210",
            "socket_count": 2,
            "cores_per_socket": 10,
            "threads_per_core": 2,
        },
    )

    # 3. Query the dashboard summary to verify compliance calculation
    dashboard_resp = await client.get("/api/v1/dashboard/summary")
    assert dashboard_resp.status_code == 200
    inventory = dashboard_resp.json()["license_inventory"]

    inventory_row = next(row for row in inventory if row["product_name"] == product_name)

    # cores_licensed = 0 (we only licensed NUP)
    # cores_in_use = 0
    # nups_licensed = 50
    # nups_in_use = 250 (10 core licenses * 25)
    # balance = nups_licensed - nups_in_use = 50 - 250 = -200 (Deficit)
    assert inventory_row["cores_licensed"] == 0
    assert inventory_row["cores_in_use"] == 0
    assert inventory_row["nups_licensed"] == 50
    assert inventory_row["nups_in_use"] == 250
    assert inventory_row["balance"] == -200

    # 4. Now add an additional NUP entitlement of 300 to make it a surplus (total 350 NUP licensed)
    await client.post(
        f"/api/v1/agreements/{agreement_id}/entitlements",
        json={
            "product_id": p_id,
            "metric": "named_user_plus",
            "quantity": 300,
        },
    )

    dashboard_resp2 = await client.get("/api/v1/dashboard/summary")
    inventory2 = dashboard_resp2.json()["license_inventory"]
    inventory_row2 = next(row for row in inventory2 if row["product_name"] == product_name)
    # nups_licensed = 50 + 300 = 350
    # nups_in_use = 250
    # balance = 350 - 250 = 100 (Surplus)
    assert inventory_row2["nups_licensed"] == 350
    assert inventory_row2["balance"] == 100
