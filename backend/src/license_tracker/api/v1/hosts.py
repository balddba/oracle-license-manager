"""API v1 host and CPU profile routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from license_tracker.api.deps import CpuServiceDep, HostEntitlementServiceDep, HostServiceDep
from license_tracker.collectors.ssh import SshHostProbe
from license_tracker.domain.enums import HostLicenseType
from license_tracker.domain.license_calc import calculate_named_users_required
from license_tracker.models import (
    CpuProfileRead,
    CpuProfileUpsert,
    HostCreate,
    HostListRead,
    HostProductAssign,
    HostProductRead,
    HostRead,
    HostUpdate,
    PooledProductRead,
)
from license_tracker.services.host_entitlement_service import HostEntitlementService
from license_tracker.services.host_list_builder import build_host_list_read

router = APIRouter(prefix="/hosts", tags=["hosts"])


def _cpu_to_read(profile) -> CpuProfileRead:
    """Map a CPU profile ORM row to an API response.

    Args:
        profile: Host CPU profile row.

    Returns:
        CpuProfileRead: API response payload.
    """
    matched = profile.matched_core_factor
    return CpuProfileRead(
        id=profile.id,
        host_id=profile.host_id,
        cpu_model=profile.cpu_model,
        core_factor=profile.core_factor,
        core_factor_name=matched.name if matched is not None else None,
        socket_count=profile.socket_count,
        cores_per_socket=profile.cores_per_socket,
        threads_per_core=profile.threads_per_core,
        logical_processor_count=profile.logical_processor_count,
        physical_cores=profile.physical_cores,
        processor_licenses_required=profile.processor_licenses_required,
        source=profile.source,
        collected_at=profile.collected_at,
        created_at=profile.created_at,
    )


@router.get("", response_model=list[HostListRead])
async def list_hosts(
    host_service: HostServiceDep,
    cpu_service: CpuServiceDep,
    entitlement_service: HostEntitlementServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[HostListRead]:
    """List hosts with assigned products and processor license requirements.

    Args:
        host_service (HostService): Host service.
        cpu_service (CpuService): CPU service.
        entitlement_service (HostEntitlementService): Host product assignment service.
        offset (int): Pagination offset.
        limit (int): Page size.

    Returns:
        list[HostListRead]: Host rows.
    """
    hosts = await host_service.get_hosts(offset=offset, limit=limit)
    result: list[HostListRead] = []
    for host in hosts:
        result.append(
            await build_host_list_read(
                host,
                cpu_service=cpu_service,
                entitlement_service=entitlement_service,
            )
        )
    return result


@router.post("", response_model=HostRead, status_code=status.HTTP_201_CREATED)
async def create_host(data: HostCreate, service: HostServiceDep) -> HostRead:
    """Create a host.

    Args:
        data (HostCreate): Creation payload.
        service (HostService): Host service.

    Returns:
        HostRead: Created host.
    """
    row = await service.create_host(data)
    return HostRead.model_validate(row)


@router.get("/pooled-products", response_model=list[PooledProductRead])
async def list_pooled_products(
    entitlement_service: HostEntitlementServiceDep,
) -> list[PooledProductRead]:
    """List distinct products in the pooled license inventory.

    Args:
        entitlement_service (HostEntitlementService): Host entitlement service.

    Returns:
        list[PooledProductRead]: Products available for server assignment.
    """
    return await entitlement_service.list_pooled_products()


@router.get("/{host_id}", response_model=HostRead)
async def get_host(
    host_id: uuid.UUID,
    service: HostServiceDep,
    cpu_service: CpuServiceDep,
) -> HostRead:
    """Get a host by id.

    Args:
        host_id (uuid.UUID): Host id.
        service (HostService): Host service.
        cpu_service (CpuService): CPU service.

    Returns:
        HostRead: Host row.

    Raises:
        HTTPException: If not found.
    """
    row = await service.get_host(host_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    result = HostRead.model_validate(row)
    if result.license_type == HostLicenseType.NUP:
        cpu = await cpu_service.get_cpus(host_id)
        licensable_cores = cpu.processor_licenses_required if cpu is not None else None
        result.named_users_required = calculate_named_users_required(licensable_cores)
    return result


@router.put("/{host_id}", response_model=HostRead)
async def update_host(
    host_id: uuid.UUID,
    data: HostUpdate,
    service: HostServiceDep,
) -> HostRead:
    """Update a host.

    Args:
        host_id (uuid.UUID): Host id.
        data (HostUpdate): Update payload.
        service (HostService): Host service.

    Returns:
        HostRead: Updated host.

    Raises:
        HTTPException: If not found or license type cannot be applied.
    """
    existing = await service.get_host(host_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    try:
        row = await service.update_host(host_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    return HostRead.model_validate(row)


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(host_id: uuid.UUID, service: HostServiceDep) -> None:
    """Delete a host.

    Args:
        host_id (uuid.UUID): Host id.
        service (HostService): Host service.

    Raises:
        HTTPException: If not found.
    """
    deleted = await service.delete_host(host_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")


@router.get("/{host_id}/entitlements", response_model=list[HostProductRead])
async def list_host_entitlements(
    host_id: uuid.UUID,
    host_service: HostServiceDep,
    entitlement_service: HostEntitlementServiceDep,
) -> list[HostProductRead]:
    """List product licenses assigned to a host.

    Args:
        host_id (uuid.UUID): Host id.
        host_service (HostService): Host service.
        entitlement_service (HostEntitlementService): Host entitlement service.

    Returns:
        list[HostProductRead]: Assigned products.

    Raises:
        HTTPException: If host not found.
    """
    host = await host_service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    rows = await entitlement_service.list_for_host(host_id)
    return HostEntitlementService.to_product_reads(rows, host.license_type)


@router.post(
    "/{host_id}/entitlements",
    response_model=HostProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def assign_host_product(
    host_id: uuid.UUID,
    data: HostProductAssign,
    host_service: HostServiceDep,
    entitlement_service: HostEntitlementServiceDep,
) -> HostProductRead:
    """Assign a product license to a host.

    License type is taken from the host (all products on a server are CPU or NUP).
    The product does not need to exist in the pooled inventory.

    Args:
        host_id (uuid.UUID): Host id.
        data (HostProductAssign): Assignment payload.
        host_service (HostService): Host service.
        entitlement_service (HostEntitlementService): Host entitlement service.

    Returns:
        HostProductRead: Assigned product.

    Raises:
        HTTPException: If host not found or assignment is invalid.
    """
    host = await host_service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    try:
        row = await entitlement_service.assign_product(host_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return HostEntitlementService.to_product_reads([row], host.license_type)[0]


@router.delete("/{host_id}/entitlements/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_host_product(
    host_id: uuid.UUID,
    assignment_id: uuid.UUID,
    host_service: HostServiceDep,
    entitlement_service: HostEntitlementServiceDep,
) -> None:
    """Remove a product license assignment from a host.

    Args:
        host_id (uuid.UUID): Host id.
        assignment_id (uuid.UUID): Assignment id.
        host_service (HostService): Host service.
        entitlement_service (HostEntitlementService): Host entitlement service.

    Raises:
        HTTPException: If host or assignment not found.
    """
    host = await host_service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    removed = await entitlement_service.unassign_product(host_id, assignment_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product assignment not found",
        )


@router.get("/{host_id}/cpu-profile", response_model=CpuProfileRead)
async def get_cpu_profile(
    host_id: uuid.UUID,
    host_service: HostServiceDep,
    cpu_service: CpuServiceDep,
) -> CpuProfileRead:
    """Get the current CPU profile for a host.

    Args:
        host_id (uuid.UUID): Host id.
        host_service (HostService): Host service.
        cpu_service (CpuService): CPU service.

    Returns:
        CpuProfileRead: Latest CPU profile.

    Raises:
        HTTPException: If host or profile not found.
    """
    host = await host_service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    profile = await cpu_service.get_cpus(host_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CPU profile not found")
    return _cpu_to_read(profile)


@router.post("/{host_id}/cpu-profile", response_model=CpuProfileRead)
async def upsert_cpu_profile(
    host_id: uuid.UUID,
    data: CpuProfileUpsert,
    host_service: HostServiceDep,
    cpu_service: CpuServiceDep,
) -> CpuProfileRead:
    """Create a manual CPU profile snapshot for a host.

    Args:
        host_id (uuid.UUID): Host id.
        data (CpuProfileUpsert): CPU values.
        host_service (HostService): Host service.
        cpu_service (CpuService): CPU service.

    Returns:
        CpuProfileRead: New profile row.

    Raises:
        HTTPException: If host not found.
    """
    host = await host_service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    profile = await cpu_service.upsert_cpu(host_id, data)
    return _cpu_to_read(profile)


@router.put("/{host_id}/cpu-profile", response_model=CpuProfileRead)
async def update_cpu_profile(
    host_id: uuid.UUID,
    data: CpuProfileUpsert,
    host_service: HostServiceDep,
    cpu_service: CpuServiceDep,
) -> CpuProfileRead:
    """Append a manual CPU profile update (same as POST).

    Args:
        host_id (uuid.UUID): Host id.
        data (CpuProfileUpsert): CPU values.
        host_service (HostService): Host service.
        cpu_service (CpuService): CPU service.

    Returns:
        CpuProfileRead: New profile row.

    Raises:
        HTTPException: If host not found.
    """
    return await upsert_cpu_profile(host_id, data, host_service, cpu_service)


@router.get("/{host_id}/cpu-profile/history", response_model=list[CpuProfileRead])
async def cpu_profile_history(
    host_id: uuid.UUID,
    host_service: HostServiceDep,
    cpu_service: CpuServiceDep,
) -> list[CpuProfileRead]:
    """List CPU profile history for a host.

    Args:
        host_id (uuid.UUID): Host id.
        host_service (HostService): Host service.
        cpu_service (CpuService): CPU service.

    Returns:
        list[CpuProfileRead]: Historical profiles.

    Raises:
        HTTPException: If host not found.
    """
    host = await host_service.get_host(host_id)
    if host is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    profiles = await cpu_service.get_cpu_history(host_id)
    return [_cpu_to_read(p) for p in profiles]


@router.post("/{host_id}/probe-cpu", response_model=CpuProfileRead)
async def probe_cpu(host_id: uuid.UUID) -> CpuProfileRead:
    """Trigger on-demand SSH CPU collection (Phase 4 stub).

    Args:
        host_id (uuid.UUID): Host id.

    Raises:
        HTTPException: Always 501 until SSH probe is implemented.
    """
    _ = host_id
    raise SshHostProbe.not_implemented_error()
