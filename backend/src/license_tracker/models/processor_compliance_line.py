"""Processor compliance line model."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class ProcessorComplianceLine(BaseModel):
    """Processor entitlement purchased on a CSI agreement."""

    product_id: uuid.UUID
    product_name: str
    licensed_quantity: int
