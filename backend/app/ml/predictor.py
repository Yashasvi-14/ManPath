
import json
import math
from pathlib import Path
import shap
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

        self.preprocessor = self.model.named_steps["preprocessor"]
        self.estimator = self.model.named_steps["random forest"]

        self.explainer = shap.TreeExplainer(self.estimator)

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


    
    def _build_feature_mapping(self) -> list[str]:
        """Map transformed model features to their original input features."""

        mapping = []

        for name, _, columns in self.preprocessor.transformers_:
            if name in ("Skewed_Pipeline", "Plain_Numeric", "Ordinal"):
                mapping.extend(columns)

            elif name == "Normal":
                encoder = (
                    self.preprocessor
                    .named_transformers_["Normal"]
                    .named_steps["encode"]
                )

                encoded_names = encoder.get_feature_names_out(columns)

                for encoded_name in encoded_names:
                    original_feature = next(
                        (
                            column
                            for column in columns
                            if encoded_name.startswith(f"{column}_")
                        ),
                        encoded_name,
                    )
                    mapping.append(original_feature)

        return mapping

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


    
    def explain(self, input_data: dict) -> dict:
        """Explain a prediction using SHAP values."""

        # Validate input and prepare the prediction row.
        prediction = self.predict(input_data)

        country = input_data["Country"]
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

        # Apply the fitted preprocessing pipeline.
        transformed = self.preprocessor.transform(input_frame)

        # Calculate SHAP contributions.
        shap_values = self.explainer.shap_values(transformed)
        contributions = shap_values[0]

        # Map transformed features to original input features.
        feature_mapping = self._build_feature_mapping()

        # Aggregate one-hot encoded contributions.
        aggregated = {}

        for feature, value in zip(feature_mapping, contributions):
            aggregated[feature] = (
                aggregated.get(feature, 0.0) + float(value)
            )

        sorted_contributions = sorted(
            aggregated.items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        )

        baseline = float(self.explainer.expected_value[0])

        return {
            "predicted_score": prediction,
            "baseline_score": baseline,
            "feature_contributions": [
                {
                    "feature": feature,
                    "contribution": value,
                }
                for feature, value in sorted_contributions
            ],
        }


predictor = ModelPredictor()