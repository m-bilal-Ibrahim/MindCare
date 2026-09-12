"""Prepare the requested dataset and preprocessing-artifact layout."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight

from src.config import (
    ARTIFACTS_DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REFERENCE_DATA_DIR,
)


SPLITS = ("train", "val", "test")
CATEGORICAL_COLUMNS = ["Gender", "Occupation"]
NUMERIC_COLUMNS = [
    "Age",
    "Sleep Hours",
    "Physical Activity (hrs/week)",
    "Caffeine Intake (mg/day)",
    "Alcohol Consumption (drinks/week)",
    "Stress Level (1-10)",
    "Heart Rate (bpm)",
    "Breathing Rate (breaths/min)",
    "Sweating Level (1-5)",
    "Therapy Sessions (per month)",
    "Diet Quality (1-10)",
    "Anxiety Level (1-10)",
]


def _fit_artifacts(raw_data: pd.DataFrame, labels: pd.Series) -> None:
    """Fit reusable preprocessing objects using source data only."""
    ARTIFACTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    encoder.fit(raw_data[CATEGORICAL_COLUMNS])
    joblib.dump(encoder, ARTIFACTS_DATA_DIR / "onehot_encoder.joblib")

    scaler = StandardScaler()
    scaler.fit(raw_data[NUMERIC_COLUMNS])
    joblib.dump(scaler, ARTIFACTS_DATA_DIR / "scaler.joblib")

    classes = np.array(sorted(labels.dropna().unique()))
    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=labels,
    )
    (ARTIFACTS_DATA_DIR / "class_weights.json").write_text(
        json.dumps(dict(zip(classes, weights.tolist())), indent=2) + "\n",
        encoding="utf-8",
    )


def prepare_dataset() -> None:
    """Create combined split files and preprocessing artifacts."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    raw_data = pd.read_csv(RAW_DATA_DIR / "mindcare_dataset_final.csv")
    for split in SPLITS:
        features_path = PROCESSED_DATA_DIR / f"X_{split}.csv"
        labels_path = PROCESSED_DATA_DIR / f"y_{split}.csv"
        if features_path.exists() and labels_path.exists():
            features = pd.read_csv(features_path)
            labels = pd.read_csv(labels_path)
            pd.concat([features, labels], axis=1).to_csv(
                PROCESSED_DATA_DIR / f"{split}.csv", index=False
            )

        scaled_features_path = PROCESSED_DATA_DIR / f"X_{split}_scaled.csv"
        if scaled_features_path.exists() and labels_path.exists():
            scaled_features = pd.read_csv(scaled_features_path)
            pd.concat([scaled_features, labels], axis=1).to_csv(
                PROCESSED_DATA_DIR / f"{split}_scaled.csv", index=False
            )

        if not (PROCESSED_DATA_DIR / f"{split}.csv").exists():
            raise FileNotFoundError(f"Missing processed split: {split}.csv")
        if not (PROCESSED_DATA_DIR / f"{split}_scaled.csv").exists():
            raise FileNotFoundError(f"Missing scaled split: {split}_scaled.csv")

    reference = PROCESSED_DATA_DIR / "template_reference.csv"
    if reference.exists():
        reference.replace(REFERENCE_DATA_DIR / reference.name)

    _fit_artifacts(raw_data, pd.read_csv(PROCESSED_DATA_DIR / "train.csv").iloc[:, -1])


if __name__ == "__main__":
    prepare_dataset()