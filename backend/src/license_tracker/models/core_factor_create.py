"""Core factor create model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CoreFactorCreate(BaseModel):
    """Payload to create a processor core factor row."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=256)
    match_pattern: str = Field(max_length=256)
    core_factor: float = Field(gt=0)
    priority: int = 0
    is_default: bool = False
    notes: str | None = Field(default=None, max_length=4000)
