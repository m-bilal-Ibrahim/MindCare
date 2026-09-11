"""Resolve the currently approved production model."""

from pathlib import Path

from src.config import PRODUCTION_MODELS_DIR


def current_model_path(filename: str = "model.joblib") -> Path:
    """Return the path reserved for the approved model artifact."""
    return PRODUCTION_MODELS_DIR / filename
