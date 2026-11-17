
from uuid import UUID

from sqlalchemy import select
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


def get_assessments(
    db: Session,
    skip: int = 0,
    limit: int = 10,
) -> list[Assessment]:
    statement = (
        select(Assessment)
        .order_by(
            Assessment.created_at.desc(),
            Assessment.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def get_assessment_by_id(
    db: Session,
    assessment_id: UUID,
) -> Assessment | None:
    statement = select(Assessment).where(
        Assessment.id == assessment_id
    )

    return db.scalars(statement).first()
