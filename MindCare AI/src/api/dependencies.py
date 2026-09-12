"""Composition-root dependencies for the HTTP API."""

from src.application.recommend import RecommendUser
from src.config import PRODUCTION_MODELS_DIR
from src.infrastructure.model_predictor import JoblibPredictor


def get_recommendation_use_case() -> RecommendUser:
    """Build the recommendation use case with the approved model when available."""
    model_path = PRODUCTION_MODELS_DIR / "model.joblib"
    predictor = JoblibPredictor(model_path) if model_path.exists() else None
    return RecommendUser(predictor)