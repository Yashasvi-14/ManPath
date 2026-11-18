
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ml.predictor import predictor
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
)
from app.services.assessment_service import save_assessment
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/predict", tags=["Predictions"])

MODEL_VERSION = "rf-student-mental-health-v1"


@router.post("", response_model=PredictionResponse)
def predict_mental_health(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        input_data = request.model_dump()
        score = predictor.predict(input_data)

        save_assessment(
            db=db,
            input_data=input_data,
            predicted_score=score,
            model_version=MODEL_VERSION,
            user_id=current_user.id,
        )

        return PredictionResponse(
            predicted_score=round(score, 4)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )