"""Map database rows to domain models and bind values for drivers."""

from __future__ import annotations

import types
import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel

from license_tracker.db.models.catalog_product import CatalogProduct
from license_tracker.db.models.host import Host
from license_tracker.db.models.host_cpu_profile import HostCpuProfile
from license_tracker.db.models.host_entitlement import HostEntitlement
from license_tracker.db.models.license_agreement import LicenseAgreement
from license_tracker.db.models.processor_core_factor import ProcessorCoreFactor
from license_tracker.db.models.product_entitlement import ProductEntitlement


def coerce_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize database row values dynamically for backward compatibility.

    Args:
        row (dict[str, Any]): Raw database row.

    Returns:
        dict[str, Any]: Coerced row values.
    """
    models = [
        Host,
        ProductEntitlement,
        LicenseAgreement,
        HostEntitlement,
        CatalogProduct,
        ProcessorCoreFactor,
        HostCpuProfile,
    ]
    data: dict[str, Any] = {}
    for key, value in row.items():
        key_lower = key.lower() if isinstance(key, str) else key

        # Find if any model defines this key and get its type
        target_type = None
        for model in models:
            if key_lower in model.model_fields:
                field = model.model_fields[key_lower]
                annotation = field.annotation

                # Resolve Union types (like Union[T, None] or T | None)
                origin = get_origin(annotation)
                if origin is Union or (hasattr(types, "UnionType") and origin is types.UnionType):
                    args = get_args(annotation)
                    concrete_types = [arg for arg in args if arg is not type(None)]
                    target_type = concrete_types[0] if concrete_types else annotation
                else:
                    target_type = annotation
                break

        if target_type is uuid.UUID:
            data[key_lower] = _as_uuid(value)
        elif target_type is bool:
            data[key_lower] = _as_bool(value)
        elif isinstance(target_type, type) and issubclass(target_type, Enum):
            data[key_lower] = _coerce_enum_value(target_type, value)
        else:
            data[key_lower] = value

    return data


def coerce_row_for_model(model_cls: type[BaseModel], row: dict[str, Any]) -> dict[str, Any]:
    """Coerce database row columns dynamically based on target model field types.

    Args:
        model_cls (type[BaseModel]): Target Pydantic model class.
        row (dict[str, Any]): Raw database row.

    Returns:
        dict[str, Any]: Coerced row values.
    """
    data: dict[str, Any] = {}
    for key, value in row.items():
        key_lower = key.lower() if isinstance(key, str) else key

        # Check if the model has a field with this lowercased name
        field_name = key_lower
        if field_name not in model_cls.model_fields:
            data[key_lower] = value
            continue

        field = model_cls.model_fields[field_name]
        annotation = field.annotation

        # Resolve Union types (like Union[T, None] or T | None)
        origin = get_origin(annotation)
        if origin is Union or (hasattr(types, "UnionType") and origin is types.UnionType):
            args = get_args(annotation)
            concrete_types = [arg for arg in args if arg is not type(None)]
            target_type = concrete_types[0] if concrete_types else annotation
        else:
            target_type = annotation

        # Coerce values matching known types
        if target_type is uuid.UUID:
            data[key_lower] = _as_uuid(value)
        elif target_type is bool:
            data[key_lower] = _as_bool(value)
        elif isinstance(target_type, type) and issubclass(target_type, Enum):
            data[key_lower] = _coerce_enum_value(target_type, value)
        else:
            data[key_lower] = value

    return data


def bind_value(value: Any) -> Any:
    """Convert a Python value to a driver bind parameter.

    Args:
        value (Any): Python value.

    Returns:
        Any: Driver-friendly bind value.
    """
    if value is None:
        return None
    # Convert programmatic UUID objects to strings for database text compatibility
    if isinstance(value, uuid.UUID):
        return str(value)
    # Convert StrEnum elements to their raw string values
    if isinstance(value, Enum):
        return value.value
    # Convert booleans to integers (1 or 0) for SQLite boolean representations
    if isinstance(value, bool):
        return int(value)
    # Maintain datetime and date objects directly for standard driver inputs
    if isinstance(value, (datetime, date)):
        return value
    return value


def bind_params(params: dict[str, Any]) -> dict[str, Any]:
    """Convert a parameter mapping for driver execution.

    Args:
        params (dict[str, Any]): Named bind parameters.

    Returns:
        dict[str, Any]: Driver-friendly parameters.
    """
    return {key: bind_value(value) for key, value in params.items()}


def map_host(row: dict[str, Any]) -> Host:
    """Map a hosts row to a Host model.

    Args:
        row (dict[str, Any]): Database row.

    Returns:
        Host: Domain model.
    """
    return Host.model_validate(coerce_row_for_model(Host, row))


def map_product(row: dict[str, Any]) -> ProductEntitlement:
    """Map a product_entitlements row to a ProductEntitlement model.

    Args:
        row (dict[str, Any]): Database row.

    Returns:
        ProductEntitlement: Domain model.
    """
    return ProductEntitlement.model_validate(coerce_row_for_model(ProductEntitlement, row))


def map_license(
    row: dict[str, Any],
    products: list[ProductEntitlement] | None = None,
) -> LicenseAgreement:
    """Map a license_agreements row to a LicenseAgreement model.

    Args:
        row (dict[str, Any]): Database row.
        products (list[ProductEntitlement] | None): Nested product entitlements.

    Returns:
        LicenseAgreement: Domain model.
    """
    data = coerce_row_for_model(LicenseAgreement, row)
    agreement = LicenseAgreement.model_validate(data)
    if products is not None:
        agreement.products = products
    return agreement


def map_host_entitlement(row: dict[str, Any]) -> HostEntitlement:
    """Map a host_entitlements row to a HostEntitlement model.

    Args:
        row (dict[str, Any]): Database row.

    Returns:
        HostEntitlement: Domain model.
    """
    return HostEntitlement.model_validate(coerce_row_for_model(HostEntitlement, row))


def map_catalog_product(row: dict[str, Any]) -> CatalogProduct:
    """Map a catalog_products row to a CatalogProduct model.

    Args:
        row (dict[str, Any]): Database row.

    Returns:
        CatalogProduct: Domain model.
    """
    return CatalogProduct.model_validate(coerce_row_for_model(CatalogProduct, row))


def map_core_factor(row: dict[str, Any]) -> ProcessorCoreFactor:
    """Map a processor_core_factors row to a ProcessorCoreFactor model.

    Args:
        row (dict[str, Any]): Database row.

    Returns:
        ProcessorCoreFactor: Domain model.
    """
    return ProcessorCoreFactor.model_validate(coerce_row_for_model(ProcessorCoreFactor, row))


def map_cpu_profile(
    row: dict[str, Any],
    matched_core_factor: ProcessorCoreFactor | None = None,
) -> HostCpuProfile:
    """Map a host_cpu_profiles row to a HostCpuProfile model.

    Args:
        row (dict[str, Any]): Database row.
        matched_core_factor (ProcessorCoreFactor | None): Related core factor.

    Returns:
        HostCpuProfile: Domain model.
    """
    data = coerce_row_for_model(HostCpuProfile, row)
    profile = HostCpuProfile.model_validate(data)
    if matched_core_factor is not None:
        profile.matched_core_factor = matched_core_factor
    return profile


def _as_uuid(value: Any) -> uuid.UUID | None:
    """Coerce a stored value to UUID.

    Args:
        value (Any): Stored value.

    Returns:
        uuid.UUID | None: Parsed UUID.
    """
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _coerce_enum_value(enum_cls: type[Enum], value: Any) -> Any:
    """Normalize a stored enum value for Pydantic validation.

    Legacy rows may store enum member names (for example ``MANUAL``) instead of
    the StrEnum value (``manual``).

    Args:
        enum_cls (type[Enum]): Target StrEnum class.
        value (Any): Stored database value.

    Returns:
        Any: Enum value string when recognized, otherwise the original value.
    """
    if value is None or isinstance(value, enum_cls):
        return value
    text = str(value)
    # Check if the string matches either the member value or name
    for member in enum_cls:
        # Match against either StrEnum value (e.g. 'manual') or name (e.g. 'MANUAL')
        if text == member.value or text == member.name:
            return member.value
    # Fallback to returning the raw text value, allowing Pydantic validation to report errors
    return text


def _as_bool(value: Any) -> bool:
    """Coerce a stored value to bool.

    Args:
        value (Any): Stored value.

    Returns:
        bool: Boolean value.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return bool(int(value))
