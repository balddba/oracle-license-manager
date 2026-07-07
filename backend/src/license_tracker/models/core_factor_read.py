"""Core factor read model."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CoreFactorRead(BaseModel):
    """Processor core factor API response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    match_pattern: str
    core_factor: float
    priority: int
    is_default: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
