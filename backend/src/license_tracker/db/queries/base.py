"""Abstract database interface and shared query implementations."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Self

from license_tracker.db.mappers import (
    bind_params,
    map_cpu_profile,
    map_license,
)
from license_tracker.db.models.catalog_product import CatalogProduct
from license_tracker.db.models.host import Host
from license_tracker.db.models.host_cpu_profile import HostCpuProfile
from license_tracker.db.models.host_entitlement import HostEntitlement
from license_tracker.db.models.license_agreement import LicenseAgreement
from license_tracker.db.models.processor_core_factor import ProcessorCoreFactor
from license_tracker.db.models.product_entitlement import ProductEntitlement
from license_tracker.domain.enums import CpuProfileSource, LicenseMetric
from license_tracker.models import (
    CatalogProductCreate,
    CatalogProductUpdate,
    CoreFactorCreate,
    CoreFactorUpdate,
    CpuProfileUpsert,
    HostCreate,
    HostProductAssign,
    HostUpdate,
    LicenseCreate,
    LicenseUpdate,
    ProductCreate,
    ProductUpdate,
)


def _utcnow() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


class Database(ABC):
    """Application database interface with dialect-specific drivers."""

    async def __aenter__(self) -> Self:
        """Open a connection for the request unit of work.

        Returns:
            Self: Connected database instance.
        """
        await self._open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        """Close the connection, rolling back on error.

        Args:
            exc_type (type[BaseException] | None): Exception type if raised.
            exc (BaseException | None): Exception instance if raised.
            tb (object): Traceback if raised.
        """
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            await self._close()

    @abstractmethod
    async def _open(self) -> None:
        """Open the underlying driver connection."""

    @abstractmethod
    async def _close(self) -> None:
        """Close the underlying driver connection."""

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the current transaction."""

    @abstractmethod
    async def _fetchall(
        self,
        sql: str,
        params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a query and return all rows as dictionaries.

        Args:
            sql (str): SQL statement with named binds.
            params (Mapping[str, Any] | None): Bind parameters.

        Returns:
            list[dict[str, Any]]: Result rows.
        """

    @abstractmethod
    async def _fetchone(
        self,
        sql: str,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a query and return the first row.

        Args:
            sql (str): SQL statement with named binds.
            params (Mapping[str, Any] | None): Bind parameters.

        Returns:
            dict[str, Any] | None: First row or None.
        """

    @abstractmethod
    async def _execute(
        self,
        sql: str,
        params: Mapping[str, Any] | None = None,
    ) -> None:
        """Execute a statement without returning rows.

        Args:
            sql (str): SQL statement with named binds.
            params (Mapping[str, Any] | None): Bind parameters.
        """

    @abstractmethod
    async def _executemany(
        self,
        sql: str,
        params_seq: Sequence[Mapping[str, Any]],
    ) -> None:
        """Execute a statement for each parameter mapping.

        Args:
            sql (str): SQL statement with named binds.
            params_seq (Sequence[Mapping[str, Any]]): Bind parameter rows.
        """

    @abstractmethod
    def _paginate(self, sql: str) -> str:
        """Append dialect-specific limit/offset clauses.

        Args:
            sql (str): Base SELECT statement.

        Returns:
            str: SQL including :limit and :offset binds.
        """

    @abstractmethod
    async def verify_connection(self) -> None:
        """Verify the database connection is active by executing a simple query."""

    # --- hosts ---

    @abstractmethod
    async def list_hosts(self, *, offset: int = 0, limit: int = 50) -> list[Host]:
        """List hosts with pagination.

        Args:
            offset (int): Row offset.
            limit (int): Maximum rows.

        Returns:
            list[Host]: Host records.
        """

    @abstractmethod
    async def get_host(self, host_id: uuid.UUID) -> Host | None:
        """Fetch a host by id.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            Host | None: Host if found.
        """

    @abstractmethod
    async def create_host(self, data: HostCreate) -> Host:
        """Create a host record.

        Args:
            data (HostCreate): Creation payload.

        Returns:
            Host: Persisted host.
        """

    @abstractmethod
    async def update_host(self, host_id: uuid.UUID, data: HostUpdate) -> Host | None:
        """Update a host record.

        Args:
            host_id (uuid.UUID): Host primary key.
            data (HostUpdate): Fields to update.

        Returns:
            Host | None: Updated host if found.
        """

    @abstractmethod
    async def delete_host(self, host_id: uuid.UUID) -> bool:
        """Delete a host and cascaded child rows.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            bool: True if a row was deleted.
        """

    # --- license agreements ---

    @abstractmethod
    async def list_licenses(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        renewal_within_days: int | None = None,
    ) -> list[LicenseAgreement]:
        """List license agreements with optional renewal window filter.

        Args:
            offset (int): Row offset for pagination.
            limit (int): Maximum rows to return.
            renewal_within_days (int | None): Only agreements renewing within N days.

        Returns:
            list[LicenseAgreement]: Matching license agreements with products.
        """

    @abstractmethod
    async def get_license(self, license_id: uuid.UUID) -> LicenseAgreement | None:
        """Fetch a license agreement by id with products.

        Args:
            license_id (uuid.UUID): Agreement primary key.

        Returns:
            LicenseAgreement | None: Agreement if found.
        """

    @abstractmethod
    async def create_license(self, data: LicenseCreate) -> LicenseAgreement:
        """Create a new license agreement.

        Args:
            data (LicenseCreate): Creation payload.

        Returns:
            LicenseAgreement: Persisted agreement.
        """

    @abstractmethod
    async def update_license(
        self,
        license_id: uuid.UUID,
        data: LicenseUpdate,
    ) -> LicenseAgreement | None:
        """Update an existing license agreement.

        Args:
            license_id (uuid.UUID): Agreement primary key.
            data (LicenseUpdate): Fields to update.

        Returns:
            LicenseAgreement | None: Updated agreement if found.
        """

    @abstractmethod
    async def delete_license(self, license_id: uuid.UUID) -> bool:
        """Delete a license agreement and its entitlements.

        Args:
            license_id (uuid.UUID): Agreement primary key.

        Returns:
            bool: True if a row was deleted.
        """

    async def _license_with_products(self, row: dict[str, Any]) -> LicenseAgreement:
        """Attach product entitlements to a license agreement row.

        Args:
            row (dict[str, Any]): license_agreements row.

        Returns:
            LicenseAgreement: Agreement with products populated.
        """
        products = await self.list_products(uuid.UUID(str(row["id"])))
        return map_license(row, products)

    # --- product entitlements ---

    @abstractmethod
    async def list_products(self, license_id: uuid.UUID) -> list[ProductEntitlement]:
        """List entitlements for a license agreement.

        Args:
            license_id (uuid.UUID): Parent agreement id.

        Returns:
            list[ProductEntitlement]: Product entitlements.
        """

    @abstractmethod
    async def list_all_products(self) -> list[ProductEntitlement]:
        """List all product entitlements.

        Returns:
            list[ProductEntitlement]: All product entitlement rows.
        """

    @abstractmethod
    async def get_product(self, product_id: uuid.UUID) -> ProductEntitlement | None:
        """Fetch a product entitlement by id.

        Args:
            product_id (uuid.UUID): Entitlement primary key.

        Returns:
            ProductEntitlement | None: Entitlement if found.
        """

    @abstractmethod
    async def create_product(
        self,
        license_id: uuid.UUID,
        data: ProductCreate,
    ) -> ProductEntitlement:
        """Create a product entitlement under an agreement.

        Args:
            license_id (uuid.UUID): Parent agreement id.
            data (ProductCreate): Creation payload.

        Returns:
            ProductEntitlement: Persisted entitlement.
        """

    @abstractmethod
    async def update_product(
        self,
        product_id: uuid.UUID,
        data: ProductUpdate,
    ) -> ProductEntitlement | None:
        """Update a product entitlement.

        Args:
            product_id (uuid.UUID): Entitlement primary key.
            data (ProductUpdate): Fields to update.

        Returns:
            ProductEntitlement | None: Updated entitlement if found.
        """

    @abstractmethod
    async def delete_product(self, product_id: uuid.UUID) -> bool:
        """Delete a product entitlement.

        Args:
            product_id (uuid.UUID): Entitlement primary key.

        Returns:
            bool: True if a row was deleted.
        """

    @abstractmethod
    async def product_exists_in_pool(
        self,
        product_name: str,
        option_name: str,
        metrics: Sequence[LicenseMetric],
    ) -> bool:
        """Return whether a product exists in the pool for the given metrics.

        Args:
            product_name (str): Product name.
            option_name (str): Normalized option name.
            metrics (Sequence[LicenseMetric]): Allowed metrics.

        Returns:
            bool: True when at least one entitlement matches.
        """

    # --- host entitlements ---

    @abstractmethod
    async def list_host_entitlements(self, host_id: uuid.UUID) -> list[HostEntitlement]:
        """List product licenses assigned to a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            list[HostEntitlement]: Assigned products ordered by product name.
        """

    @abstractmethod
    async def get_host_entitlement(
        self,
        host_id: uuid.UUID,
        assignment_id: uuid.UUID,
    ) -> HostEntitlement | None:
        """Fetch a host product assignment.

        Args:
            host_id (uuid.UUID): Host primary key.
            assignment_id (uuid.UUID): Assignment primary key.

        Returns:
            HostEntitlement | None: Assignment if found.
        """

    @abstractmethod
    async def find_host_entitlement(
        self,
        host_id: uuid.UUID,
        product_name: str,
        option_name: str,
    ) -> HostEntitlement | None:
        """Find an assignment by host and product identity.

        Args:
            host_id (uuid.UUID): Host primary key.
            product_name (str): Product name.
            option_name (str): Normalized option name.

        Returns:
            HostEntitlement | None: Assignment if found.
        """

    @abstractmethod
    async def create_host_entitlement(
        self,
        host_id: uuid.UUID,
        data: HostProductAssign,
        metric: LicenseMetric,
        option_name: str,
    ) -> HostEntitlement:
        """Create a host product assignment.

        Args:
            host_id (uuid.UUID): Host primary key.
            data (HostProductAssign): Assignment payload.
            metric (LicenseMetric): Metric derived from host license type.
            option_name (str): Normalized option name.

        Returns:
            HostEntitlement: Created assignment row.
        """

    @abstractmethod
    async def delete_host_entitlement(
        self,
        host_id: uuid.UUID,
        assignment_id: uuid.UUID,
    ) -> bool:
        """Remove a product assignment from a host.

        Args:
            host_id (uuid.UUID): Host primary key.
            assignment_id (uuid.UUID): Assignment primary key.

        Returns:
            bool: True if an assignment was removed.
        """

    @abstractmethod
    async def update_host_entitlement_metrics(
        self,
        host_id: uuid.UUID,
        metric: LicenseMetric,
    ) -> None:
        """Update assignment metrics for all products on a host.

        Args:
            host_id (uuid.UUID): Host primary key.
            metric (LicenseMetric): Target metric.
        """

    @abstractmethod
    async def list_host_entitlements_for_product(
        self,
        product_name: str,
        metrics: Sequence[LicenseMetric],
    ) -> list[HostEntitlement]:
        """List host assignments for a product and metric set.

        Args:
            product_name (str): Product name.
            metrics (Sequence[LicenseMetric]): Allowed metrics.

        Returns:
            list[HostEntitlement]: Matching assignments.
        """

    # --- catalog ---

    @abstractmethod
    async def list_catalog_products(
        self,
        *,
        search: str | None = None,
        category: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CatalogProduct]:
        """List catalog products with optional search and category filters.

        Args:
            search (str | None): Case-insensitive search across product and option names.
            category (str | None): Exact category filter.
            offset (int): Pagination offset.
            limit (int): Maximum rows to return.

        Returns:
            list[CatalogProduct]: Matching catalog products.
        """

    @abstractmethod
    async def list_catalog_categories(self) -> list[str]:
        """Return distinct catalog categories.

        Returns:
            list[str]: Sorted category names.
        """

    @abstractmethod
    async def get_catalog_product(self, product_id: uuid.UUID) -> CatalogProduct | None:
        """Fetch a catalog product by id.

        Args:
            product_id (uuid.UUID): Catalog product primary key.

        Returns:
            CatalogProduct | None: Product if found.
        """

    @abstractmethod
    async def create_catalog_product(self, data: CatalogProductCreate) -> CatalogProduct:
        """Create a catalog product row.

        Args:
            data (CatalogProductCreate): Creation payload.

        Returns:
            CatalogProduct: Persisted row.
        """

    @abstractmethod
    async def update_catalog_product(
        self,
        product_id: uuid.UUID,
        data: CatalogProductUpdate,
    ) -> CatalogProduct | None:
        """Update a catalog product row.

        Args:
            product_id (uuid.UUID): Catalog product primary key.
            data (CatalogProductUpdate): Fields to update.

        Returns:
            CatalogProduct | None: Updated row if found.
        """

    @abstractmethod
    async def delete_catalog_product(self, product_id: uuid.UUID) -> bool:
        """Delete a catalog product row.

        Args:
            product_id (uuid.UUID): Catalog product primary key.

        Returns:
            bool: True if a row was deleted.
        """

    @abstractmethod
    async def count_catalog_products(self) -> int:
        """Return the number of catalog product rows.

        Returns:
            int: Catalog product count.
        """

    @abstractmethod
    async def insert_catalog_products(self, rows: Sequence[Mapping[str, Any]]) -> None:
        """Bulk-insert catalog product rows.

        Args:
            rows (Sequence[Mapping[str, Any]]): Catalog rows including ids and timestamps.
        """

    # --- core factors ---

    @abstractmethod
    async def list_core_factors(self) -> list[ProcessorCoreFactor]:
        """List all processor core factor rows.

        Returns:
            list[ProcessorCoreFactor]: Core factor rows ordered by priority.
        """

    @abstractmethod
    async def get_core_factor(self, factor_id: uuid.UUID) -> ProcessorCoreFactor | None:
        """Fetch a processor core factor by id.

        Args:
            factor_id (uuid.UUID): Core factor primary key.

        Returns:
            ProcessorCoreFactor | None: Row if found.
        """

    @abstractmethod
    async def create_core_factor(self, data: CoreFactorCreate) -> ProcessorCoreFactor:
        """Create a processor core factor row.

        Args:
            data (CoreFactorCreate): Creation payload.

        Returns:
            ProcessorCoreFactor: Persisted row.
        """

    @abstractmethod
    async def update_core_factor(
        self,
        factor_id: uuid.UUID,
        data: CoreFactorUpdate,
    ) -> ProcessorCoreFactor | None:
        """Update a processor core factor row.

        Args:
            factor_id (uuid.UUID): Core factor primary key.
            data (CoreFactorUpdate): Fields to update.

        Returns:
            ProcessorCoreFactor | None: Updated row if found.
        """

    @abstractmethod
    async def delete_core_factor(self, factor_id: uuid.UUID) -> bool:
        """Delete a processor core factor row.

        Args:
            factor_id (uuid.UUID): Core factor primary key.

        Returns:
            bool: True if a row was deleted.
        """

    @abstractmethod
    async def count_core_factors(self) -> int:
        """Return the number of processor core factor rows.

        Returns:
            int: Core factor count.
        """

    @abstractmethod
    async def insert_core_factors(self, rows: Sequence[Mapping[str, Any]]) -> None:
        """Bulk-insert processor core factor rows.

        Args:
            rows (Sequence[Mapping[str, Any]]): Core factor rows including ids and timestamps.
        """

    # --- CPU profiles ---

    @abstractmethod
    async def get_latest_cpu_profile(self, host_id: uuid.UUID) -> HostCpuProfile | None:
        """Return the latest CPU profile for a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            HostCpuProfile | None: Latest profile if any exist.
        """

    @abstractmethod
    async def list_cpu_profiles(self, host_id: uuid.UUID) -> list[HostCpuProfile]:
        """Return all CPU profile snapshots for a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            list[HostCpuProfile]: Profiles newest first.
        """

    @abstractmethod
    async def create_cpu_profile(
        self,
        host_id: uuid.UUID,
        data: CpuProfileUpsert,
        *,
        source: CpuProfileSource,
        core_factor: float | None,
        core_factor_id: uuid.UUID | None,
        logical_processor_count: int,
    ) -> HostCpuProfile:
        """Append a new CPU profile snapshot for a host.

        Args:
            host_id (uuid.UUID): Host primary key.
            data (CpuProfileUpsert): CPU inventory values.
            source (CpuProfileSource): How the data was collected.
            core_factor (float | None): Resolved core factor value.
            core_factor_id (uuid.UUID | None): Matched core factor id.
            logical_processor_count (int): Logical processor count.

        Returns:
            HostCpuProfile: Persisted profile row with matched factor.
        """

    async def _cpu_profile_with_factor(self, row: dict[str, Any]) -> HostCpuProfile:
        """Attach matched core factor to a CPU profile row.

        Args:
            row (dict[str, Any]): host_cpu_profiles row.

        Returns:
            HostCpuProfile: Profile with matched_core_factor populated when present.
        """
        factor_id = row.get("core_factor_id") or row.get("CORE_FACTOR_ID")
        matched = None
        if factor_id is not None:
            matched = await self.get_core_factor(uuid.UUID(str(factor_id)))
        return map_cpu_profile(row, matched)

    # --- aggregates ---

    @abstractmethod
    async def count_licenses(self) -> int:
        """Return the number of license agreements.

        Returns:
            int: Agreement count.
        """

    @abstractmethod
    async def count_products(self) -> int:
        """Return the number of product entitlements.

        Returns:
            int: Product entitlement count.
        """

    @abstractmethod
    async def count_hosts(self) -> int:
        """Return the number of hosts.

        Returns:
            int: Host count.
        """

    @abstractmethod
    async def count_renewals_within(self, within_days: int) -> int:
        """Count agreements renewing within a day window.

        Args:
            within_days (int): Inclusive day window from today.

        Returns:
            int: Matching agreement count.
        """

    @abstractmethod
    async def list_host_ids(self) -> list[uuid.UUID]:
        """Return all host primary keys.

        Returns:
            list[uuid.UUID]: Host ids.
        """

    @abstractmethod
    async def total_physical_cores(self) -> int:
        """Sum physical cores from the latest profile per host.

        Returns:
            int: Total physical cores.
        """

    @staticmethod
    def _in_clause(
        column: str,
        values: Sequence[Any],
        prefix: str,
    ) -> tuple[str, dict[str, Any]]:
        """Build a named-parameter IN clause.

        Args:
            column (str): Column name.
            values (Sequence[Any]): Values to bind.
            prefix (str): Parameter name prefix.

        Returns:
            tuple[str, dict[str, Any]]: SQL fragment and bind parameters.
        """
        params: dict[str, Any] = {}
        placeholders: list[str] = []
        for index, value in enumerate(values):
            key = f"{prefix}_{index}"
            placeholders.append(f":{key}")
            params[key] = value
        return f"{column} IN ({', '.join(placeholders)})", params

    @staticmethod
    def prepare_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
        """Normalize bind parameters for driver execution.

        Args:
            params (Mapping[str, Any] | None): Named bind parameters.

        Returns:
            dict[str, Any]: Driver-friendly parameters.
        """
        if not params:
            return {}
        return bind_params(dict(params))
