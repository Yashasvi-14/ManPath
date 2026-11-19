
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment


NUMERIC_FEATURES = [
    "Study_Hours",
    "Avg_Daily_Usage_Hours",
    "Sleep_Hours_Per_Night",
    "Physical_Activity_Hours",
    "Daily_Unlocks",
]

CATEGORICAL_FEATURES = [
    "Stress_Level",
    "Most_Used_Platform",
    "Purpose_Of_Use",
]


def get_user_assessment_history(
    db: Session,
    user_id: UUID,
) -> list[Assessment]:
    """Fetch complete chronological assessment history for one user."""

    return db.scalars(
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .order_by(
            Assessment.created_at.asc(),
            Assessment.id.asc(),
        )
    ).all()


def calculate_summary(assessments: list[Assessment]) -> dict:
    """Calculate assessment count and latest score comparison."""

    total = len(assessments)

    if total == 0:
        return {
            "total_assessments": 0,
            "latest_score": None,
            "previous_score": None,
            "score_difference": None,
        }

    latest_score = assessments[-1].predicted_score

    previous_score = (
        assessments[-2].predicted_score
        if total >= 2
        else None
    )

    score_difference = (
        round(latest_score - previous_score, 4)
        if previous_score is not None
        else None
    )

    return {
        "total_assessments": total,
        "latest_score": latest_score,
        "previous_score": previous_score,
        "score_difference": score_difference,
    }


def build_score_history(assessments: list[Assessment]) -> list[dict]:
    """Build chronological predicted-score history."""

    return [
        {
            "date": assessment.created_at,
            "score": assessment.predicted_score,
        }
        for assessment in assessments
    ]


def build_habit_trends(assessments: list[Assessment]) -> list[dict]:
    """Build historical trends for numerical lifestyle features."""

    trends = []

    for feature in NUMERIC_FEATURES:
        history = []

        for assessment in assessments:
            value = assessment.input_data.get(feature)

            if value is None:
                continue

            history.append({
                "date": assessment.created_at,
                "value": float(value),
            })

        trends.append({
            "feature": feature,
            "history": history,
        })

    return trends


def build_categorical_trends(
    assessments: list[Assessment],
) -> list[dict]:
    """Build distributions and chronological history for categorical features."""

    trends = []
    total = len(assessments)

    for feature in CATEGORICAL_FEATURES:
        counts = {}
        history = []

        for assessment in assessments:
            value = assessment.input_data.get(feature)

            if value is None:
                continue

            counts[value] = counts.get(value, 0) + 1

            history.append({
                "date": assessment.created_at,
                "value": value,
            })

        distribution = [
            {
                "category": category,
                "count": count,
                "percentage": round((count / total) * 100, 2),
            }
            for category, count in sorted(counts.items())
        ] if total else []

        trends.append({
            "feature": feature,
            "distribution": distribution,
            "history": history,
        })

    return trends


def build_user_profile(assessments: list[Assessment]) -> dict:
    """Build the latest available user profile from assessment data."""

    if not assessments:
        return {
            "age": None,
            "gender": None,
            "academic_level": None,
            "country": None,
        }

    latest_input = assessments[-1].input_data

    return {
        "age": latest_input.get("Age"),
        "gender": latest_input.get("Gender"),
        "academic_level": latest_input.get("Academic_Level"),
        "country": latest_input.get("Country"),
    }


def build_insights(assessments: list[Assessment]) -> list[str]:
    """Generate simple observations from the two latest assessments."""

    if len(assessments) < 2:
        return []

    previous = assessments[-2]
    latest = assessments[-1]

    insights = []

    for feature in NUMERIC_FEATURES:
        old_value = previous.input_data.get(feature)
        new_value = latest.input_data.get(feature)

        if old_value is None or new_value is None:
            continue

        difference = float(new_value) - float(old_value)

        if difference == 0:
            continue

        direction = "increased" if difference > 0 else "decreased"

        insights.append(
            f"{feature} {direction} by {abs(difference):.2f} "
            "between your last two assessments."
        )

    for feature in CATEGORICAL_FEATURES:
        old_value = previous.input_data.get(feature)
        new_value = latest.input_data.get(feature)

        if old_value is None or new_value is None:
            continue

        if old_value != new_value:
            insights.append(
                f"Your recorded {feature.replace('_', ' ')} changed "
                f"from {old_value} to {new_value}."
            )

    return insights


def build_analytics_overview(
    db: Session,
    user_id: UUID,
) -> dict:
    """Build the complete personal analytics overview."""

    assessments = get_user_assessment_history(db, user_id)

    latest_explanation = (
        assessments[-1].explanation
        if assessments
        else None
    )

    return {
        "summary": calculate_summary(assessments),
        "profile": build_user_profile(assessments),
        "score_history": build_score_history(assessments),
        "habit_trends": build_habit_trends(assessments),
        "categorical_trends": build_categorical_trends(assessments),
        "latest_explanation": latest_explanation,
        "insights": build_insights(assessments),
    }
