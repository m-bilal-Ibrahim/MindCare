"""Recommendation use case."""

from src.domain.ports import Predictor


class RecommendUser:
    """Coordinate recommendation policy independently of delivery details."""

    def __init__(self, predictor: Predictor | None = None) -> None:
        self._predictor = predictor

    def execute(self, features: dict[str, float]) -> str:
        """Return a model recommendation or require professional review."""
        if self._predictor is None:
            return "review_required"
        return self._predictor.predict(features)