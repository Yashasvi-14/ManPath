
from fastapi import APIRouter, HTTPException

from app.ml.predictor import predictor
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
)

router = APIRouter(prefix="/predict", tags=["Predictions"])


@router.post("", response_model=PredictionResponse)
def predict_mental_health(request: PredictionRequest):
    try:
        score = predictor.predict(request.model_dump())

        return PredictionResponse(
            predicted_score=round(score, 4)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )
