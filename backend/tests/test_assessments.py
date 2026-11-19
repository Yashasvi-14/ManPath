import sys
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user


@pytest.fixture
def mock_db():
    db = MagicMock()
    test_user = SimpleNamespace(
        id=uuid4(),
        is_active=True,
    )

    def override_get_db():
        yield db

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield db, test_user

    app.dependency_overrides.clear()


@pytest.fixture
def sample_assessment():
    return SimpleNamespace(
        id=uuid4(),
        input_data={"Age": 21, "Stress_Level": "Medium"},
        predicted_score=6.079,
        model_version="rf-student-mental-health-v1",
        created_at=datetime.now(timezone.utc),
        explanation=None,
    )


def test_list_assessments(mock_db, sample_assessment, monkeypatch):
    from app.api import assessments

    db, user = mock_db
    captured = {}

    def fake_get_assessments(db, user_id, skip, limit):
        captured["user_id"] = user_id
        return [sample_assessment], 1

    monkeypatch.setattr(assessments, "get_assessments", fake_get_assessments)

    client = TestClient(app)
    response = client.get("/assessments/")

    assert response.status_code == 200
    result = response.json()

    assert result["total"] == 1
    assert result["skip"] == 0
    assert result["limit"] == 10
    assert len(result["assessments"]) == 1
    assert result["assessments"][0]["id"] == str(sample_assessment.id)
    assert captured["user_id"] == user.id


def test_assessment_pagination(mock_db, monkeypatch):
    from app.api import assessments

    db, user = mock_db
    captured = {}

    def fake_get_assessments(db, user_id, skip, limit):
        captured.update(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )
        return [], 25

    monkeypatch.setattr(assessments, "get_assessments", fake_get_assessments)

    client = TestClient(app)
    response = client.get("/assessments/?skip=10&limit=5")

    assert response.status_code == 200
    assert captured == {
        "user_id": user.id,
        "skip": 10,
        "limit": 5,
    }
    assert response.json()["total"] == 25


def test_empty_assessment_history(mock_db, monkeypatch):
    from app.api import assessments

    def fake_get_assessments(db, user_id, skip, limit):
        return [], 0

    monkeypatch.setattr(assessments, "get_assessments", fake_get_assessments)

    client = TestClient(app)
    response = client.get("/assessments/")

    assert response.status_code == 200
    assert response.json()["assessments"] == []
    assert response.json()["total"] == 0


def test_retrieve_assessment(mock_db, sample_assessment, monkeypatch):
    from app.api import assessments

    db, user = mock_db
    captured = {}

    def fake_get_assessment_by_id(db, assessment_id, user_id):
        captured["assessment_id"] = assessment_id
        captured["user_id"] = user_id
        return sample_assessment

    monkeypatch.setattr(
        assessments,
        "get_assessment_by_id",
        fake_get_assessment_by_id,
    )

    client = TestClient(app)
    response = client.get(f"/assessments/{sample_assessment.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(sample_assessment.id)
    assert response.json()["predicted_score"] == 6.079
    assert captured["assessment_id"] == sample_assessment.id
    assert captured["user_id"] == user.id


def test_retrieve_assessment_with_explanation(mock_db, sample_assessment, monkeypatch):
    from app.api import assessments

    sample_assessment.explanation = {
        "predicted_score": 6.079,
        "baseline_score": 6.2152,
        "feature_contributions": [
            {
                "feature": "Sleep_Hours_Per_Night",
                "contribution": 0.1047,
            },
            {
                "feature": "Avg_Daily_Usage_Hours",
                "contribution": -0.3117,
            },
        ],
    }

    monkeypatch.setattr(
        assessments,
        "get_assessment_by_id",
        lambda db, assessment_id, user_id: sample_assessment,
    )

    client = TestClient(app)
    response = client.get(f"/assessments/{sample_assessment.id}")

    assert response.status_code == 200

    explanation = response.json()["explanation"]

    assert explanation["predicted_score"] == 6.079
    assert explanation["baseline_score"] == 6.2152
    assert len(explanation["feature_contributions"]) == 2
    assert explanation["feature_contributions"][0]["feature"] == "Sleep_Hours_Per_Night"


def test_assessment_not_found(mock_db, monkeypatch):
    from app.api import assessments

    monkeypatch.setattr(
        assessments,
        "get_assessment_by_id",
        lambda db, assessment_id, user_id: None,
    )

    client = TestClient(app)
    response = client.get(f"/assessments/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Assessment not found"


def test_invalid_pagination_parameters(mock_db):
    client = TestClient(app)

    response = client.get("/assessments/?skip=-1")

    assert response.status_code == 422
