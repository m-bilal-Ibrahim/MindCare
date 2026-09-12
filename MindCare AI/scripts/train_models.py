"""Train baseline severity models and save the selected production model."""

import json

import pandas as pd

from src.config import (
    EXPERIMENT_MODELS_DIR,
    PROCESSED_DATA_DIR,
    PRODUCTION_MODELS_DIR,
    REPORTS_DIR,
    TARGET_COLUMN,
    WEARABLE_FEATURE_COLUMNS,
)
from src.models.evaluate import classification_metrics
from src.models.train import save_model, train_candidates


def main() -> None:
    """Train candidates, select by validation macro-F1, and evaluate once on test data."""
    train_data = pd.read_csv(PROCESSED_DATA_DIR / "train_scaled.csv")
    validation_data = pd.read_csv(PROCESSED_DATA_DIR / "val_scaled.csv")
    test_data = pd.read_csv(PROCESSED_DATA_DIR / "test_scaled.csv")

    candidates = train_candidates(
        train_data,
        validation_data,
        feature_columns=WEARABLE_FEATURE_COLUMNS,
    )
    selected_name = max(
        candidates,
        key=lambda name: candidates[name]["validation_metrics"]["macro_f1"],
    )
    selected = candidates[selected_name]

    test_features = list(WEARABLE_FEATURE_COLUMNS)
    test_predictions = selected["model"].predict(test_data[test_features])
    metrics = {
        "selected_model": selected_name,
        "candidates": {
            name: result["validation_metrics"] for name, result in candidates.items()
        },
        "test": classification_metrics(test_data[TARGET_COLUMN], test_predictions),
        "feature_columns": test_features,
    }

    EXPERIMENT_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, result in candidates.items():
        save_model(result["model"], EXPERIMENT_MODELS_DIR / f"{name}.joblib")

    REPORTS_DIR.joinpath("metrics").mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "metrics" / "baseline_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n",
        encoding="utf-8",
    )
    save_model(selected["model"], PRODUCTION_MODELS_DIR / "model.joblib")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()