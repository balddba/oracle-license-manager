"""Core factor update model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CoreFactorUpdate(BaseModel):
    """Payload to update a processor core factor row."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=256)
    match_pattern: str | None = Field(default=None, max_length=256)
    core_factor: float | None = Field(default=None, gt=0)
    priority: int | None = None
    is_default: bool | None = None
    notes: str | None = Field(default=None, max_length=4000)
