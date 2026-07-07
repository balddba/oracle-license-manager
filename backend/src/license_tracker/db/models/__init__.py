"""Domain models for persisted license tracker entities."""

from license_tracker.db.models.catalog_product import CatalogProduct
from license_tracker.db.models.host import Host
from license_tracker.db.models.host_cpu_profile import HostCpuProfile
from license_tracker.db.models.host_entitlement import HostEntitlement
from license_tracker.db.models.license_agreement import LicenseAgreement
from license_tracker.db.models.processor_core_factor import ProcessorCoreFactor
from license_tracker.db.models.product_entitlement import ProductEntitlement

__all__ = [
    "CatalogProduct",
    "Host",
    "HostCpuProfile",
    "HostEntitlement",
    "LicenseAgreement",
    "ProcessorCoreFactor",
    "ProductEntitlement",
]
