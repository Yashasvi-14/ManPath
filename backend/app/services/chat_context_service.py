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
            "analytics": None,
        }

    latest = assessments[-1]

    analytics = build_analytics_overview(db, user_id)

    return {
        "has_assessments": True,
        "assessment_count": len(assessments),
        "latest_assessment": {
            "id": str(latest.id),
            "created_at": latest.created_at.isoformat(),
            "input_data": latest.input_data,
            "predicted_score": latest.predicted_score,
            "model_version": latest.model_version,
            "explanation": latest.explanation,
        },
        "analytics": analytics,
    }