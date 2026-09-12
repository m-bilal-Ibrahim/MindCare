"""Focused checks for the initial project contracts."""

from pathlib import Path

from src.config import DATA_DIR, MODELS_DIR
from src.data.validate_data import require_columns
from src.application.chat import ChatAssistant
from src.application.recommend import RecommendUser


def test_data_and_model_roots_exist() -> None:
    assert DATA_DIR.is_dir()
    assert MODELS_DIR.is_dir()


def test_require_columns_accepts_and_rejects_schema() -> None:
    import pandas as pd

    require_columns(pd.DataFrame({"target": [1]}), ["target"])
    try:
        require_columns(pd.DataFrame({"value": [1]}), ["target"])
    except ValueError as error:
        assert "target" in str(error)
    else:
        raise AssertionError("Missing columns should raise ValueError")


def test_recommendation_use_case_is_safe_without_approved_model() -> None:
    use_case = RecommendUser()

    assert use_case.execute({"Stress Level (1-10)": 8.0}) == "review_required"


def test_chat_assistant_keeps_the_safety_response_in_the_application_layer() -> None:
    assert "qualified mental-health professional" in ChatAssistant().respond("help")





