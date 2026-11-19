
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.analytics_service import (
    build_analytics_overview,
    get_user_assessment_history,
)


def build_chat_context(
    db: Session,
    user_id: UUID,
) -> dict:
    """
    Build personalized context for the authenticated user's AI conversation.
    """

    assessments = get_user_assessment_history(db, user_id)

    if not assessments:
        return {
            "has_assessments": False,
            "message": (
                "The user has not completed any assessments yet. "
                "Do not invent assessment scores, trends, or personal insights."
            ),
            "assessment_count": 0,
            "latest_assessment": None,
            "assessment_history": [],
            "analytics": None,
        }

    latest = assessments[-1]

    assessment_history = [
        {
            "id": str(assessment.id),
            "created_at": assessment.created_at.isoformat(),
            "input_data": assessment.input_data,
            "predicted_score": assessment.predicted_score,
            "model_version": assessment.model_version,
            "explanation": assessment.explanation,
        }
        for assessment in assessments
    ]

    analytics = build_analytics_overview(db, user_id)

    return {
        "has_assessments": True,
        "assessment_count": len(assessments),
        "latest_assessment": assessment_history[-1],
        "assessment_history": assessment_history,
        "analytics": analytics,
    }
