"""API v1 Oracle catalog product routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from license_tracker.api.deps import CatalogServiceDep
from license_tracker.models import CatalogProductCreate, CatalogProductRead, CatalogProductUpdate

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/categories", response_model=list[str])
async def list_catalog_categories(service: CatalogServiceDep) -> list[str]:
    """List distinct Oracle catalog product categories.

    Args:
        service (CatalogService): Catalog service.

    Returns:
        list[str]: Category names.
    """
    return await service.list_categories()


@router.get("/products", response_model=list[CatalogProductRead])
async def list_catalog_products(
    service: CatalogServiceDep,
    search: str | None = Query(None, min_length=1),
    category: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[CatalogProductRead]:
    """Search Oracle catalog products from the technology price list.

    Args:
        service (CatalogService): Catalog service.
        search (str | None): Product name search string.
        category (str | None): Category filter.
        offset (int): Pagination offset.
        limit (int): Maximum rows to return.

    Returns:
        list[CatalogProductRead]: Matching catalog products.
    """
    rows = await service.list_products(
        search=search,
        category=category,
        offset=offset,
        limit=limit,
    )
    return [CatalogProductRead.model_validate(row) for row in rows]


@router.post("/products", response_model=CatalogProductRead, status_code=status.HTTP_201_CREATED)
async def create_catalog_product(
    data: CatalogProductCreate,
    service: CatalogServiceDep,
) -> CatalogProductRead:
    """Create an Oracle catalog product row.

    Args:
        data (CatalogProductCreate): Creation payload.
        service (CatalogService): Catalog service.

    Returns:
        CatalogProductRead: Created catalog product row.
    """
    row = await service.create_product(data)
    return CatalogProductRead.model_validate(row)


@router.get("/products/{product_id}", response_model=CatalogProductRead)
async def get_catalog_product(
    product_id: uuid.UUID,
    service: CatalogServiceDep,
) -> CatalogProductRead:
    """Get one Oracle catalog product by id.

    Args:
        product_id (uuid.UUID): Catalog product id.
        service (CatalogService): Catalog service.

    Returns:
        CatalogProductRead: Catalog product row.

    Raises:
        HTTPException: If not found.
    """
    row = await service.get_product(product_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found"
        )
    return CatalogProductRead.model_validate(row)


@router.put("/products/{product_id}", response_model=CatalogProductRead)
async def update_catalog_product(
    product_id: uuid.UUID,
    data: CatalogProductUpdate,
    service: CatalogServiceDep,
) -> CatalogProductRead:
    """Update an Oracle catalog product row.

    Args:
        product_id (uuid.UUID): Catalog product id.
        data (CatalogProductUpdate): Update payload.
        service (CatalogService): Catalog service.

    Returns:
        CatalogProductRead: Updated catalog product row.

    Raises:
        HTTPException: If not found.
    """
    row = await service.update_product(product_id, data)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found"
        )
    return CatalogProductRead.model_validate(row)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog_product(
    product_id: uuid.UUID,
    service: CatalogServiceDep,
) -> None:
    """Delete an Oracle catalog product row.

    Args:
        product_id (uuid.UUID): Catalog product id.
        service (CatalogService): Catalog service.

    Raises:
        HTTPException: If not found.
    """
    deleted = await service.delete_product(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found"
        )
