"""License detail read model."""

from __future__ import annotations

from pydantic import Field

from license_tracker.models.license_read import LicenseRead
from license_tracker.models.product_read import ProductRead


class LicenseDetailRead(LicenseRead):
    """License agreement with nested product entitlements."""

    products: list[ProductRead] = Field(default_factory=list)
