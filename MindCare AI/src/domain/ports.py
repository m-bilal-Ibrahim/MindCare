"""Interfaces used by the application layer."""

from typing import Protocol


class Predictor(Protocol):
    """Port for a trained model that predicts a recommendation."""

    def predict(self, features: dict[str, float]) -> str:
        """Return a recommendation for the supplied features."""