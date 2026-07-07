"""Catalog product service."""

from __future__ import annotations

import uuid

from license_tracker.db.models.catalog_product import CatalogProduct
from license_tracker.db.queries.base import Database
from license_tracker.models import CatalogProductCreate, CatalogProductUpdate


class CatalogService:
    """Data access for Oracle catalog products."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database

    async def list_products(
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
        return await self._db.list_catalog_products(
            search=search,
            category=category,
            offset=offset,
            limit=limit,
        )

    async def list_categories(self) -> list[str]:
        """Return distinct catalog categories.

        Returns:
            list[str]: Sorted category names.
        """
        return await self._db.list_catalog_categories()

    async def get_product(self, product_id: uuid.UUID) -> CatalogProduct | None:
        """Fetch a catalog product by id.

        Args:
            product_id (uuid.UUID): Catalog product primary key.

        Returns:
            CatalogProduct | None: Product if found.
        """
        return await self._db.get_catalog_product(product_id)

    async def create_product(self, data: CatalogProductCreate) -> CatalogProduct:
        """Create a catalog product row.

        Args:
            data (CatalogProductCreate): Creation payload.

        Returns:
            CatalogProduct: Persisted row.
        """
        return await self._db.create_catalog_product(data)

    async def update_product(
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
        return await self._db.update_catalog_product(product_id, data)

    async def delete_product(self, product_id: uuid.UUID) -> bool:
        """Delete a catalog product row.

        Args:
            product_id (uuid.UUID): Catalog product primary key.

        Returns:
            bool: True if a row was deleted.
        """
        return await self._db.delete_catalog_product(product_id)
