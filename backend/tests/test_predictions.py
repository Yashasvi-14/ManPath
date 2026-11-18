
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user

client = TestClient(app)

VALID_INPUT = {
    "Study_Hours": 4.5,
    "Age": 21,
    "Avg_Daily_Usage_Hours": 5.2,
    "Daily_Unlocks": 80,
    "Physical_Activity_Hours": 1.0,
    "Sleep_Hours_Per_Night": 7.0,
    "Stress_Level": "Medium",
    "Gender": "Male",
    "Academic_Level": "Undergraduate",
    "Most_Used_Platform": "Instagram",
    "Purpose_Of_Use": "Entertainment",
    "Country": "India",
}


@pytest.fixture(autouse=True)
def override_dependencies():
    mock_db = MagicMock()

    test_user = MagicMock()
    test_user.id = uuid4()
    test_user.is_active = True

    def override_get_db():
        yield mock_db

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield mock_db, test_user

    app.dependency_overrides.clear()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200


@patch("app.api.predictions.save_assessment")
def test_valid_prediction_saves_assessment(
    mock_save,
    override_dependencies,
):
    mock_db, test_user = override_dependencies

    response = client.post("/predict", json=VALID_INPUT)

    assert response.status_code == 200

    result = response.json()
    assert isinstance(result["predicted_score"], float)
    assert result["model"] == "RandomForestRegressor"

    mock_save.assert_called_once()

    kwargs = mock_save.call_args.kwargs

    assert kwargs["db"] is mock_db
    assert kwargs["input_data"] == VALID_INPUT
    assert isinstance(kwargs["predicted_score"], float)
    assert kwargs["model_version"] == "rf-student-mental-health-v1"
    assert kwargs["user_id"] == test_user.id


@patch("app.api.predictions.save_assessment")
def test_unknown_country(mock_save):
    payload = {**VALID_INPUT, "Country": "Japan"}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert isinstance(response.json()["predicted_score"], float)
    mock_save.assert_called_once()

    assert mock_save.call_args.kwargs["user_id"] is not None


@patch("app.api.predictions.save_assessment")
def test_invalid_stress_level_does_not_save(mock_save):
    payload = {**VALID_INPUT, "Stress_Level": "Extreme"}

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    mock_save.assert_not_called()


def test_missing_field():
    payload = VALID_INPUT.copy()
    del payload["Age"]

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_extra_field():
    payload = {**VALID_INPUT, "unexpected_field": "value"}

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


@patch("app.api.predictions.save_assessment")
def test_database_failure_does_not_return_success(mock_save):
    mock_save.side_effect = RuntimeError("Database unavailable")

    test_client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    response = test_client.post("/predict", json=VALID_INPUT)

    assert response.status_code == 500
