"""Permanent safeguards against target and post-assessment feature leakage."""

from scripts.train_anxiety_model import FEATURE_COLUMNS as ANXIETY_FEATURE_COLUMNS
from src.config import WEARABLE_FEATURE_COLUMNS


FORBIDDEN_FEATURES = {
    "Anxiety Level (1-10)",
    "Stress Level (1-10)",
    "Severity",
    "Exercises",
    "Sleep_Schedule",
    "Nutrition",
}


def test_severity_model_has_no_leakage_features() -> None:
    assert not FORBIDDEN_FEATURES.intersection(WEARABLE_FEATURE_COLUMNS)


def test_anxiety_model_has_no_leakage_features() -> None:
    assert not FORBIDDEN_FEATURES.intersection(ANXIETY_FEATURE_COLUMNS)