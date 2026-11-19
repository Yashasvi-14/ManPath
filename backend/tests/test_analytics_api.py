
import sys
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user


@pytest.fixture
def mock_dependencies():
    db = MagicMock()
    user = SimpleNamespace(
        id=uuid4(),
        is_active=True,
    )

    def override_get_db():
        yield db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield db, user

    app.dependency_overrides.clear()


def test_analytics_overview(mock_dependencies, monkeypatch):
    from app.api import analytics

    db, user = mock_dependencies
    captured = {}

    expected = {
        "summary": {
            "total_assessments": 1,
            "latest_score": 6.05,
            "previous_score": None,
            "score_difference": None,
        },
        "profile": {
            "age": 21,
            "gender": "Male",
            "academic_level": "Undergraduate",
            "country": "India",
        },
        "score_history": [],
        "habit_trends": [],
        "categorical_trends": [],
        "latest_explanation": None,
        "insights": [],
    }

    def fake_build_analytics_overview(db, user_id):
        captured["user_id"] = user_id
        return expected

    monkeypatch.setattr(
        analytics,
        "build_analytics_overview",
        fake_build_analytics_overview,
    )

    client = TestClient(app)
    response = client.get("/analytics/overview")

    assert response.status_code == 200
    assert response.json()["summary"]["latest_score"] == 6.05
    assert response.json()["profile"]["country"] == "India"
    assert captured["user_id"] == user.id


def test_analytics_overview_empty_history(mock_dependencies, monkeypatch):
    from app.api import analytics

    db, user = mock_dependencies

    expected = {
        "summary": {
            "total_assessments": 0,
            "latest_score": None,
            "previous_score": None,
            "score_difference": None,
        },
        "profile": {
            "age": None,
            "gender": None,
            "academic_level": None,
            "country": None,
        },
        "score_history": [],
        "habit_trends": [],
        "categorical_trends": [],
        "latest_explanation": None,
        "insights": [],
    }

    monkeypatch.setattr(
        analytics,
        "build_analytics_overview",
        lambda db, user_id: expected,
    )

    client = TestClient(app)
    response = client.get("/analytics/overview")

    assert response.status_code == 200
    assert response.json()["summary"]["total_assessments"] == 0
    assert response.json()["score_history"] == []
    assert response.json()["latest_explanation"] is None


def test_analytics_requires_authentication():
    from app.core.dependencies import get_current_user

    app.dependency_overrides.pop(get_current_user, None)

    client = TestClient(app)
    response = client.get("/analytics/overview")

    assert response.status_code == 401
