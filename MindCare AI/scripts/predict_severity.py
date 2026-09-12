"""Production inference for the approved Severity classifier only."""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import shap

from src.config import ARTIFACTS_DATA_DIR, PRODUCTION_MODELS_DIR


MODEL_PATH = PRODUCTION_MODELS_DIR / "model.joblib"
REQUIRED_FIELDS = (
    "Age",
    "Gender",
    "Occupation",
    "Sleep Hours",
    "Physical Activity (hrs/week)",
    "Caffeine Intake (mg/day)",
    "Alcohol Consumption (drinks/week)",
    "Smoking",
    "Diet Quality (1-10)",
    "Heart Rate (bpm)",
    "Breathing Rate (breaths/min)",
    "Sweating Level (1-5)",
    "Family History of Anxiety",
    "Dizziness",
    "Medication",
    "Therapy Sessions (per month)",
    "Recent Major Life Event",
)
CATEGORICAL_VALUES = {
    "Gender": {"Female", "Male", "Other"},
    "Occupation": {
        "Artist", "Athlete", "Chef", "Doctor", "Engineer", "Freelancer",
        "Lawyer", "Musician", "Nurse", "Other", "Scientist", "Student", "Teacher",
    },
}
BINARY_FIELDS = {
    "Smoking",
    "Family History of Anxiety",
    "Dizziness",
    "Medication",
    "Recent Major Life Event",
}
NUMERIC_RANGES = {
    "Age": (18, 120),
    "Sleep Hours": (0, 14),
    "Physical Activity (hrs/week)": (0, 168),
    "Caffeine Intake (mg/day)": (0, 2000),
    "Alcohol Consumption (drinks/week)": (0, 50),
    "Diet Quality (1-10)": (1, 10),
    "Heart Rate (bpm)": (40, 180),
    "Breathing Rate (breaths/min)": (5, 60),
    "Sweating Level (1-5)": (1, 5),
    "Therapy Sessions (per month)": (0, 50),
}


def _validate_patient(patient: dict[str, Any]) -> None:
    """Reject incomplete, invalid, or implausible patient profiles."""
    missing = [field for field in REQUIRED_FIELDS if field not in patient]
    if missing:
        raise ValueError(f"Missing required patient fields: {', '.join(missing)}")
    for field, allowed in CATEGORICAL_VALUES.items():
        if patient[field] not in allowed:
            raise ValueError(f"Unexpected {field}: {patient[field]!r}")
    for field in BINARY_FIELDS:
        if patient[field] not in {"Yes", "No", 0, 1, False, True}:
            raise ValueError(f"{field} must be Yes or No")
    for field, (minimum, maximum) in NUMERIC_RANGES.items():
        try:
            value = float(patient[field])
        except (TypeError, ValueError) as error:
            raise ValueError(f"{field} must be numeric") from error
        if not minimum <= value <= maximum:
            raise ValueError(f"{field} must be between {minimum} and {maximum}")


def _binary_value(value: Any) -> int:
    """Convert raw binary values to the training representation."""
    if value in {"Yes", 1, True}:
        return 1
    return 0


def _prepare_features(patient: dict[str, Any], model: Any) -> pd.DataFrame:
    """Apply the shared encoder/scaler and align with the approved model columns."""
    encoder = joblib.load(ARTIFACTS_DATA_DIR / "onehot_encoder.joblib")
    scaler = joblib.load(ARTIFACTS_DATA_DIR / "scaler.joblib")
    raw = pd.DataFrame([{field: patient[field] for field in REQUIRED_FIELDS}])
    for field in BINARY_FIELDS:
        raw[field] = raw[field].map(_binary_value)

    encoded = pd.DataFrame(
        encoder.transform(raw[["Gender", "Occupation"]]),
        columns=encoder.get_feature_names_out(["Gender", "Occupation"]),
    )
    scaled_input = pd.DataFrame(0.0, index=raw.index, columns=scaler.feature_names_in_)
    for field in scaler.feature_names_in_:
        if field in raw:
            scaled_input[field] = raw[field]
    scaled = pd.DataFrame(
        scaler.transform(scaled_input),
        columns=scaler.feature_names_in_,
    )
    prepared = pd.concat([scaled, raw[list(BINARY_FIELDS)], encoded], axis=1)
    model_columns = list(model.feature_names_in_)
    return prepared.reindex(columns=model_columns, fill_value=0.0)


def _shap_values(model: Any, features: pd.DataFrame, class_index: int) -> list[dict[str, float]]:
    """Return the five largest absolute SHAP contributions for the predicted class."""
    explanation = shap.TreeExplainer(model)(features)
    values = explanation.values
    if values.ndim == 3:
        values = values[0, :, class_index]
    else:
        values = values[0]
    ranked = sorted(
        zip(features.columns, values),
        key=lambda item: abs(float(item[1])),
        reverse=True,
    )[:5]
    return [
        {"feature": feature, "shap_value": float(value)}
        for feature, value in ranked
    ]


def predict_severity(patient: dict[str, Any]) -> dict[str, Any]:
    """Predict a Severity band and explain its top five model contributions."""
    _validate_patient(patient)
    model = joblib.load(MODEL_PATH)
    features = _prepare_features(patient, model)
    probabilities = model.predict_proba(features)[0]
    class_index = int(probabilities.argmax())
    return {
        "severity": str(model.classes_[class_index]),
        "confidence": float(probabilities[class_index]),
        "top_features": _shap_values(model, features, class_index),
    }


if __name__ == "__main__":
    raise SystemExit("Import predict_severity(patient) from this module.")