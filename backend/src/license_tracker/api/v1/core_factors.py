"""API v1 processor core factor routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from license_tracker.api.deps import CoreFactorServiceDep
from license_tracker.models import CoreFactorCreate, CoreFactorRead, CoreFactorUpdate

router = APIRouter(prefix="/core-factors", tags=["core-factors"])


@router.get("", response_model=list[CoreFactorRead])
async def list_core_factors(service: CoreFactorServiceDep) -> list[CoreFactorRead]:
    """List processor core factor reference rows.

    Args:
        service (CoreFactorService): Core factor service.

    Returns:
        list[CoreFactorRead]: Core factor rows.
    """
    rows = await service.get_core_factors()
    return [CoreFactorRead.model_validate(row) for row in rows]


@router.post("", response_model=CoreFactorRead, status_code=status.HTTP_201_CREATED)
async def create_core_factor(
    data: CoreFactorCreate,
    service: CoreFactorServiceDep,
) -> CoreFactorRead:
    """Create a processor core factor row.

    Args:
        data (CoreFactorCreate): Creation payload.
        service (CoreFactorService): Core factor service.

    Returns:
        CoreFactorRead: Created row.
    """
    row = await service.create_core_factor(data)
    return CoreFactorRead.model_validate(row)


@router.get("/resolve", response_model=CoreFactorRead)
async def resolve_core_factor(
    service: CoreFactorServiceDep,
    cpu_model: str = Query(..., min_length=1),
) -> CoreFactorRead:
    """Resolve the best matching core factor for a CPU model string.

    Args:
        service (CoreFactorService): Core factor service.
        cpu_model (str): CPU model name to match.

    Returns:
        CoreFactorRead: Matched core factor row.

    Raises:
        HTTPException: If no core factor could be resolved.
    """
    _, matched = await service.resolve_for_cpu_model(cpu_model)
    if matched is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No processor core factor configured",
        )
    return CoreFactorRead.model_validate(matched)


@router.put("/{factor_id}", response_model=CoreFactorRead)
async def update_core_factor(
    factor_id: uuid.UUID,
    data: CoreFactorUpdate,
    service: CoreFactorServiceDep,
) -> CoreFactorRead:
    """Update a processor core factor row.

    Args:
        factor_id (uuid.UUID): Core factor id.
        data (CoreFactorUpdate): Update payload.
        service (CoreFactorService): Core factor service.

    Returns:
        CoreFactorRead: Updated row.

    Raises:
        HTTPException: If not found.
    """
    row = await service.update_core_factor(factor_id, data)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Core factor not found")
    return CoreFactorRead.model_validate(row)


@router.delete("/{factor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_core_factor(
    factor_id: uuid.UUID,
    service: CoreFactorServiceDep,
) -> None:
    """Delete a processor core factor row.

    Args:
        factor_id (uuid.UUID): Core factor id.
        service (CoreFactorService): Core factor service.

    Raises:
        HTTPException: If not found.
    """
    deleted = await service.delete_core_factor(factor_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Core factor not found")
