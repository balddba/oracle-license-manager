"""Database seeding script for developer mock data."""

from __future__ import annotations

import asyncio
import sys
from datetime import date
from pathlib import Path

from loguru import logger

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from license_tracker.config import get_settings
from license_tracker.db.queries.factory import create_database
from license_tracker.db.session import init_db
from license_tracker.domain.enums import (
    CpuProfileSource,
    HostEnvironment,
    HostLicenseType,
    LicenseMetric,
    LicenseStatus,
)
from license_tracker.models import (
    CpuProfileUpsert,
    HostCreate,
    HostProductAssign,
    LicenseCreate,
    ProductCreate,
)
from license_tracker.services.cpu_service import CpuService


async def seed() -> None:
    """Initialize the database and load realistic developer demo data."""
    settings = get_settings()
    logger.info("Initializing database...")
    await init_db(settings)

    database = create_database(settings)
    async with database:
        # Check if agreements already exist
        agreements = await database.list_licenses()
        if agreements:
            logger.info("Database already seeded with {} agreements. Skipping.", len(agreements))
            return

        logger.info("Seeding database with developer mock data...")

        # Initialize CpuService
        cpu_service = CpuService(database)

        # 1. Create Agreements & Entitlements
        # CSI-8049182: Omni Consumer Products (OCP)
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
        logger.info("Created agreement: CSI-8049182")

        # Entitlements for CSI-8049182
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

        # CSI-9204851: Weyland-Yutani Corp
        agreement_2 = await database.create_license(
            LicenseCreate(
                csi="CSI-9204851",
                customer_name="Weyland-Yutani Corp",
                support_level="Standard Support",
                start_date=date(2024, 11, 16),
                renewal_date=date(2026, 11, 15),
                status=LicenseStatus.ACTIVE,
                notes=(
                    "WebLogic middleware and SE2 database entitlement "
                    "for non-production environments."
                ),
            )
        )
        logger.info("Created agreement: CSI-9204851")

        # Entitlements for CSI-9204851
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

        # CSI-3304918: Tyrell Corporation
        agreement_3 = await database.create_license(
            LicenseCreate(
                csi="CSI-3304918",
                customer_name="Tyrell Corporation",
                support_level=None,
                start_date=date(2025, 9, 1),
                renewal_date=date(2026, 8, 31),
                status=LicenseStatus.PENDING,
                notes=(
                    "Upcoming renewal under review. Moving WebLogic workloads to CPU-based cores."
                ),
            )
        )
        logger.info("Created agreement: CSI-3304918")

        # Entitlements for CSI-3304918
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
        # Host 1: prod-db-cluster-01.balddba.com (Processor license)
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
        # Assign products to Host 1
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
        logger.info("Seeded Host: prod-db-cluster-01.balddba.com")

        # Host 2: prod-db-cluster-02.balddba.com (Processor license)
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
        # Assign products to Host 2
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
        logger.info("Seeded Host: prod-db-cluster-02.balddba.com")

        # Host 3: nonprod-web-01.balddba.com (Named User Plus license)
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
        # Assign products to Host 3
        await database.create_host_entitlement(
            host_3.id,
            HostProductAssign(product_name="Oracle WebLogic Suite"),
            LicenseMetric.NAMED_USER_PLUS,
            "",
        )
        logger.info("Seeded Host: nonprod-web-01.balddba.com")

        # Host 4: legacy-se2-db.balddba.com (Standard Edition 2, Named User Plus)
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
        # Assign products to Host 4
        await database.create_host_entitlement(
            host_4.id,
            HostProductAssign(product_name="Oracle Database Standard Edition 2"),
            LicenseMetric.NAMED_USER_PLUS,
            "",
        )
        logger.info("Seeded Host: legacy-se2-db.balddba.com")

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
        logger.info("Seeded Host: prod-wls-01.balddba.com")

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
        logger.info("Seeded Host: prod-cache-01.balddba.com")

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
        logger.info("Seeded Host: dev-db-01.balddba.com")

        await database.commit()
        logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
