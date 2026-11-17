from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    input_data: dict
    predicted_score: float
    model_version: str
    created_at: datetime


class AssessmentListResponse(BaseModel):
    assessments: list[AssessmentResponse]
    total: int
    skip: int
    limit: int