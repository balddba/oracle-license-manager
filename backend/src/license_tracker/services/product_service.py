"""Product entitlement service."""

from __future__ import annotations

import uuid

from license_tracker.db.models.product_entitlement import ProductEntitlement
from license_tracker.db.queries.base import Database
from license_tracker.models import ProductCreate, ProductUpdate


class ProductService:
    """Data access for product entitlements."""

    def __init__(self, database: Database) -> None:
        """Initialize the service.

        Args:
            database (Database): Database backend.
        """
        self._db = database

    async def get_products(self, license_id: uuid.UUID) -> list[ProductEntitlement]:
        """List entitlements for a license agreement.

        Args:
            license_id (uuid.UUID): Parent agreement id.

        Returns:
            list[ProductEntitlement]: Product entitlements.
        """
        return await self._db.list_products(license_id)

    async def get_product(self, product_id: uuid.UUID) -> ProductEntitlement | None:
        """Fetch a product entitlement by id.

        Args:
            product_id (uuid.UUID): Entitlement primary key.

        Returns:
            ProductEntitlement | None: Entitlement if found.
        """
        return await self._db.get_product(product_id)

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
        return await self._db.create_product(license_id, data)

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
        return await self._db.update_product(product_id, data)

    async def delete_product(self, product_id: uuid.UUID) -> bool:
        """Delete a product entitlement.

        Args:
            product_id (uuid.UUID): Entitlement primary key.

        Returns:
            bool: True if a row was deleted.
        """
        return await self._db.delete_product(product_id)
