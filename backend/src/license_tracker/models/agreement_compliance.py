"""Agreement compliance model."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from license_tracker.models.processor_compliance_line import ProcessorComplianceLine


class AgreementCompliance(BaseModel):
    """Purchased license inventory for a CSI agreement."""

    agreement_id: uuid.UUID
    csi: str
    processor_licenses_purchased: int
    processor_lines: list[ProcessorComplianceLine] = Field(default_factory=list)
    named_user_plus_purchased: int
