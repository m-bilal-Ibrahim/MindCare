"""Inference helpers."""

from pathlib import Path

import joblib


def load_model(path: str | Path):
    """Load a serialized model artifact."""
    return joblib.load(path)


def predict(model, features):
    """Generate predictions from a fitted model."""
    return model.predict(features)
