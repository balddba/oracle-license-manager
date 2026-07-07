"""License list read model."""

from __future__ import annotations

from pydantic import Field

from license_tracker.models.license_read import LicenseRead
from license_tracker.models.product_read import ProductRead


class LicenseListRead(LicenseRead):
    """License agreement list row with nested product entitlements."""

    product_count: int = 0
    products: list[ProductRead] = Field(default_factory=list)
