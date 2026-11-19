
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.prediction import FeatureContribution


class AssessmentExplanation(BaseModel):
    predicted_score: float
    baseline_score: float
    feature_contributions: list[FeatureContribution]


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    input_data: dict
    predicted_score: float
    model_version: str
    created_at: datetime
    explanation: AssessmentExplanation | None = None


class AssessmentListResponse(BaseModel):
    assessments: list[AssessmentResponse]
    total: int
    skip: int
    limit: int
