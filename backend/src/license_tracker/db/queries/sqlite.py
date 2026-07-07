"""SQLite database backend using aiosqlite."""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any

import aiosqlite

from license_tracker.db.mappers import (
    map_catalog_product,
    map_core_factor,
    map_host,
    map_host_entitlement,
    map_product,
)
from license_tracker.db.models.catalog_product import CatalogProduct
from license_tracker.db.models.host import Host
from license_tracker.db.models.host_cpu_profile import HostCpuProfile
from license_tracker.db.models.host_entitlement import HostEntitlement
from license_tracker.db.models.license_agreement import LicenseAgreement
from license_tracker.db.models.processor_core_factor import ProcessorCoreFactor
from license_tracker.db.models.product_entitlement import ProductEntitlement
from license_tracker.db.queries.base import Database
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

# Register sqlite3 adapters for date and datetime to prevent deprecation warnings in Python 3.12+
sqlite3.register_adapter(date, lambda val: val.isoformat())
sqlite3.register_adapter(datetime, lambda val: val.isoformat())


def _utcnow() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


class SqliteDatabase(Database):
    """SQLite implementation of the Database query interface."""

    def __init__(self, path: str) -> None:
        """Initialize the SQLite backend.

        Args:
            path (str): SQLite database file path or ``:memory:``.
        """
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def _open(self) -> None:
        """Open an aiosqlite connection with foreign keys enabled."""
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")

    async def _close(self) -> None:
        """Close the aiosqlite connection."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._conn is not None:
            await self._conn.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        if self._conn is not None:
            await self._conn.rollback()

    def _paginate(self, sql: str) -> str:
        """Append SQLite LIMIT/OFFSET clauses.

        Args:
            sql (str): Base SELECT statement.

        Returns:
            str: SQL including :limit and :offset binds.
        """
        return f"{sql.rstrip().rstrip(';')} LIMIT :limit OFFSET :offset"

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
        conn = self._require_conn()
        cursor = await conn.execute(sql, self.prepare_params(params))
        try:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await cursor.close()

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
        conn = self._require_conn()
        cursor = await conn.execute(sql, self.prepare_params(params))
        try:
            row = await cursor.fetchone()
            return dict(row) if row is not None else None
        finally:
            await cursor.close()

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
        conn = self._require_conn()
        await conn.execute(sql, self.prepare_params(params))

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
        conn = self._require_conn()
        await conn.executemany(
            sql,
            [self.prepare_params(params) for params in params_seq],
        )

    def _require_conn(self) -> aiosqlite.Connection:
        """Return the open connection or raise.

        Returns:
            aiosqlite.Connection: Active connection.

        Raises:
            RuntimeError: If the connection is not open.
        """
        if self._conn is None:
            raise RuntimeError("SqliteDatabase connection is not open")
        return self._conn

    async def verify_connection(self) -> None:
        """Verify the database connection is active by executing a simple query."""
        await self._fetchone("SELECT 1")

    # --- hosts ---

    async def list_hosts(self, *, offset: int = 0, limit: int = 50) -> list[Host]:
        """List hosts with pagination.

        Args:
            offset (int): Row offset.
            limit (int): Maximum rows.

        Returns:
            list[Host]: Host records.
        """
        sql = self._paginate(
            "SELECT * FROM hosts ORDER BY hostname",
        )
        rows = await self._fetchall(sql, {"offset": offset, "limit": limit})
        return [map_host(row) for row in rows]

    async def get_host(self, host_id: uuid.UUID) -> Host | None:
        """Fetch a host by id.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            Host | None: Host if found.
        """
        row = await self._fetchone("SELECT * FROM hosts WHERE id = :id", {"id": host_id})
        return map_host(row) if row is not None else None

    async def create_host(self, data: HostCreate) -> Host:
        """Create a host record.

        Args:
            data (HostCreate): Creation payload.

        Returns:
            Host: Persisted host.
        """
        host = Host(**data.model_dump())
        await self._execute(
            """
            INSERT INTO hosts (
                id, hostname, fqdn, ip_address, environment, license_type,
                named_users_required, os_name, notes, ssh_enabled, ssh_port, ssh_user,
                created_at, updated_at
            ) VALUES (
                :id, :hostname, :fqdn, :ip_address, :environment, :license_type,
                :named_users_required, :os_name, :notes, :ssh_enabled, :ssh_port, :ssh_user,
                :created_at, :updated_at
            )
            """,
            host.model_dump(),
        )
        return host

    async def update_host(self, host_id: uuid.UUID, data: HostUpdate) -> Host | None:
        """Update a host record.

        Args:
            host_id (uuid.UUID): Host primary key.
            data (HostUpdate): Fields to update.

        Returns:
            Host | None: Updated host if found.
        """
        host = await self.get_host(host_id)
        if host is None:
            return None
        updates = data.model_dump(exclude_unset=True)
        updated = host.model_copy(update={**updates, "updated_at": _utcnow()})
        await self._execute(
            """
            UPDATE hosts SET
                hostname = :hostname,
                fqdn = :fqdn,
                ip_address = :ip_address,
                environment = :environment,
                license_type = :license_type,
                named_users_required = :named_users_required,
                os_name = :os_name,
                notes = :notes,
                ssh_enabled = :ssh_enabled,
                ssh_port = :ssh_port,
                ssh_user = :ssh_user,
                updated_at = :updated_at
            WHERE id = :id
            """,
            updated.model_dump(),
        )
        return updated

    async def delete_host(self, host_id: uuid.UUID) -> bool:
        """Delete a host and cascaded child rows.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            bool: True if a row was deleted.
        """
        host = await self.get_host(host_id)
        if host is None:
            return False
        await self._execute("DELETE FROM hosts WHERE id = :id", {"id": host_id})
        return True

    # --- license agreements ---

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
        sql = "SELECT * FROM license_agreements"
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if renewal_within_days is not None:
            today = date.today()
            cutoff = today + timedelta(days=renewal_within_days)
            sql += """
                WHERE renewal_date IS NOT NULL
                  AND renewal_date <= :cutoff
                  AND renewal_date >= :today
            """
            params["cutoff"] = cutoff
            params["today"] = today
        sql += " ORDER BY csi"
        rows = await self._fetchall(self._paginate(sql), params)
        return [await self._license_with_products(row) for row in rows]

    async def get_license(self, license_id: uuid.UUID) -> LicenseAgreement | None:
        """Fetch a license agreement by id with products.

        Args:
            license_id (uuid.UUID): Agreement primary key.

        Returns:
            LicenseAgreement | None: Agreement if found.
        """
        row = await self._fetchone(
            "SELECT * FROM license_agreements WHERE id = :id",
            {"id": license_id},
        )
        if row is None:
            return None
        return await self._license_with_products(row)

    async def create_license(self, data: LicenseCreate) -> LicenseAgreement:
        """Create a new license agreement.

        Args:
            data (LicenseCreate): Creation payload.

        Returns:
            LicenseAgreement: Persisted agreement.
        """
        agreement = LicenseAgreement(**data.model_dump())
        await self._execute(
            """
            INSERT INTO license_agreements (
                id, csi, customer_name, support_level, start_date, renewal_date,
                status, notes, created_at, updated_at
            ) VALUES (
                :id, :csi, :customer_name, :support_level, :start_date, :renewal_date,
                :status, :notes, :created_at, :updated_at
            )
            """,
            agreement.model_dump(exclude={"products"}),
        )
        return agreement

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
        agreement = await self.get_license(license_id)
        if agreement is None:
            return None
        updates = data.model_dump(exclude_unset=True)
        updated = agreement.model_copy(update={**updates, "updated_at": _utcnow()})
        await self._execute(
            """
            UPDATE license_agreements SET
                csi = :csi,
                customer_name = :customer_name,
                support_level = :support_level,
                start_date = :start_date,
                renewal_date = :renewal_date,
                status = :status,
                notes = :notes,
                updated_at = :updated_at
            WHERE id = :id
            """,
            updated.model_dump(exclude={"products"}),
        )
        return updated

    async def delete_license(self, license_id: uuid.UUID) -> bool:
        """Delete a license agreement and its entitlements.

        Args:
            license_id (uuid.UUID): Agreement primary key.

        Returns:
            bool: True if a row was deleted.
        """
        agreement = await self.get_license(license_id)
        if agreement is None:
            return False
        await self._execute("DELETE FROM license_agreements WHERE id = :id", {"id": license_id})
        return True

    # --- product entitlements ---

    async def list_products(self, license_id: uuid.UUID) -> list[ProductEntitlement]:
        """List entitlements for a license agreement.

        Args:
            license_id (uuid.UUID): Parent agreement id.

        Returns:
            list[ProductEntitlement]: Product entitlements.
        """
        rows = await self._fetchall(
            """
            SELECT * FROM product_entitlements
            WHERE agreement_id = :agreement_id
            ORDER BY product_name
            """,
            {"agreement_id": license_id},
        )
        return [map_product(row) for row in rows]

    async def list_all_products(self) -> list[ProductEntitlement]:
        """List all product entitlements.

        Returns:
            list[ProductEntitlement]: All product entitlement rows.
        """
        rows = await self._fetchall(
            """
            SELECT * FROM product_entitlements
            ORDER BY product_name, option_name, metric
            """
        )
        return [map_product(row) for row in rows]

    async def get_product(self, product_id: uuid.UUID) -> ProductEntitlement | None:
        """Fetch a product entitlement by id.

        Args:
            product_id (uuid.UUID): Entitlement primary key.

        Returns:
            ProductEntitlement | None: Entitlement if found.
        """
        row = await self._fetchone(
            "SELECT * FROM product_entitlements WHERE id = :id",
            {"id": product_id},
        )
        return map_product(row) if row is not None else None

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
        product = ProductEntitlement(agreement_id=license_id, **data.model_dump())
        await self._execute(
            """
            INSERT INTO product_entitlements (
                id, agreement_id, product_name, option_name, metric, quantity,
                notes, created_at, updated_at
            ) VALUES (
                :id, :agreement_id, :product_name, :option_name, :metric, :quantity,
                :notes, :created_at, :updated_at
            )
            """,
            product.model_dump(),
        )
        return product

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
        product = await self.get_product(product_id)
        if product is None:
            return None
        updates = data.model_dump(exclude_unset=True)
        updated = product.model_copy(update={**updates, "updated_at": _utcnow()})
        await self._execute(
            """
            UPDATE product_entitlements SET
                product_name = :product_name,
                option_name = :option_name,
                metric = :metric,
                quantity = :quantity,
                notes = :notes,
                updated_at = :updated_at
            WHERE id = :id
            """,
            updated.model_dump(),
        )
        return updated

    async def delete_product(self, product_id: uuid.UUID) -> bool:
        """Delete a product entitlement.

        Args:
            product_id (uuid.UUID): Entitlement primary key.

        Returns:
            bool: True if a row was deleted.
        """
        product = await self.get_product(product_id)
        if product is None:
            return False
        await self._execute("DELETE FROM product_entitlements WHERE id = :id", {"id": product_id})
        return True

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
        if not metrics:
            return False
        clause, params = self._in_clause("metric", list(metrics), "metric")
        params["product_name"] = product_name
        rows = await self._fetchall(
            f"""
            SELECT option_name FROM product_entitlements
            WHERE product_name = :product_name AND {clause}
            """,
            params,
        )
        for row in rows:
            stored = row.get("option_name") or row.get("OPTION_NAME") or ""
            if (stored or "") == option_name:
                return True
        return False

    # --- host entitlements ---

    async def list_host_entitlements(self, host_id: uuid.UUID) -> list[HostEntitlement]:
        """List product licenses assigned to a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            list[HostEntitlement]: Assigned products ordered by product name.
        """
        rows = await self._fetchall(
            """
            SELECT * FROM host_entitlements
            WHERE host_id = :host_id
            ORDER BY product_name, option_name
            """,
            {"host_id": host_id},
        )
        return [map_host_entitlement(row) for row in rows]

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
        row = await self._fetchone(
            """
            SELECT * FROM host_entitlements
            WHERE host_id = :host_id AND id = :id
            """,
            {"host_id": host_id, "id": assignment_id},
        )
        return map_host_entitlement(row) if row is not None else None

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
        row = await self._fetchone(
            """
            SELECT * FROM host_entitlements
            WHERE host_id = :host_id
              AND product_name = :product_name
              AND option_name = :option_name
            """,
            {
                "host_id": host_id,
                "product_name": product_name,
                "option_name": option_name,
            },
        )
        return map_host_entitlement(row) if row is not None else None

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
        row = HostEntitlement(
            host_id=host_id,
            product_name=data.product_name,
            option_name=option_name,
            metric=metric,
            notes=data.notes,
        )
        await self._execute(
            """
            INSERT INTO host_entitlements (
                id, host_id, product_name, option_name, metric, notes,
                created_at, updated_at
            ) VALUES (
                :id, :host_id, :product_name, :option_name, :metric, :notes,
                :created_at, :updated_at
            )
            """,
            row.model_dump(),
        )
        return row

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
        row = await self.get_host_entitlement(host_id, assignment_id)
        if row is None:
            return False
        await self._execute(
            "DELETE FROM host_entitlements WHERE id = :id",
            {"id": assignment_id},
        )
        return True

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
        await self._execute(
            """
            UPDATE host_entitlements
            SET metric = :metric, updated_at = :updated_at
            WHERE host_id = :host_id
            """,
            {"metric": metric, "updated_at": _utcnow(), "host_id": host_id},
        )

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
        if not metrics:
            return []
        clause, params = self._in_clause("metric", list(metrics), "metric")
        params["product_name"] = product_name
        rows = await self._fetchall(
            f"""
            SELECT * FROM host_entitlements
            WHERE product_name = :product_name AND {clause}
            """,
            params,
        )
        return [map_host_entitlement(row) for row in rows]

    # --- catalog ---

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
        sql = "SELECT * FROM catalog_products WHERE 1 = 1"
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if category:
            sql += " AND category = :category"
            params["category"] = category
        if search:
            pattern = f"%{search.strip().lower()}%"
            sql += """
                AND (
                    LOWER(product_name) LIKE :pattern
                    OR LOWER(COALESCE(option_name, '')) LIKE :pattern
                )
            """
            params["pattern"] = pattern
        sql += " ORDER BY category, product_name, option_name"
        rows = await self._fetchall(self._paginate(sql), params)
        return [map_catalog_product(row) for row in rows]

    async def list_catalog_categories(self) -> list[str]:
        """Return distinct catalog categories.

        Returns:
            list[str]: Sorted category names.
        """
        rows = await self._fetchall(
            """
            SELECT DISTINCT category FROM catalog_products
            ORDER BY category
            """
        )
        return [str(row.get("category") or row.get("CATEGORY")) for row in rows]

    async def get_catalog_product(self, product_id: uuid.UUID) -> CatalogProduct | None:
        """Fetch a catalog product by id.

        Args:
            product_id (uuid.UUID): Catalog product primary key.

        Returns:
            CatalogProduct | None: Product if found.
        """
        row = await self._fetchone(
            "SELECT * FROM catalog_products WHERE id = :id",
            {"id": product_id},
        )
        return map_catalog_product(row) if row is not None else None

    async def create_catalog_product(self, data: CatalogProductCreate) -> CatalogProduct:
        """Create a catalog product row.

        Args:
            data (CatalogProductCreate): Creation payload.

        Returns:
            CatalogProduct: Persisted row.
        """
        row = CatalogProduct(**data.model_dump())
        await self._execute(
            """
            INSERT INTO catalog_products (
                id, price_list_id, category, product_name, option_name,
                list_price_nup_usd, list_price_nup_support_usd,
                list_price_processor_usd, list_price_processor_support_usd,
                supports_nup, supports_processor, created_at, updated_at
            ) VALUES (
                :id, :price_list_id, :category, :product_name, :option_name,
                :list_price_nup_usd, :list_price_nup_support_usd,
                :list_price_processor_usd, :list_price_processor_support_usd,
                :supports_nup, :supports_processor, :created_at, :updated_at
            )
            """,
            row.model_dump(),
        )
        return row

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
        row = await self.get_catalog_product(product_id)
        if row is None:
            return None
        updates = data.model_dump(exclude_unset=True)
        updated = row.model_copy(update={**updates, "updated_at": _utcnow()})
        await self._execute(
            """
            UPDATE catalog_products SET
                price_list_id = :price_list_id,
                category = :category,
                product_name = :product_name,
                option_name = :option_name,
                list_price_nup_usd = :list_price_nup_usd,
                list_price_nup_support_usd = :list_price_nup_support_usd,
                list_price_processor_usd = :list_price_processor_usd,
                list_price_processor_support_usd = :list_price_processor_support_usd,
                supports_nup = :supports_nup,
                supports_processor = :supports_processor,
                updated_at = :updated_at
            WHERE id = :id
            """,
            updated.model_dump(),
        )
        return updated

    async def delete_catalog_product(self, product_id: uuid.UUID) -> bool:
        """Delete a catalog product row.

        Args:
            product_id (uuid.UUID): Catalog product primary key.

        Returns:
            bool: True if a row was deleted.
        """
        row = await self.get_catalog_product(product_id)
        if row is None:
            return False
        await self._execute("DELETE FROM catalog_products WHERE id = :id", {"id": product_id})
        return True

    async def count_catalog_products(self) -> int:
        """Return the number of catalog product rows.

        Returns:
            int: Catalog product count.
        """
        row = await self._fetchone("SELECT COUNT(*) AS cnt FROM catalog_products")
        return int((row or {}).get("cnt") or (row or {}).get("CNT") or 0)

    async def insert_catalog_products(self, rows: Sequence[Mapping[str, Any]]) -> None:
        """Bulk-insert catalog product rows.

        Args:
            rows (Sequence[Mapping[str, Any]]): Catalog rows including ids and timestamps.
        """
        if not rows:
            return
        await self._executemany(
            """
            INSERT INTO catalog_products (
                id, price_list_id, category, product_name, option_name,
                list_price_nup_usd, list_price_nup_support_usd,
                list_price_processor_usd, list_price_processor_support_usd,
                supports_nup, supports_processor, created_at, updated_at
            ) VALUES (
                :id, :price_list_id, :category, :product_name, :option_name,
                :list_price_nup_usd, :list_price_nup_support_usd,
                :list_price_processor_usd, :list_price_processor_support_usd,
                :supports_nup, :supports_processor, :created_at, :updated_at
            )
            """,
            list(rows),
        )

    # --- core factors ---

    async def list_core_factors(self) -> list[ProcessorCoreFactor]:
        """List all processor core factor rows.

        Returns:
            list[ProcessorCoreFactor]: Core factor rows ordered by priority.
        """
        rows = await self._fetchall(
            """
            SELECT * FROM processor_core_factors
            ORDER BY priority DESC, name
            """
        )
        return [map_core_factor(row) for row in rows]

    async def get_core_factor(self, factor_id: uuid.UUID) -> ProcessorCoreFactor | None:
        """Fetch a processor core factor by id.

        Args:
            factor_id (uuid.UUID): Core factor primary key.

        Returns:
            ProcessorCoreFactor | None: Row if found.
        """
        row = await self._fetchone(
            "SELECT * FROM processor_core_factors WHERE id = :id",
            {"id": factor_id},
        )
        return map_core_factor(row) if row is not None else None

    async def create_core_factor(self, data: CoreFactorCreate) -> ProcessorCoreFactor:
        """Create a processor core factor row.

        Args:
            data (CoreFactorCreate): Creation payload.

        Returns:
            ProcessorCoreFactor: Persisted row.
        """
        row = ProcessorCoreFactor(**data.model_dump())
        await self._execute(
            """
            INSERT INTO processor_core_factors (
                id, name, match_pattern, core_factor, priority, is_default,
                notes, created_at, updated_at
            ) VALUES (
                :id, :name, :match_pattern, :core_factor, :priority, :is_default,
                :notes, :created_at, :updated_at
            )
            """,
            row.model_dump(),
        )
        return row

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
        row = await self.get_core_factor(factor_id)
        if row is None:
            return None
        updates = data.model_dump(exclude_unset=True)
        updated = row.model_copy(update={**updates, "updated_at": _utcnow()})
        await self._execute(
            """
            UPDATE processor_core_factors SET
                name = :name,
                match_pattern = :match_pattern,
                core_factor = :core_factor,
                priority = :priority,
                is_default = :is_default,
                notes = :notes,
                updated_at = :updated_at
            WHERE id = :id
            """,
            updated.model_dump(),
        )
        return updated

    async def delete_core_factor(self, factor_id: uuid.UUID) -> bool:
        """Delete a processor core factor row.

        Args:
            factor_id (uuid.UUID): Core factor primary key.

        Returns:
            bool: True if a row was deleted.
        """
        row = await self.get_core_factor(factor_id)
        if row is None:
            return False
        await self._execute(
            "DELETE FROM processor_core_factors WHERE id = :id",
            {"id": factor_id},
        )
        return True

    async def count_core_factors(self) -> int:
        """Return the number of processor core factor rows.

        Returns:
            int: Core factor count.
        """
        row = await self._fetchone("SELECT COUNT(*) AS cnt FROM processor_core_factors")
        return int((row or {}).get("cnt") or (row or {}).get("CNT") or 0)

    async def insert_core_factors(self, rows: Sequence[Mapping[str, Any]]) -> None:
        """Bulk-insert processor core factor rows.

        Args:
            rows (Sequence[Mapping[str, Any]]): Core factor rows including ids and timestamps.
        """
        if not rows:
            return
        await self._executemany(
            """
            INSERT INTO processor_core_factors (
                id, name, match_pattern, core_factor, priority, is_default,
                notes, created_at, updated_at
            ) VALUES (
                :id, :name, :match_pattern, :core_factor, :priority, :is_default,
                :notes, :created_at, :updated_at
            )
            """,
            list(rows),
        )

    # --- CPU profiles ---

    async def get_latest_cpu_profile(self, host_id: uuid.UUID) -> HostCpuProfile | None:
        """Return the latest CPU profile for a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            HostCpuProfile | None: Latest profile if any exist.
        """
        sql = self._paginate(
            """
            SELECT * FROM host_cpu_profiles
            WHERE host_id = :host_id
            ORDER BY collected_at DESC
            """
        )
        row = await self._fetchone(sql, {"host_id": host_id, "offset": 0, "limit": 1})
        if row is None:
            return None
        return await self._cpu_profile_with_factor(row)

    async def list_cpu_profiles(self, host_id: uuid.UUID) -> list[HostCpuProfile]:
        """Return all CPU profile snapshots for a host.

        Args:
            host_id (uuid.UUID): Host primary key.

        Returns:
            list[HostCpuProfile]: Profiles newest first.
        """
        rows = await self._fetchall(
            """
            SELECT * FROM host_cpu_profiles
            WHERE host_id = :host_id
            ORDER BY collected_at DESC
            """,
            {"host_id": host_id},
        )
        return [await self._cpu_profile_with_factor(row) for row in rows]

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
        profile = HostCpuProfile(
            host_id=host_id,
            cpu_model=data.cpu_model,
            core_factor=core_factor,
            core_factor_id=core_factor_id,
            socket_count=data.socket_count,
            cores_per_socket=data.cores_per_socket,
            threads_per_core=data.threads_per_core,
            logical_processor_count=logical_processor_count,
            source=source,
            collected_at=_utcnow(),
        )
        await self._execute(
            """
            INSERT INTO host_cpu_profiles (
                id, host_id, cpu_model, core_factor, core_factor_id, socket_count,
                cores_per_socket, threads_per_core, logical_processor_count,
                source, collected_at, created_at
            ) VALUES (
                :id, :host_id, :cpu_model, :core_factor, :core_factor_id, :socket_count,
                :cores_per_socket, :threads_per_core, :logical_processor_count,
                :source, :collected_at, :created_at
            )
            """,
            profile.model_dump(
                exclude={"matched_core_factor", "physical_cores", "processor_licenses_required"}
            ),
        )
        row = await self._fetchone(
            "SELECT * FROM host_cpu_profiles WHERE id = :id",
            {"id": profile.id},
        )
        assert row is not None
        return await self._cpu_profile_with_factor(row)

    # --- aggregates ---

    async def count_licenses(self) -> int:
        """Return the number of license agreements.

        Returns:
            int: Agreement count.
        """
        row = await self._fetchone("SELECT COUNT(*) AS cnt FROM license_agreements")
        return int((row or {}).get("cnt") or (row or {}).get("CNT") or 0)

    async def count_products(self) -> int:
        """Return the number of product entitlements.

        Returns:
            int: Product entitlement count.
        """
        row = await self._fetchone("SELECT COUNT(*) AS cnt FROM product_entitlements")
        return int((row or {}).get("cnt") or (row or {}).get("CNT") or 0)

    async def count_hosts(self) -> int:
        """Return the number of hosts.

        Returns:
            int: Host count.
        """
        row = await self._fetchone("SELECT COUNT(*) AS cnt FROM hosts")
        return int((row or {}).get("cnt") or (row or {}).get("CNT") or 0)

    async def count_renewals_within(self, within_days: int) -> int:
        """Count agreements renewing within a day window.

        Args:
            within_days (int): Inclusive day window from today.

        Returns:
            int: Matching agreement count.
        """
        today = date.today()
        cutoff = today + timedelta(days=within_days)
        row = await self._fetchone(
            """
            SELECT COUNT(*) AS cnt FROM license_agreements
            WHERE renewal_date IS NOT NULL
              AND renewal_date >= :today
              AND renewal_date <= :cutoff
            """,
            {"today": today, "cutoff": cutoff},
        )
        return int((row or {}).get("cnt") or (row or {}).get("CNT") or 0)

    async def list_host_ids(self) -> list[uuid.UUID]:
        """Return all host primary keys.

        Returns:
            list[uuid.UUID]: Host ids.
        """
        rows = await self._fetchall("SELECT id FROM hosts")
        return [uuid.UUID(str(row.get("id") or row.get("ID"))) for row in rows]

    async def total_physical_cores(self) -> int:
        """Sum physical cores from the latest profile per host.

        Returns:
            int: Total physical cores.
        """
        total = 0
        for host_id in await self.list_host_ids():
            profile = await self.get_latest_cpu_profile(host_id)
            if profile is not None:
                total += profile.physical_cores
        return total
