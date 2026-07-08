"""Agreement license compliance calculations."""

from __future__ import annotations

import uuid
from collections import defaultdict

from license_tracker.db.models.product_entitlement import ProductEntitlement
from license_tracker.db.queries.base import Database
from license_tracker.domain.enums import LicenseMetric
from license_tracker.domain.license_calc import calculate_named_users_required
from license_tracker.models import (
    AgreementCompliance,
    ProcessorComplianceLine,
    ProductLicenseSummary,
)
from license_tracker.services.cpu_service import CpuService
from license_tracker.services.license_service import LicenseService

_CORE_METRICS = frozenset(
    {
        LicenseMetric.PROCESSOR,
    }
)
_NAMED_USER_METRICS = frozenset(
    {
        LicenseMetric.NAMED_USER_PLUS,
    }
)


class ComplianceService:
    """Compare pooled entitlements against server product assignments."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database
        self._license_service = LicenseService(database)
        self._cpu_service = CpuService(database)

    async def get_agreement_compliance(self, agreement_id: uuid.UUID) -> AgreementCompliance | None:
        """Return purchased license inventory for a CSI agreement.

        Server coverage is computed organization-wide on the dashboard; individual
        CSIs only record what was purchased under that agreement.

        Args:
            agreement_id (uuid.UUID): Agreement primary key.

        Returns:
            AgreementCompliance | None: Inventory summary if agreement exists.
        """
        # Fetch the specific CSI agreement details from the database
        agreement = await self._license_service.get_license(agreement_id)
        if agreement is None:
            return None

        # Build list of detailed processor compliance lines and aggregate total processors purchased
        processor_lines: list[ProcessorComplianceLine] = []
        processor_purchased_total = 0
        for product in agreement.products:
            # Filter specifically for processor-based metric purchases
            if product.metric != LicenseMetric.PROCESSOR:
                continue
            processor_purchased_total += product.quantity
            processor_lines.append(
                ProcessorComplianceLine(
                    product_id=product.id,
                    product_name=product.product_name,
                    licensed_quantity=product.quantity,
                )
            )

        # Collect and sum up all Named User Plus (NUP) license metrics
        # purchased under this agreement
        nup_products = [
            product
            for product in agreement.products
            if product.metric == LicenseMetric.NAMED_USER_PLUS
        ]
        nup_purchased_total = sum(product.quantity for product in nup_products)

        # Return compliance view summarizing both metric types for this specific CSI agreement
        return AgreementCompliance(
            agreement_id=agreement.id,
            csi=agreement.csi,
            processor_licenses_purchased=processor_purchased_total,
            processor_lines=processor_lines,
            named_user_plus_purchased=nup_purchased_total,
        )

    async def list_license_inventory(self) -> list[ProductLicenseSummary]:
        """Roll up owned and in-use license counts by product across all CSIs.

        Returns:
            list[ProductLicenseSummary]: One row per product name, ordered alphabetically.
        """
        # Fetch all active product entitlements registered across all CSI contracts
        entitlements = await self._db.list_all_products()

        # Group entitlements mapping each unique product name to its list of matching entitlements
        by_product: dict[str, list[ProductEntitlement]] = defaultdict(list)
        for entitlement in entitlements:
            by_product[entitlement.product_name].append(entitlement)

        # Compile consolidated compliance status summaries per product,
        # sorted alphabetically by name
        summaries: list[ProductLicenseSummary] = []
        for product_name in sorted(by_product):
            group = by_product[product_name]

            # Aggregate total licensed core quantities from matching entitlements
            cores_licensed = sum(
                entitlement.quantity for entitlement in group if entitlement.metric in _CORE_METRICS
            )

            # Aggregate total licensed NUP user count from matching entitlements
            nups_licensed = sum(
                entitlement.quantity
                for entitlement in group
                if entitlement.metric in _NAMED_USER_METRICS
            )

            # Calculate current operational metrics from servers running the product
            cores_in_use = await self._cores_in_use_for_product(product_name)
            nups_in_use = await self._nups_in_use_for_product(product_name)

            # Build summary line computing compliance balance
            # (positive balance means surplus, negative means shortfall)
            if cores_licensed > 0 or cores_in_use > 0:
                balance = cores_licensed - cores_in_use
            elif nups_licensed > 0 or nups_in_use > 0:
                balance = nups_licensed - (nups_in_use or 0)
            else:
                balance = 0

            summaries.append(
                ProductLicenseSummary(
                    product_name=product_name,
                    cores_licensed=cores_licensed,
                    nups_licensed=nups_licensed,
                    cores_in_use=cores_in_use,
                    nups_in_use=nups_in_use,
                    balance=balance,
                )
            )
        return summaries

    async def _cores_in_use_for_product(self, product_name: str) -> int:
        """Sum core-based license requirements for hosts running a product.

        Args:
            product_name (str): Product name shared across entitlements.

        Returns:
            int: Processor licenses in use for the product.
        """
        # Retrieve hosts assigned this product under any processor-based metrics
        assignments = await self._db.list_host_entitlements_for_product(
            product_name,
            list(_CORE_METRICS),
        )
        if not assignments:
            return 0

        in_use = 0
        # Track unique host IDs to prevent double-counting processor capacity
        # on hosts with multiple matching assignments
        counted_hosts: set[uuid.UUID] = set()
        for assignment in assignments:
            host_id = assignment.host_id
            if host_id in counted_hosts:
                continue
            # Fetch CPU profile requirements for host
            required = await self._host_processor_required(host_id)
            if required is not None:
                in_use += required
                counted_hosts.add(host_id)
        return in_use

    async def _nups_in_use_for_product(self, product_name: str) -> int:
        """Sum named-user license requirements for hosts running a product.

        Args:
            product_name (str): Product name shared across entitlements.

        Returns:
            int: Named User Plus licenses in use for the product.
        """
        # Retrieve hosts assigned this product under any user-based metrics
        assignments = await self._db.list_host_entitlements_for_product(
            product_name,
            list(_NAMED_USER_METRICS),
        )
        if not assignments:
            return 0

        in_use = 0
        # Track unique host IDs to avoid double-calculating NUP requirements
        # on hosts with multiple assignments
        counted_hosts: set[uuid.UUID] = set()
        for assignment in assignments:
            host_id = assignment.host_id
            if host_id in counted_hosts:
                continue
            # Fetch user minimum profile requirements for host
            required = await self._host_named_users_required(host_id)
            if required is not None:
                in_use += required
                counted_hosts.add(host_id)
        return in_use

    async def _host_named_users_required(self, host_id: uuid.UUID) -> int | None:
        """Return named-user licenses required for a host CPU profile.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            int | None: Required NUP count when a profile exists.
        """
        profile = await self._cpu_service.get_cpus(host_id)
        if profile is None:
            return None
        return calculate_named_users_required(profile.processor_licenses_required)

    async def _host_processor_required(self, host_id: uuid.UUID) -> int | None:
        """Return processor licenses required for a host CPU profile.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            int | None: Required processor licenses when a profile exists.
        """
        profile = await self._cpu_service.get_cpus(host_id)
        if profile is None:
            return None
        return profile.processor_licenses_required
