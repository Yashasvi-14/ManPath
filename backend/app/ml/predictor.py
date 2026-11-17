
import json
import math
from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "Mental_Health_Model.pkl"
COUNTRY_CONFIG_PATH = PROJECT_ROOT / "ml" / "artifacts" / "country_groups.json"


class ModelPredictor:
    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

        if not COUNTRY_CONFIG_PATH.exists():
            raise FileNotFoundError(
                f"Country configuration not found: {COUNTRY_CONFIG_PATH}"
            )

        self.model = joblib.load(MODEL_PATH)

        with open(COUNTRY_CONFIG_PATH, encoding="utf-8") as file:
            country_config = json.load(file)

        self.top_countries = set(country_config["top_countries"])
        self.fallback_country = country_config["fallback_country"]

        self.feature_names = list(self.model.feature_names_in_)

        self._load_categories()

    def _load_categories(self):
        """Read valid categorical values from the trained encoders."""
        preprocessor = self.model.named_steps["preprocessor"]

        ordinal_pipeline = preprocessor.named_transformers_["Ordinal"]
        ordinal_encoder = ordinal_pipeline.named_steps["encode"]

        nominal_pipeline = preprocessor.named_transformers_["Normal"]
        nominal_encoder = nominal_pipeline.named_steps["encode"]

        self.valid_stress_levels = set(ordinal_encoder.categories_[0])

        self.valid_categories = {}

        nominal_columns = preprocessor.transformers_[-1][2]

        for column, categories in zip(
            nominal_columns, nominal_encoder.categories_
        ):
            self.valid_categories[column] = set(categories)

    
    def predict(self, input_data: dict) -> float:
        """Generate a prediction from raw user input."""

        numeric_features = [
            "Study_Hours",
            "Age",
            "Avg_Daily_Usage_Hours",
            "Daily_Unlocks",
            "Physical_Activity_Hours",
            "Sleep_Hours_Per_Night",
        ]

        for feature in numeric_features:
            value = input_data[feature]

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{feature} must be numeric")

            if not math.isfinite(value):
                raise ValueError(f"{feature} must be finite")

        if input_data["Stress_Level"] not in self.valid_stress_levels:
            raise ValueError("Invalid Stress_Level")

        for column, categories in self.valid_categories.items():
            if column == "Grouped_country":
                continue

            if input_data[column] not in categories:
                raise ValueError(f"Invalid {column}")

        country = input_data["Country"]

        if not isinstance(country, str) or not country.strip():
            raise ValueError("Country must be a non-empty string")

        grouped_country = (
            country if country in self.top_countries
            else self.fallback_country
        )

        row = {
            feature: input_data[feature]
            for feature in self.feature_names
            if feature != "Grouped_country"
        }

        row["Grouped_country"] = grouped_country

        input_frame = pd.DataFrame(
            [row],
            columns=self.feature_names
        )

        prediction = self.model.predict(input_frame)[0]

        return float(prediction)

predictor = ModelPredictor()
