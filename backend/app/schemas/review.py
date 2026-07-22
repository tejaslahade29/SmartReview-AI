from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PartyMappingEntrySchema(BaseModel):
    original_name: str
    normalized_role: str


class ReviewFindingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    finding_id: str
    paragraph_id: str
    issue_type: str
    severity: str
    explanation: str
    suggested_text: str | None = None
    confidence: float


class ReviewSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    agreement_type: str
    status: str
    model_used: str
    party_mapping: list[PartyMappingEntrySchema]
    created_at: datetime
    findings: list[ReviewFindingSchema]
