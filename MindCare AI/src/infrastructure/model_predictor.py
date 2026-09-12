"""Joblib-backed implementation of the prediction port."""

from pathlib import Path

import joblib
import pandas as pd


class JoblibPredictor:
    """Adapt a serialized model to the application predictor contract."""

    def __init__(self, path: str | Path) -> None:
        self._model = joblib.load(path)

    def predict(self, features: dict[str, float]) -> str:
        """Predict one recommendation from feature values."""
        feature_frame = pd.DataFrame([features])
        model_columns = getattr(self._model, "feature_names_in_", feature_frame.columns)
        feature_frame = feature_frame.reindex(columns=model_columns, fill_value=0)
        prediction = self._model.predict(feature_frame)
        return str(prediction[0])