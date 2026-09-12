"""Audit the approved Severity model and compare full-feature candidates."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from src.config import EXPERIMENT_MODELS_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR, REPORTS_DIR


TARGET = "Severity"
BANDS = ["Minimal (1-2)", "Mild (3-4)", "Moderate (5-6)", "High (7-8)", "Severe (9-10)"]
MATCH_COLUMNS = [
    "Sleep Hours",
    "Physical Activity (hrs/week)",
    "Heart Rate (bpm)",
    "Breathing Rate (breaths/min)",
    "Sweating Level (1-5)",
    "Dizziness",
]
FULL_FEATURE_COLUMNS = [
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
]
BINARY_COLUMNS = [
    "Smoking",
    "Family History of Anxiety",
    "Dizziness",
    "Medication",
    "Recent Major Life Event",
]
CATEGORICAL_COLUMNS = ["Gender", "Occupation"]


def _normalise_binary(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in BINARY_COLUMNS:
        if column not in result:
            continue
        result[column] = result[column].map({"Yes": 1, "No": 0}).fillna(result[column])
        result[column] = pd.to_numeric(result[column], errors="raise")
    return result


def _raw_split_indices(raw: pd.DataFrame, splits: dict[str, pd.DataFrame]) -> dict[str, np.ndarray]:
    """Recover the original raw rows represented by each processed split."""
    raw_key = _normalise_binary(raw[MATCH_COLUMNS]).round(10).astype(str)
    raw_key["_occurrence"] = raw_key.groupby(MATCH_COLUMNS, sort=False).cumcount()
    raw_key["_raw_index"] = np.arange(len(raw))
    result = {}
    for name, split in splits.items():
        split_key = split[MATCH_COLUMNS].round(10).astype(str)
        split_key["_occurrence"] = split_key.groupby(MATCH_COLUMNS, sort=False).cumcount()
        matched = split_key.merge(
            raw_key[MATCH_COLUMNS + ["_occurrence", "_raw_index"]],
            on=MATCH_COLUMNS + ["_occurrence"],
            how="left",
            validate="one_to_one",
        )
        if matched["_raw_index"].isna().any():
            raise ValueError(f"Could not map all {name} rows back to raw data")
        result[name] = matched["_raw_index"].astype(int).to_numpy()
    return result


def _metrics(actual: pd.Series, predicted: np.ndarray) -> dict:
    report = classification_report(
        actual,
        predicted,
        labels=BANDS,
        output_dict=True,
        zero_division=0,
    )
    per_band = {
        band: {
            "precision": float(report[band]["precision"]),
            "recall": float(report[band]["recall"]),
            "f1": float(report[band]["f1-score"]),
            "support": int(report[band]["support"]),
        }
        for band in BANDS
    }
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_f1": float(f1_score(actual, predicted, labels=BANDS, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(actual, predicted, labels=BANDS).tolist(),
        "labels": BANDS,
        "per_band": per_band,
    }


def _build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLUMNS),
        ],
        remainder="passthrough",
    )


def main() -> None:
    raw = pd.read_csv(RAW_DATA_DIR / "mindcare_dataset_final.csv")
    processed = {
        name: pd.read_csv(PROCESSED_DATA_DIR / f"{name}.csv")
        for name in ("train", "val", "test")
    }
    processed_scaled_test = pd.read_csv(PROCESSED_DATA_DIR / "test_scaled.csv")
    indices = _raw_split_indices(raw, processed)
    raw_normalised = _normalise_binary(raw)
    raw_features = raw_normalised[FULL_FEATURE_COLUMNS]
    train_x = raw_features.iloc[indices["train"]]
    val_x = raw_features.iloc[indices["val"]]
    test_x = raw_features.iloc[indices["test"]]
    train_y = raw[TARGET].iloc[indices["train"]]
    val_y = raw[TARGET].iloc[indices["val"]]
    test_y = raw[TARGET].iloc[indices["test"]]
    label_to_id = {label: index for index, label in enumerate(BANDS)}
    id_to_label = {index: label for label, index in label_to_id.items()}
    train_y_encoded = train_y.map(label_to_id)

    current_model = joblib.load(Path("models/production/model.joblib"))
    current_test_x = processed_scaled_test.reindex(columns=current_model.feature_names_in_)
    current_predictions = current_model.predict(current_test_x)
    results = {"current_production_6_feature_random_forest": _metrics(test_y, current_predictions)}

    candidates = {
        "full_feature_lightgbm": LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            class_weight="balanced",
            random_state=42,
            verbosity=-1,
        ),
        "full_feature_xgboost": XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1,
        ),
        "full_feature_catboost": CatBoostClassifier(
            iterations=300,
            depth=6,
            learning_rate=0.05,
            loss_function="MultiClass",
            random_seed=42,
            verbose=False,
        ),
    }
    for name, estimator in candidates.items():
        model = Pipeline([("preprocessor", _build_preprocessor()), ("classifier", estimator)])
        model.fit(train_x, train_y_encoded)
        encoded_predictions = model.predict(test_x).ravel().astype(int)
        predictions = np.array([id_to_label[index] for index in encoded_predictions])
        results[name] = _metrics(test_y, predictions)
        joblib.dump(model, EXPERIMENT_MODELS_DIR / f"{name}.joblib")

    best_name = max(results, key=lambda name: results[name]["macro_f1"] if name != "current_production_6_feature_random_forest" else -1)
    report = {
        "target": TARGET,
        "full_feature_columns": FULL_FEATURE_COLUMNS,
        "provenance": {
            "production_model": "models/production/model.joblib",
            "production_features": list(current_model.feature_names_in_),
            "notebook_training_record": "No executed training cells or feature_list.json found; notebooks are scaffolds.",
            "training_script_record": "The artifact was trained earlier with scripts/train_models.py using the six wearable features; the script is present now but has no earlier committed training record.",
            "git_training_record": "No prior training-script or model-artifact commit was found; model artifacts are ignored/generated files.",
        },
        "same_test_rows": int(len(test_y)),
        "current_production": results["current_production_6_feature_random_forest"],
        "full_feature_candidates": {
            name: metrics for name, metrics in results.items()
            if name != "current_production_6_feature_random_forest"
        },
        "best_full_feature_candidate": best_name,
        "comparison_by_band": {
            band: {
                "current_production": results["current_production_6_feature_random_forest"]["per_band"][band],
                **{
                    name: metrics["per_band"][band]
                    for name, metrics in results.items()
                    if name != "current_production_6_feature_random_forest"
                },
            }
            for band in BANDS
        },
    }
    REPORTS_DIR.joinpath("metrics").mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "metrics" / "severity_model_audit.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()