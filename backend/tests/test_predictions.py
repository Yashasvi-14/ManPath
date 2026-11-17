
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

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


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200


def test_valid_prediction():
    response = client.post("/predict", json=VALID_INPUT)

    assert response.status_code == 200

    result = response.json()
    assert isinstance(result["predicted_score"], float)
    assert result["model"] == "RandomForestRegressor"


def test_unknown_country():
    payload = {**VALID_INPUT, "Country": "Japan"}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert isinstance(response.json()["predicted_score"], float)


def test_invalid_stress_level():
    payload = {**VALID_INPUT, "Stress_Level": "Extreme"}

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_missing_field():
    payload = VALID_INPUT.copy()
    del payload["Age"]

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_extra_field():
    payload = {**VALID_INPUT, "unexpected_field": "value"}

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
