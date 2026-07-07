"""API request and response models."""

from __future__ import annotations

from license_tracker.models.agreement_compliance import AgreementCompliance
from license_tracker.models.catalog_product_create import CatalogProductCreate
from license_tracker.models.catalog_product_read import CatalogProductRead
from license_tracker.models.catalog_product_update import CatalogProductUpdate
from license_tracker.models.core_factor_create import CoreFactorCreate
from license_tracker.models.core_factor_read import CoreFactorRead
from license_tracker.models.core_factor_update import CoreFactorUpdate
from license_tracker.models.cpu_profile_read import CpuProfileRead
from license_tracker.models.cpu_profile_upsert import CpuProfileUpsert
from license_tracker.models.dashboard_summary import DashboardSummary
from license_tracker.models.health_response import HealthResponse
from license_tracker.models.host_create import HostCreate
from license_tracker.models.host_list_read import HostListRead
from license_tracker.models.host_product_assign import HostProductAssign
from license_tracker.models.host_product_read import HostProductRead
from license_tracker.models.host_read import HostRead
from license_tracker.models.host_update import HostUpdate
from license_tracker.models.license_create import LicenseCreate
from license_tracker.models.license_detail_read import LicenseDetailRead
from license_tracker.models.license_list_read import LicenseListRead
from license_tracker.models.license_read import LicenseRead
from license_tracker.models.license_tracker_report import LicenseTrackerReport
from license_tracker.models.license_update import LicenseUpdate
from license_tracker.models.pooled_product_read import PooledProductRead
from license_tracker.models.processor_compliance_line import ProcessorComplianceLine
from license_tracker.models.product_create import ProductCreate
from license_tracker.models.product_license_summary import ProductLicenseSummary
from license_tracker.models.product_read import ProductRead
from license_tracker.models.product_update import ProductUpdate

__all__ = [
    "AgreementCompliance",
    "CatalogProductCreate",
    "CatalogProductRead",
    "CatalogProductUpdate",
    "CoreFactorCreate",
    "CoreFactorRead",
    "CoreFactorUpdate",
    "CpuProfileRead",
    "CpuProfileUpsert",
    "DashboardSummary",
    "HealthResponse",
    "HostCreate",
    "HostListRead",
    "HostProductAssign",
    "HostProductRead",
    "HostRead",
    "HostUpdate",
    "LicenseCreate",
    "LicenseDetailRead",
    "LicenseListRead",
    "LicenseRead",
    "LicenseTrackerReport",
    "LicenseUpdate",
    "PooledProductRead",
    "ProcessorComplianceLine",
    "ProductCreate",
    "ProductLicenseSummary",
    "ProductRead",
    "ProductUpdate",
]
