"""Processor core factor reference domain model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC.
    """
    return datetime.now(UTC)


class ProcessorCoreFactor(BaseModel):
    """Oracle processor core factor used to convert cores to processor licenses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    match_pattern: str
    core_factor: float
    priority: int = 0
    is_default: bool = False
    notes: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
