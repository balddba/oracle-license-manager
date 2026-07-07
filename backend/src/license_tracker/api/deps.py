"""FastAPI dependency injection."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from license_tracker.db.queries.base import Database
from license_tracker.db.session import get_database as _get_database
from license_tracker.services.catalog_service import CatalogService
from license_tracker.services.compliance_service import ComplianceService
from license_tracker.services.core_factor_service import CoreFactorService
from license_tracker.services.cpu_service import CpuService
from license_tracker.services.dashboard_service import DashboardService
from license_tracker.services.host_entitlement_service import HostEntitlementService
from license_tracker.services.host_service import HostService
from license_tracker.services.license_service import LicenseService
from license_tracker.services.product_service import ProductService
from license_tracker.services.report_service import ReportService

DatabaseDep = Annotated[Database, Depends(_get_database)]


async def get_license_service(database: DatabaseDep) -> LicenseService:
    """Provide a license service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        LicenseService: License data service.
    """
    return LicenseService(database)


async def get_product_service(database: DatabaseDep) -> ProductService:
    """Provide a product service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        ProductService: Product entitlement service.
    """
    return ProductService(database)


async def get_host_service(database: DatabaseDep) -> HostService:
    """Provide a host service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        HostService: Host inventory service.
    """
    return HostService(database)


async def get_host_entitlement_service(database: DatabaseDep) -> HostEntitlementService:
    """Provide a host entitlement service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        HostEntitlementService: Host entitlement association service.
    """
    return HostEntitlementService(database)


async def get_cpu_service(database: DatabaseDep) -> CpuService:
    """Provide a CPU profile service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        CpuService: CPU profile service.
    """
    return CpuService(database)


async def get_core_factor_service(database: DatabaseDep) -> CoreFactorService:
    """Provide a core factor service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        CoreFactorService: Processor core factor service.
    """
    return CoreFactorService(database)


async def get_catalog_service(database: DatabaseDep) -> CatalogService:
    """Provide a catalog service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        CatalogService: Oracle catalog service.
    """
    return CatalogService(database)


async def get_compliance_service(database: DatabaseDep) -> ComplianceService:
    """Provide a compliance service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        ComplianceService: Agreement compliance service.
    """
    return ComplianceService(database)


async def get_dashboard_service(database: DatabaseDep) -> DashboardService:
    """Provide a dashboard service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        DashboardService: Dashboard aggregate service.
    """
    return DashboardService(database)


async def get_report_service(database: DatabaseDep) -> ReportService:
    """Provide a report service for the request.

    Args:
        database (Database): Database backend.

    Returns:
        ReportService: Full report service.
    """
    return ReportService(database)


LicenseServiceDep = Annotated[LicenseService, Depends(get_license_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
HostServiceDep = Annotated[HostService, Depends(get_host_service)]
HostEntitlementServiceDep = Annotated[HostEntitlementService, Depends(get_host_entitlement_service)]
CpuServiceDep = Annotated[CpuService, Depends(get_cpu_service)]
CoreFactorServiceDep = Annotated[CoreFactorService, Depends(get_core_factor_service)]
CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
ComplianceServiceDep = Annotated[ComplianceService, Depends(get_compliance_service)]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
