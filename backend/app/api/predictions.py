
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ml.predictor import predictor
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    SimulationResponse,
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
        explanation = predictor.explain(input_data)
        score = explanation["predicted_score"]

        save_assessment(
            db=db,
            input_data=input_data,
            predicted_score=score,
            model_version=MODEL_VERSION,
            user_id=current_user.id,
            explanation=explanation,
        )

        return PredictionResponse(
            predicted_score=round(score, 4),
            baseline_score=explanation["baseline_score"],
            feature_contributions=explanation["feature_contributions"],
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

@router.post("/simulate", response_model=SimulationResponse)
def simulate_mental_health(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        input_data = request.model_dump()

        explanation = predictor.explain(input_data)

        score = explanation["predicted_score"]
        baseline = explanation["baseline_score"]

        return SimulationResponse(
            hypothetical=True,
            predicted_score=round(score, 4),
            baseline_score=baseline,
            score_difference=round(score - baseline, 4),
            interpretation=(
                "This is a hypothetical model-based simulation, "
                "not an actual assessment or a prediction of future "
                "mental health. The result does not establish causation."
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )