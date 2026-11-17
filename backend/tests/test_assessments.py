
import sys
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.core.database import get_db


@pytest.fixture
def mock_db():
    db = MagicMock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield db
    app.dependency_overrides.clear()


@pytest.fixture
def sample_assessment():
    return SimpleNamespace(
        id=uuid4(),
        input_data={"Age": 21, "Stress_Level": "Medium"},
        predicted_score=6.079,
        model_version="rf-student-mental-health-v1",
        created_at=datetime.now(timezone.utc),
    )


def test_list_assessments(
    mock_db,
    sample_assessment,
    monkeypatch,
):
    from app.api import assessments

    monkeypatch.setattr(
        assessments,
        "get_assessments",
        lambda db, skip, limit: [sample_assessment],
    )
    mock_db.scalar.return_value = 1

    client = TestClient(app)
    response = client.get("/assessments")

    assert response.status_code == 200

    result = response.json()
    assert result["total"] == 1
    assert result["skip"] == 0
    assert result["limit"] == 10
    assert len(result["assessments"]) == 1
    assert result["assessments"][0]["id"] == str(sample_assessment.id)


def test_assessment_pagination(
    mock_db,
    monkeypatch,
):
    from app.api import assessments

    captured = {}

    def fake_get_assessments(db, skip, limit):
        captured["skip"] = skip
        captured["limit"] = limit
        return []

    monkeypatch.setattr(
        assessments,
        "get_assessments",
        fake_get_assessments,
    )
    mock_db.scalar.return_value = 25

    client = TestClient(app)
    response = client.get("/assessments?skip=10&limit=5")

    assert response.status_code == 200
    assert captured == {"skip": 10, "limit": 5}
    assert response.json()["total"] == 25


def test_empty_assessment_history(
    mock_db,
    monkeypatch,
):
    from app.api import assessments

    monkeypatch.setattr(
        assessments,
        "get_assessments",
        lambda db, skip, limit: [],
    )
    mock_db.scalar.return_value = 0

    client = TestClient(app)
    response = client.get("/assessments")

    assert response.status_code == 200
    assert response.json()["assessments"] == []
    assert response.json()["total"] == 0


def test_retrieve_assessment(
    mock_db,
    sample_assessment,
    monkeypatch,
):
    from app.api import assessments

    monkeypatch.setattr(
        assessments,
        "get_assessment_by_id",
        lambda db, assessment_id: sample_assessment,
    )

    client = TestClient(app)
    response = client.get(
        f"/assessments/{sample_assessment.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(sample_assessment.id)
    assert response.json()["predicted_score"] == 6.079


def test_assessment_not_found(
    mock_db,
    monkeypatch,
):
    from app.api import assessments

    monkeypatch.setattr(
        assessments,
        "get_assessment_by_id",
        lambda db, assessment_id: None,
    )

    client = TestClient(app)
    response = client.get(
        f"/assessments/{uuid4()}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Assessment not found"


def test_invalid_pagination_parameters(mock_db):
    client = TestClient(app)

    response = client.get("/assessments?skip=-1")

    assert response.status_code == 422
