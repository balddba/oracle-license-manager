"""API v1 health, dashboard, and system seeding routes."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from license_tracker.api.deps import DashboardServiceDep, DatabaseDep, get_cpu_service
from license_tracker.domain.enums import (
    CpuProfileSource,
    HostEnvironment,
    HostLicenseType,
    LicenseMetric,
    LicenseStatus,
)
from license_tracker.models import (
    CpuProfileUpsert,
    DashboardSummary,
    HealthResponse,
    HostCreate,
    HostProductAssign,
    LicenseCreate,
    ProductCreate,
)
from license_tracker.services.cpu_service import CpuService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return API liveness status.

    Returns:
        HealthResponse: Health payload.
    """
    return HealthResponse()


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def dashboard_summary(service: DashboardServiceDep) -> DashboardSummary:
    """Return dashboard aggregate metrics.

    Args:
        service (DashboardService): Dashboard service.

    Returns:
        DashboardSummary: Aggregate counts.
    """
    return await service.get_dashboard_summary()


@router.post("/system/seed", status_code=status.HTTP_201_CREATED)
async def seed_database(
    database: DatabaseDep,
    cpu_service: Annotated[CpuService, Depends(get_cpu_service)],
) -> dict[str, str]:
    """Seed the database with realistic sample data if empty.

    Args:
        database (Database): Database client.
        cpu_service (CpuService): CPU service.

    Returns:
        dict[str, str]: Success status message.

    Raises:
        HTTPException: If database is already seeded.
    """
    logger.info("Web API request to seed database received.")
    agreements = await database.list_licenses()
    if agreements:
        logger.warning("Web API seed request rejected: database already contains data.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database already contains agreement records; seeding skipped.",
        )

    # 1. Create Agreements & Entitlements
    agreement_1 = await database.create_license(
        LicenseCreate(
            csi="CSI-8049182",
            customer_name="Omni Consumer Products (OCP)",
            support_level="Premier Support",
            start_date=date(2023, 7, 1),
            renewal_date=date(2027, 6, 30),
            status=LicenseStatus.ACTIVE,
            notes="Primary database agreements covering production virtualization clusters.",
        )
    )

    await database.create_product(
        agreement_1.id,
        ProductCreate(
            product_name="Oracle Database Enterprise Edition",
            option_name=None,
            metric=LicenseMetric.PROCESSOR,
            quantity=16,
            notes="Base database processor licenses.",
        ),
    )
    await database.create_product(
        agreement_1.id,
        ProductCreate(
            product_name="Oracle Database Enterprise Edition",
            option_name="Real Application Clusters",
            metric=LicenseMetric.PROCESSOR,
            quantity=28,
            notes="Required for production active-active cluster nodes.",
        ),
    )
    await database.create_product(
        agreement_1.id,
        ProductCreate(
            product_name="Oracle Database Enterprise Edition",
            option_name="Diagnostics Pack",
            metric=LicenseMetric.PROCESSOR,
            quantity=16,
            notes="Monitoring pack.",
        ),
    )
    await database.create_product(
        agreement_1.id,
        ProductCreate(
            product_name="Oracle Database Enterprise Edition",
            option_name="Tuning Pack",
            metric=LicenseMetric.PROCESSOR,
            quantity=16,
            notes="Tuning tools.",
        ),
    )
    await database.create_product(
        agreement_1.id,
        ProductCreate(
            product_name="Advanced Security",
            option_name=None,
            metric=LicenseMetric.PROCESSOR,
            quantity=28,
            notes="Database security option licensed for all prod cluster cores.",
        ),
    )
    await database.create_product(
        agreement_1.id,
        ProductCreate(
            product_name="SOA Suite for Oracle Middleware",
            option_name=None,
            metric=LicenseMetric.PROCESSOR,
            quantity=10,
            notes="Integration server processor entitlements.",
        ),
    )

    agreement_2 = await database.create_license(
        LicenseCreate(
            csi="CSI-9204851",
            customer_name="Weyland-Yutani Corp",
            support_level="Standard Support",
            start_date=date(2024, 11, 16),
            renewal_date=date(2026, 11, 15),
            status=LicenseStatus.ACTIVE,
            notes=(
                "WebLogic middleware and SE2 database entitlement for non-production environments."
            ),
        )
    )

    await database.create_product(
        agreement_2.id,
        ProductCreate(
            product_name="Oracle WebLogic Suite",
            option_name=None,
            metric=LicenseMetric.NAMED_USER_PLUS,
            quantity=200,
            notes="Non-prod middleware scaling capacity.",
        ),
    )
    await database.create_product(
        agreement_2.id,
        ProductCreate(
            product_name="Oracle Database Standard Edition 2",
            option_name=None,
            metric=LicenseMetric.NAMED_USER_PLUS,
            quantity=300,
            notes="Standard edition development storage.",
        ),
    )
    await database.create_product(
        agreement_2.id,
        ProductCreate(
            product_name="Coherence Enterprise Edition",
            option_name=None,
            metric=LicenseMetric.NAMED_USER_PLUS,
            quantity=250,
            notes="Data grid user entitlements.",
        ),
    )

    agreement_3 = await database.create_license(
        LicenseCreate(
            csi="CSI-3304918",
            customer_name="Tyrell Corporation",
            support_level=None,
            start_date=date(2025, 9, 1),
            renewal_date=date(2026, 8, 31),
            status=LicenseStatus.PENDING,
            notes=("Upcoming renewal under review. Moving WebLogic workloads to CPU-based cores."),
        )
    )

    await database.create_product(
        agreement_3.id,
        ProductCreate(
            product_name="Oracle Database Enterprise Edition",
            option_name="Partitioning",
            metric=LicenseMetric.PROCESSOR,
            quantity=8,
            notes="Database Partitioning option.",
        ),
    )
    await database.create_product(
        agreement_3.id,
        ProductCreate(
            product_name="Oracle WebLogic Suite",
            option_name=None,
            metric=LicenseMetric.PROCESSOR,
            quantity=8,
            notes="Processor metrics for standard cluster.",
        ),
    )
    await database.create_product(
        agreement_3.id,
        ProductCreate(
            product_name="WebLogic Server Enterprise Edition",
            option_name=None,
            metric=LicenseMetric.NAMED_USER_PLUS,
            quantity=100,
            notes="Application server user entitlements.",
        ),
    )

    # 2. Create Hosts, CPU Profiles, and Entitlements
    host_1 = await database.create_host(
        HostCreate(
            hostname="prod-db-cluster-01.balddba.com",
            fqdn="prod-db-cluster-01.balddba.com",
            ip_address="10.200.1.11",
            environment=HostEnvironment.PRODUCTION,
            license_type=HostLicenseType.CPU,
            os_name="Oracle Linux 8.8",
            notes="Active Oracle RAC Node 1. Production database backend.",
            ssh_enabled=True,
            ssh_port=22,
            ssh_user="oracle",
        )
    )
    await cpu_service.upsert_cpu(
        host_1.id,
        CpuProfileUpsert(
            cpu_model="Intel(R) Xeon(R) Gold 6330 CPU @ 2.00GHz",
            socket_count=2,
            cores_per_socket=14,
            threads_per_core=2,
            logical_processor_count=56,
        ),
        source=CpuProfileSource.SSH_PROBE,
    )
    await database.create_host_entitlement(
        host_1.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "",
    )
    await database.create_host_entitlement(
        host_1.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "Real Application Clusters",
    )
    await database.create_host_entitlement(
        host_1.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "Diagnostics Pack",
    )
    await database.create_host_entitlement(
        host_1.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "Tuning Pack",
    )
    await database.create_host_entitlement(
        host_1.id,
        HostProductAssign(product_name="Advanced Security"),
        LicenseMetric.PROCESSOR,
        "",
    )
    await database.create_host_entitlement(
        host_1.id,
        HostProductAssign(product_name="SOA Suite for Oracle Middleware"),
        LicenseMetric.PROCESSOR,
        "",
    )

    host_2 = await database.create_host(
        HostCreate(
            hostname="prod-db-cluster-02.balddba.com",
            fqdn="prod-db-cluster-02.balddba.com",
            ip_address="10.200.1.12",
            environment=HostEnvironment.PRODUCTION,
            license_type=HostLicenseType.CPU,
            os_name="Oracle Linux 8.8",
            notes="Active Oracle RAC Node 2. Production database backend.",
            ssh_enabled=True,
            ssh_port=22,
            ssh_user="oracle",
        )
    )
    await cpu_service.upsert_cpu(
        host_2.id,
        CpuProfileUpsert(
            cpu_model="Intel(R) Xeon(R) Gold 6330 CPU @ 2.00GHz",
            socket_count=2,
            cores_per_socket=14,
            threads_per_core=2,
            logical_processor_count=56,
        ),
        source=CpuProfileSource.SSH_PROBE,
    )
    await database.create_host_entitlement(
        host_2.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "",
    )
    await database.create_host_entitlement(
        host_2.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "Real Application Clusters",
    )
    await database.create_host_entitlement(
        host_2.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "Diagnostics Pack",
    )
    await database.create_host_entitlement(
        host_2.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "Tuning Pack",
    )
    await database.create_host_entitlement(
        host_2.id,
        HostProductAssign(product_name="Advanced Security"),
        LicenseMetric.PROCESSOR,
        "",
    )
    await database.create_host_entitlement(
        host_2.id,
        HostProductAssign(product_name="SOA Suite for Oracle Middleware"),
        LicenseMetric.PROCESSOR,
        "",
    )

    host_3 = await database.create_host(
        HostCreate(
            hostname="nonprod-web-01.balddba.com",
            fqdn="nonprod-web-01.balddba.com",
            ip_address="192.168.4.15",
            environment=HostEnvironment.NON_PRODUCTION,
            license_type=HostLicenseType.NUP,
            os_name="Red Hat Enterprise Linux 9.2",
            notes="Middle tier for Weyland-Yutani dev portal. Uses WebLogic.",
            ssh_enabled=False,
            ssh_port=22,
            ssh_user=None,
        )
    )
    await database._execute(
        "UPDATE hosts SET named_users_required = :named_users_required WHERE id = :id",
        {"id": str(host_3.id), "named_users_required": 120},
    )
    await cpu_service.upsert_cpu(
        host_3.id,
        CpuProfileUpsert(
            cpu_model="AMD EPYC 7543 32-Core Processor",
            socket_count=1,
            cores_per_socket=16,
            threads_per_core=2,
            logical_processor_count=32,
        ),
        source=CpuProfileSource.MANUAL,
    )
    await database.create_host_entitlement(
        host_3.id,
        HostProductAssign(product_name="Oracle WebLogic Suite"),
        LicenseMetric.NAMED_USER_PLUS,
        "",
    )

    host_4 = await database.create_host(
        HostCreate(
            hostname="legacy-se2-db.balddba.com",
            fqdn="legacy-se2-db.balddba.com",
            ip_address="172.16.50.8",
            environment=HostEnvironment.PRODUCTION,
            license_type=HostLicenseType.NUP,
            os_name="Windows Server 2019",
            notes="Standard edition DB hosting customer profiles.",
            ssh_enabled=False,
            ssh_port=22,
            ssh_user=None,
        )
    )
    await database._execute(
        "UPDATE hosts SET named_users_required = :named_users_required WHERE id = :id",
        {"id": str(host_4.id), "named_users_required": 25},
    )
    await cpu_service.upsert_cpu(
        host_4.id,
        CpuProfileUpsert(
            cpu_model="Intel(R) Xeon(R) Silver 4210 CPU @ 2.20GHz",
            socket_count=2,
            cores_per_socket=10,
            threads_per_core=2,
            logical_processor_count=20,
        ),
        source=CpuProfileSource.MANUAL,
    )
    await database.create_host_entitlement(
        host_4.id,
        HostProductAssign(product_name="Oracle Database Standard Edition 2"),
        LicenseMetric.NAMED_USER_PLUS,
        "",
    )

    # Host 5: prod-wls-01.balddba.com (WebLogic EE NUP - Deficit)
    host_5 = await database.create_host(
        HostCreate(
            hostname="prod-wls-01.balddba.com",
            fqdn="prod-wls-01.balddba.com",
            ip_address="10.100.12.30",
            environment=HostEnvironment.PRODUCTION,
            license_type=HostLicenseType.NUP,
            os_name="Oracle Linux 9.1",
            notes="Core application server running WebLogic Enterprise Edition.",
            ssh_enabled=False,
            ssh_port=22,
            ssh_user=None,
        )
    )
    await database._execute(
        "UPDATE hosts SET named_users_required = :named_users_required WHERE id = :id",
        {"id": str(host_5.id), "named_users_required": 150},
    )
    await cpu_service.upsert_cpu(
        host_5.id,
        CpuProfileUpsert(
            cpu_model="Intel(R) Xeon(R) Silver 4214 CPU @ 2.20GHz",
            socket_count=2,
            cores_per_socket=12,
            threads_per_core=2,
            logical_processor_count=48,
        ),
        source=CpuProfileSource.MANUAL,
    )
    await database.create_host_entitlement(
        host_5.id,
        HostProductAssign(product_name="WebLogic Server Enterprise Edition"),
        LicenseMetric.NAMED_USER_PLUS,
        "",
    )

    # Host 6: prod-cache-01.balddba.com (Coherence EE NUP - Balanced)
    host_6 = await database.create_host(
        HostCreate(
            hostname="prod-cache-01.balddba.com",
            fqdn="prod-cache-01.balddba.com",
            ip_address="10.100.12.31",
            environment=HostEnvironment.PRODUCTION,
            license_type=HostLicenseType.NUP,
            os_name="Oracle Linux 9.1",
            notes="Coherence cache cluster member.",
            ssh_enabled=False,
            ssh_port=22,
            ssh_user=None,
        )
    )
    await database._execute(
        "UPDATE hosts SET named_users_required = :named_users_required WHERE id = :id",
        {"id": str(host_6.id), "named_users_required": 50},
    )
    await cpu_service.upsert_cpu(
        host_6.id,
        CpuProfileUpsert(
            cpu_model="Intel(R) Xeon(R) Silver 4210 CPU @ 2.20GHz",
            socket_count=2,
            cores_per_socket=10,
            threads_per_core=2,
            logical_processor_count=40,
        ),
        source=CpuProfileSource.MANUAL,
    )
    await database.create_host_entitlement(
        host_6.id,
        HostProductAssign(product_name="Coherence Enterprise Edition"),
        LicenseMetric.NAMED_USER_PLUS,
        "",
    )

    # Host 7: dev-db-01.balddba.com (Partitioning Processor - Surplus)
    host_7 = await database.create_host(
        HostCreate(
            hostname="dev-db-01.balddba.com",
            fqdn="dev-db-01.balddba.com",
            ip_address="172.16.50.15",
            environment=HostEnvironment.NON_PRODUCTION,
            license_type=HostLicenseType.CPU,
            os_name="Red Hat Enterprise Linux 8.6",
            notes="Development partition database.",
            ssh_enabled=False,
            ssh_port=22,
            ssh_user=None,
        )
    )
    await cpu_service.upsert_cpu(
        host_7.id,
        CpuProfileUpsert(
            cpu_model="Intel(R) Xeon(R) Bronze 3204 CPU @ 1.90GHz",
            socket_count=1,
            cores_per_socket=6,
            threads_per_core=1,
            logical_processor_count=6,
        ),
        source=CpuProfileSource.MANUAL,
    )
    await database.create_host_entitlement(
        host_7.id,
        HostProductAssign(product_name="Oracle Database Enterprise Edition"),
        LicenseMetric.PROCESSOR,
        "Partitioning",
    )

    logger.info("Database seeding completed successfully via Web API request.")
    return {"status": "seeded", "message": "Example developer test data seeded successfully."}
