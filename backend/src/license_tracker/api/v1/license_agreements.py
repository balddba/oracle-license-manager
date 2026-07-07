"""API v1 license agreement routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from license_tracker.api.deps import ComplianceServiceDep, LicenseServiceDep, ProductServiceDep
from license_tracker.models import (
    AgreementCompliance,
    LicenseCreate,
    LicenseDetailRead,
    LicenseListRead,
    LicenseRead,
    LicenseUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)

router = APIRouter(prefix="/agreements", tags=["agreements"])


@router.get("", response_model=list[LicenseListRead])
async def list_agreements(
    service: LicenseServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    renewal_within_days: int | None = Query(None, ge=1),
) -> list[LicenseListRead]:
    """List license agreements with product entitlements.

    Args:
        service (LicenseService): License service.
        offset (int): Pagination offset.
        limit (int): Page size.
        renewal_within_days (int | None): Filter by renewal window.

    Returns:
        list[LicenseListRead]: Agreement rows with products and license counts.
    """
    rows = await service.get_licenses(
        offset=offset,
        limit=limit,
        renewal_within_days=renewal_within_days,
    )
    return [
        LicenseListRead(
            **LicenseRead.model_validate(row).model_dump(),
            product_count=len(row.products),
            products=[ProductRead.model_validate(product) for product in row.products],
        )
        for row in rows
    ]


@router.post("", response_model=LicenseRead, status_code=status.HTTP_201_CREATED)
async def create_agreement(
    data: LicenseCreate,
    service: LicenseServiceDep,
) -> LicenseRead:
    """Create a license agreement.

    Args:
        data (LicenseCreate): Creation payload.
        service (LicenseService): License service.

    Returns:
        LicenseRead: Created agreement.
    """
    row = await service.create_license(data)
    return LicenseRead.model_validate(row)


@router.get("/{agreement_id}", response_model=LicenseDetailRead)
async def get_agreement(
    agreement_id: uuid.UUID,
    service: LicenseServiceDep,
) -> LicenseDetailRead:
    """Get agreement detail with entitlements.

    Args:
        agreement_id (uuid.UUID): Agreement id.
        service (LicenseService): License service.

    Returns:
        LicenseDetailRead: Agreement with products.

    Raises:
        HTTPException: If not found.
    """
    row = await service.get_license(agreement_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    return LicenseDetailRead.model_validate(row)


@router.get("/{agreement_id}/compliance", response_model=AgreementCompliance)
async def get_agreement_compliance(
    agreement_id: uuid.UUID,
    service: ComplianceServiceDep,
) -> AgreementCompliance:
    """Return processor and NUP compliance for a CSI agreement.

    Args:
        agreement_id (uuid.UUID): Agreement id.
        service (ComplianceService): Compliance service.

    Returns:
        AgreementCompliance: Compliance summary.

    Raises:
        HTTPException: If not found.
    """
    row = await service.get_agreement_compliance(agreement_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    return row


@router.put("/{agreement_id}", response_model=LicenseRead)
async def update_agreement(
    agreement_id: uuid.UUID,
    data: LicenseUpdate,
    service: LicenseServiceDep,
) -> LicenseRead:
    """Update a license agreement.

    Args:
        agreement_id (uuid.UUID): Agreement id.
        data (LicenseUpdate): Update payload.
        service (LicenseService): License service.

    Returns:
        LicenseRead: Updated agreement.

    Raises:
        HTTPException: If not found.
    """
    row = await service.update_license(agreement_id, data)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    return LicenseRead.model_validate(row)


@router.delete("/{agreement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agreement(
    agreement_id: uuid.UUID,
    service: LicenseServiceDep,
) -> None:
    """Delete a license agreement.

    Args:
        agreement_id (uuid.UUID): Agreement id.
        service (LicenseService): License service.

    Raises:
        HTTPException: If not found.
    """
    deleted = await service.delete_license(agreement_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")


@router.get("/{agreement_id}/entitlements", response_model=list[ProductRead])
async def list_entitlements(
    agreement_id: uuid.UUID,
    license_service: LicenseServiceDep,
    product_service: ProductServiceDep,
) -> list[ProductRead]:
    """List entitlements for an agreement.

    Args:
        agreement_id (uuid.UUID): Agreement id.
        license_service (LicenseService): License service.
        product_service (ProductService): Product service.

    Returns:
        list[ProductRead]: Entitlement rows.

    Raises:
        HTTPException: If agreement not found.
    """
    agreement = await license_service.get_license(agreement_id)
    if agreement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    rows = await product_service.get_products(agreement_id)
    return [ProductRead.model_validate(row) for row in rows]


@router.post(
    "/{agreement_id}/entitlements",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_entitlement(
    agreement_id: uuid.UUID,
    data: ProductCreate,
    license_service: LicenseServiceDep,
    product_service: ProductServiceDep,
) -> ProductRead:
    """Create an entitlement under an agreement.

    Args:
        agreement_id (uuid.UUID): Agreement id.
        data (ProductCreate): Creation payload.
        license_service (LicenseService): License service.
        product_service (ProductService): Product service.

    Returns:
        ProductRead: Created entitlement.

    Raises:
        HTTPException: If agreement not found.
    """
    agreement = await license_service.get_license(agreement_id)
    if agreement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    row = await product_service.create_product(agreement_id, data)
    return ProductRead.model_validate(row)


@router.put("/{agreement_id}/entitlements/{entitlement_id}", response_model=ProductRead)
async def update_entitlement(
    agreement_id: uuid.UUID,
    entitlement_id: uuid.UUID,
    data: ProductUpdate,
    license_service: LicenseServiceDep,
    product_service: ProductServiceDep,
) -> ProductRead:
    """Update an entitlement.

    Args:
        agreement_id (uuid.UUID): Agreement id.
        entitlement_id (uuid.UUID): Entitlement id.
        data (ProductUpdate): Update payload.
        license_service (LicenseService): License service.
        product_service (ProductService): Product service.

    Returns:
        ProductRead: Updated entitlement.

    Raises:
        HTTPException: If not found.
    """
    agreement = await license_service.get_license(agreement_id)
    if agreement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    row = await product_service.get_product(entitlement_id)
    if row is None or row.agreement_id != agreement_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entitlement not found")
    updated = await product_service.update_product(entitlement_id, data)
    assert updated is not None
    return ProductRead.model_validate(updated)


@router.delete(
    "/{agreement_id}/entitlements/{entitlement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_entitlement(
    agreement_id: uuid.UUID,
    entitlement_id: uuid.UUID,
    license_service: LicenseServiceDep,
    product_service: ProductServiceDep,
) -> None:
    """Delete an entitlement.

    Args:
        agreement_id (uuid.UUID): Agreement id.
        entitlement_id (uuid.UUID): Entitlement id.
        license_service (LicenseService): License service.
        product_service (ProductService): Product service.

    Raises:
        HTTPException: If not found.
    """
    agreement = await license_service.get_license(agreement_id)
    if agreement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found")
    row = await product_service.get_product(entitlement_id)
    if row is None or row.agreement_id != agreement_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entitlement not found")
    await product_service.delete_product(entitlement_id)
