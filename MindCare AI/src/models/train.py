"""Model training entry points."""

from pathlib import Path

import joblib


def save_model(model, path: str | Path) -> Path:
    """Persist a fitted model artifact and return its path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, destination)
    return destination
