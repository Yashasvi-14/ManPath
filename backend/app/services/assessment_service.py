from sqlalchemy.orm import Session

from app.models.assessment import Assessment


def save_assessment(
    db: Session,
    input_data: dict,
    predicted_score: float,
    model_version: str,
) -> Assessment:
    assessment = Assessment(
        input_data=input_data,
        predicted_score=predicted_score,
        model_version=model_version,
    )

    try:
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    except Exception:
        db.rollback()
        raise