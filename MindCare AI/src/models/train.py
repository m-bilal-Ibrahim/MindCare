"""Model training entry points."""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from src.config import PREDICTION_EXCLUDED_COLUMNS, RANDOM_STATE, TARGET_COLUMN
from src.models.evaluate import classification_metrics


def save_model(model, path: str | Path) -> Path:
    """Persist a fitted model artifact and return its path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, destination)
    return destination


def train_candidates(
    train_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    feature_columns: list[str] | tuple[str, ...] | None = None,
) -> dict[str, dict[str, Any]]:
    """Train candidates and evaluate them on validation data."""
    features = list(feature_columns) if feature_columns else [
        column for column in train_data.columns
        if column not in PREDICTION_EXCLUDED_COLUMNS
    ]
    missing = sorted(set(features) - set(train_data.columns))
    if missing:
        raise ValueError(f"Missing training features: {', '.join(missing)}")
    train_features = train_data[features]
    train_target = train_data[TARGET_COLUMN]
    validation_features = validation_data[features]
    validation_target = validation_data[TARGET_COLUMN]

    candidates = {
        "logistic_regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }
    results = {}
    for name, model in candidates.items():
        model.fit(train_features, train_target)
        predictions = model.predict(validation_features)
        results[name] = {
            "model": model,
            "validation_metrics": classification_metrics(validation_target, predictions),
            "feature_columns": features,
        }
    return results
