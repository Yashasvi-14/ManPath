
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.assessment import Assessment


def save_assessment(
    db: Session,
    input_data: dict,
    predicted_score: float,
    model_version: str,
    user_id: UUID,
    explanation: dict | None = None,
):
    assessment = Assessment(
        input_data=input_data,
        predicted_score=predicted_score,
        model_version=model_version,
        user_id=user_id,
        explanation=explanation,
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
    user_id: UUID,
    skip: int = 0,
    limit: int = 10,
):
    query = select(Assessment).where(
        Assessment.user_id == user_id
    )

    total = db.scalar(
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.user_id == user_id)
    )

    assessments = db.scalars(
        query
        .order_by(
            Assessment.created_at.desc(),
            Assessment.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    ).all()

    return assessments, total


def get_assessment_by_id(
    db: Session,
    assessment_id: UUID,
    user_id: UUID,
):
    return db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.user_id == user_id,
        )
    )