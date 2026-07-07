"""Product license summary model."""

from __future__ import annotations

from pydantic import BaseModel


class ProductLicenseSummary(BaseModel):
    """License counts for one product rolled up across all CSI agreements."""

    product_name: str
    cores_licensed: int
    nups_licensed: int
    cores_in_use: int
    nups_in_use: int | None
    balance: int
