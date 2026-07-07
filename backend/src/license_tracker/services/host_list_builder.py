"""Build enriched host list API rows."""

from __future__ import annotations

from license_tracker.db.models.host import Host
from license_tracker.domain.enums import HostLicenseType
from license_tracker.domain.license_calc import (
    NUP_USERS_PER_LICENSE,
    calculate_named_users_required,
)
from license_tracker.models import HostListRead
from license_tracker.services.cpu_service import CpuService
from license_tracker.services.host_entitlement_service import HostEntitlementService


def licenses_required_summary(host: HostListRead) -> tuple[str | None, list[str]]:
    """Build the licenses-required label and calculation detail lines.

    Args:
        host (HostListRead): Host list row with CPU and license fields.

    Returns:
        tuple[str | None, list[str]]: Display label and math lines for the modal.
    """
    if host.license_type == HostLicenseType.NUP:
        named_users = calculate_named_users_required(host.processor_licenses_required)
        if named_users is None:
            return None, ["CPU profile is incomplete — licensable cores cannot be calculated yet."]
        label = f"{named_users} NUPs"
        factor_label = (
            f"{host.core_factor_name} ({host.core_factor})"
            if host.core_factor_name
            else str(host.core_factor)
            if host.core_factor is not None
            else None
        )
        detail = [
            "Server license type: NUP (Named User Plus)",
        ]
        if host.cpu_model:
            detail.append(f"CPU model: {host.cpu_model}")
        if (
            host.socket_count is not None
            and host.cores_per_socket is not None
            and host.physical_cores is not None
            and host.core_factor is not None
            and host.processor_licenses_required is not None
            and factor_label is not None
        ):
            detail.extend(
                [
                    (
                        f"{host.socket_count} sockets × {host.cores_per_socket} cores/socket "
                        f"= {host.physical_cores} physical cores"
                    ),
                    (
                        f"{host.physical_cores} physical cores × {factor_label} "
                        f"= {host.processor_licenses_required} licensable cores"
                    ),
                    (
                        f"{host.processor_licenses_required} licensable cores "
                        f"× {NUP_USERS_PER_LICENSE} = {named_users} NUPs"
                    ),
                ]
            )
        else:
            detail.append(f"Named users required: {named_users}")
        detail.append(f"Total licenses required: {named_users} NUPs")
        if host.assigned_products:
            detail.append("Assigned products:")
            detail.extend(f"• {product}" for product in host.assigned_products)
        return label, detail

    if (
        host.socket_count is None
        or host.cores_per_socket is None
        or host.physical_cores is None
        or host.core_factor is None
        or host.processor_licenses_required is None
    ):
        return None, ["CPU profile is incomplete — licensable cores cannot be calculated yet."]

    label = f"{host.processor_licenses_required} CPU"
    factor_label = (
        f"{host.core_factor_name} ({host.core_factor})"
        if host.core_factor_name
        else str(host.core_factor)
    )
    detail = [
        "Server license type: CPU (processor)",
    ]
    if host.cpu_model:
        detail.append(f"CPU model: {host.cpu_model}")
    detail.extend(
        [
            (
                f"{host.socket_count} sockets × {host.cores_per_socket} cores/socket "
                f"= {host.physical_cores} physical cores"
            ),
            (
                f"{host.physical_cores} physical cores × {factor_label} "
                f"= {host.processor_licenses_required} licensable cores"
            ),
            f"Total licenses required: {host.processor_licenses_required} CPU",
        ]
    )
    if host.assigned_products:
        detail.append("Assigned products:")
        detail.extend(f"• {product}" for product in host.assigned_products)
    return label, detail


async def build_host_list_read(
    host: Host,
    *,
    cpu_service: CpuService,
    entitlement_service: HostEntitlementService,
) -> HostListRead:
    """Enrich a host row with assignments, CPU profile, and license requirements.

    Args:
        host (Host): Persisted host record.
        cpu_service (CpuService): CPU profile service.
        entitlement_service (HostEntitlementService): Host product assignment service.

    Returns:
        HostListRead: API-ready host list row.
    """
    assignments = await entitlement_service.list_for_host(host.id)
    cpu = await cpu_service.get_cpus(host.id)
    item = HostListRead.model_validate(host)
    item.assigned_products = [
        HostEntitlementService.format_assignment_label(row) for row in assignments
    ]
    if cpu is not None:
        matched = cpu.matched_core_factor
        item.cpu_model = cpu.cpu_model
        item.socket_count = cpu.socket_count
        item.cores_per_socket = cpu.cores_per_socket
        item.physical_cores = cpu.physical_cores
        item.core_factor = cpu.core_factor
        item.core_factor_name = matched.name if matched is not None else None
        item.processor_licenses_required = cpu.processor_licenses_required
    if item.license_type == HostLicenseType.NUP:
        item.named_users_required = calculate_named_users_required(item.processor_licenses_required)
    item.licenses_required_label, item.licenses_required_detail = licenses_required_summary(item)
    return item
