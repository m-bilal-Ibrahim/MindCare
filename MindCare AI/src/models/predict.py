"""Backward-compatible model inference exports."""

from pathlib import Path

from src.infrastructure.model_predictor import JoblibPredictor


def load_model(path: str | Path):
    """Load a serialized model artifact."""
    return JoblibPredictor(path)


def predict(model, features):
    """Generate predictions from a fitted model."""
    return model.predict(features)
