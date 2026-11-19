
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Study_Hours: float = Field(ge=0, allow_inf_nan=False)
    Age: float = Field(gt=0, allow_inf_nan=False)
    Avg_Daily_Usage_Hours: float = Field(ge=0, allow_inf_nan=False)
    Daily_Unlocks: int = Field(ge=0)
    Physical_Activity_Hours: float = Field(ge=0, allow_inf_nan=False)
    Sleep_Hours_Per_Night: float = Field(ge=0, allow_inf_nan=False)

    Stress_Level: Literal["Low", "Medium", "High", "Very High"]

    Gender: Literal["Female", "Male"]

    Academic_Level: Literal[
        "Graduate",
        "High School",
        "Undergraduate"
    ]

    Most_Used_Platform: Literal[
        "Facebook", "Instagram", "KakaoTalk", "LINE",
        "LinkedIn", "Snapchat", "TikTok", "Twitter",
        "VKontakte", "WeChat", "WhatsApp", "YouTube"
    ]

    Purpose_Of_Use: Literal[
        "Education", "Entertainment", "Networking", "News"
    ]

    Country: str = Field(min_length=1, max_length=100)


class FeatureContribution(BaseModel):
    feature: str
    contribution: float


class PredictionResponse(BaseModel):
    predicted_score: float
    baseline_score: float
    feature_contributions: list[FeatureContribution]
    model: str = "RandomForestRegressor"


class SimulationResponse(BaseModel):
    hypothetical: bool = True
    predicted_score: float
    baseline_score: float
    score_difference: float
    interpretation: str
    model: str = "RandomForestRegressor"