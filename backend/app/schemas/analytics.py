
from datetime import datetime

from pydantic import BaseModel

from app.schemas.assessment import AssessmentExplanation


class AnalyticsSummary(BaseModel):
    total_assessments: int
    latest_score: float | None
    previous_score: float | None
    score_difference: float | None


class ScoreHistoryItem(BaseModel):
    date: datetime
    score: float


class HabitDataPoint(BaseModel):
    date: datetime
    value: float


class HabitTrend(BaseModel):
    feature: str
    history: list[HabitDataPoint]


class CategoryCount(BaseModel):
    category: str
    count: int
    percentage: float


class CategoricalDataPoint(BaseModel):
    date: datetime
    value: str


class CategoricalTrend(BaseModel):
    feature: str
    distribution: list[CategoryCount]
    history: list[CategoricalDataPoint]


class UserProfile(BaseModel):
    age: float | None = None
    gender: str | None = None
    academic_level: str | None = None
    country: str | None = None


class AnalyticsOverviewResponse(BaseModel):
    summary: AnalyticsSummary
    profile: UserProfile
    score_history: list[ScoreHistoryItem]
    habit_trends: list[HabitTrend]
    categorical_trends: list[CategoricalTrend]
    latest_explanation: AssessmentExplanation | None
    insights: list[str]
