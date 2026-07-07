"""Pooled product read model."""

from __future__ import annotations

from pydantic import BaseModel

from license_tracker.domain.enums import HostLicenseType


class PooledProductRead(BaseModel):
    """Distinct product available in the pooled license inventory."""

    product_name: str
    option_name: str | None
    license_type: HostLicenseType
    total_quantity: int
