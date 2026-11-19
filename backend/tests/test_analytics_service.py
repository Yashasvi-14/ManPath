import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.analytics_service import (
    calculate_summary,
    build_score_history,
    build_habit_trends,
    build_categorical_trends,
    build_user_profile,
    build_insights,
)


def create_assessment(score, input_data, day, explanation=None):
    return SimpleNamespace(
        predicted_score=score,
        input_data=input_data,
        created_at=datetime(2026, 11, day, tzinfo=timezone.utc),
        explanation=explanation,
    )


@pytest.fixture
def sample_assessments():
    return [
        create_assessment(
            6.2,
            {
                "Age": 21,
                "Gender": "Male",
                "Academic_Level": "Undergraduate",
                "Country": "India",
                "Study_Hours": 3.0,
                "Avg_Daily_Usage_Hours": 5.0,
                "Sleep_Hours_Per_Night": 7.0,
                "Physical_Activity_Hours": 1.0,
                "Daily_Unlocks": 80,
                "Stress_Level": "High",
                "Most_Used_Platform": "Instagram",
                "Purpose_Of_Use": "Entertainment",
            },
            10,
        ),
        create_assessment(
            6.05,
            {
                "Age": 21,
                "Gender": "Male",
                "Academic_Level": "Undergraduate",
                "Country": "India",
                "Study_Hours": 4.0,
                "Avg_Daily_Usage_Hours": 4.5,
                "Sleep_Hours_Per_Night": 7.5,
                "Physical_Activity_Hours": 1.5,
                "Daily_Unlocks": 70,
                "Stress_Level": "Medium",
                "Most_Used_Platform": "YouTube",
                "Purpose_Of_Use": "Education",
            },
            19,
            explanation={
                "predicted_score": 6.05,
                "baseline_score": 6.215,
                "feature_contributions": [],
            },
        ),
    ]


def test_calculate_summary(sample_assessments):
    result = calculate_summary(sample_assessments)

    assert result["total_assessments"] == 2
    assert result["latest_score"] == 6.05
    assert result["previous_score"] == 6.2
    assert result["score_difference"] == -0.15


def test_calculate_summary_empty_history():
    result = calculate_summary([])

    assert result["total_assessments"] == 0
    assert result["latest_score"] is None
    assert result["previous_score"] is None
    assert result["score_difference"] is None


def test_build_score_history(sample_assessments):
    result = build_score_history(sample_assessments)

    assert len(result) == 2
    assert result[0]["score"] == 6.2
    assert result[1]["score"] == 6.05


def test_build_habit_trends(sample_assessments):
    result = build_habit_trends(sample_assessments)

    assert len(result) == 5

    study_trend = next(
        item for item in result
        if item["feature"] == "Study_Hours"
    )

    assert study_trend["history"][0]["value"] == 3.0
    assert study_trend["history"][1]["value"] == 4.0


def test_build_categorical_trends(sample_assessments):
    result = build_categorical_trends(sample_assessments)

    stress = next(
        item for item in result
        if item["feature"] == "Stress_Level"
    )

    assert len(stress["history"]) == 2
    assert len(stress["distribution"]) == 2
    assert all(
        item["percentage"] == 50.0
        for item in stress["distribution"]
    )


def test_build_user_profile(sample_assessments):
    result = build_user_profile(sample_assessments)

    assert result["age"] == 21
    assert result["gender"] == "Male"
    assert result["academic_level"] == "Undergraduate"
    assert result["country"] == "India"


def test_build_user_profile_empty_history():
    result = build_user_profile([])

    assert result["age"] is None
    assert result["gender"] is None


def test_build_insights(sample_assessments):
    result = build_insights(sample_assessments)

    assert any("Study_Hours increased by 1.00" in item for item in result)
    assert any("Stress Level" in item or "Stress Level" in item.title() for item in result)



def test_build_analytics_overview(sample_assessments, monkeypatch):
    from app.services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_user_assessment_history",
        lambda db, user_id: sample_assessments,
    )

    result = analytics_service.build_analytics_overview(
        db=None,
        user_id=None,
    )

    assert result["summary"]["total_assessments"] == 2
    assert len(result["score_history"]) == 2
    assert len(result["habit_trends"]) == 5
    assert len(result["categorical_trends"]) == 3
    assert result["profile"]["country"] == "India"
    assert result["latest_explanation"]["predicted_score"] == 6.05
    assert len(result["insights"]) > 0
