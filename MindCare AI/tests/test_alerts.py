"""Tests for the alert layer (src/inference/alerts.py) and its place in the API responses.

Run with: pytest tests/test_alerts.py -v
"""

from __future__ import annotations

import math

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from src.api.main import app
from src.inference.alerts import AlertThresholds, evaluate_alerts, load_thresholds

THRESHOLDS = load_thresholds()

# A patient that trips no flag: every value sits well inside its threshold.
QUIET = {
    "Sleep Hours": 7.5,
    "Stress Level (1-10)": 4,
    "Heart Rate (bpm)": 75,
    "Breathing Rate (breaths/min)": 16,
    "Caffeine Intake (mg/day)": 150,
    "Diet Quality (1-10)": 7,
}

ALERT_FIELDS = {"alert_flags", "alert_flag_count", "attention_level", "model_class", "final_risk_class"}


def _flag_names(features: dict, model_class: str = "Low") -> list[str]:
    return [f["name"] for f in evaluate_alerts(features, model_class, THRESHOLDS)["alert_flags"]]


def test_config_file_has_the_draft_values():
    assert THRESHOLDS == AlertThresholds(
        sleep_hours_max=3, stress_min=8, heart_rate_min=115, breathing_rate_min=27,
        caffeine_mg_min=520, diet_quality_below=4,
    )


def test_quiet_patient_is_clear():
    result = evaluate_alerts(QUIET, "Medium", THRESHOLDS)
    assert result == {
        "alert_flags": [], "alert_flag_count": 0, "attention_level": "clear",
        "model_class": "Medium", "final_risk_class": "Medium",
    }


# (flag, feature, just below, at, just above, fires at/below/above)
BOUNDARIES = [
    ("low_sleep", "Sleep Hours", 2.9, 3, 3.1, (True, True, False)),
    ("high_stress", "Stress Level (1-10)", 7, 8, 9, (False, True, True)),
    ("high_heart_rate", "Heart Rate (bpm)", 114.9, 115, 115.1, (False, True, True)),
    ("high_breathing_rate", "Breathing Rate (breaths/min)", 26.9, 27, 27.1, (False, True, True)),
    ("high_caffeine", "Caffeine Intake (mg/day)", 519.9, 520, 520.1, (False, True, True)),
    ("low_diet_quality", "Diet Quality (1-10)", 3.9, 4, 4.1, (True, False, False)),
]


@pytest.mark.parametrize("flag,feature,below,at,above,fires", BOUNDARIES, ids=[b[0] for b in BOUNDARIES])
def test_each_threshold_at_and_around_its_boundary(flag, feature, below, at, above, fires):
    for value, should_fire in zip((below, at, above), fires):
        names = _flag_names({**QUIET, feature: value})
        assert (flag in names) is should_fire, f"{feature}={value}"
        assert names == ([flag] if should_fire else []), "a flag must fire on its own value alone"


def test_flag_reports_value_and_threshold():
    flag = evaluate_alerts({**QUIET, "Heart Rate (bpm)": 120}, "Low", THRESHOLDS)["alert_flags"][0]
    assert flag == {"name": "high_heart_rate", "feature": "Heart Rate (bpm)", "value": 120, "threshold": 115}


def test_sleep_two_is_urgent_and_final_high_but_model_class_untouched():
    result = evaluate_alerts({**QUIET, "Sleep Hours": 2}, "Low", THRESHOLDS)
    assert result["attention_level"] == "urgent"
    assert result["final_risk_class"] == "High"
    assert result["model_class"] == "Low"


def test_model_high_is_urgent_without_any_flag():
    result = evaluate_alerts(QUIET, "High", THRESHOLDS)
    assert result["alert_flag_count"] == 0
    assert result["attention_level"] == "urgent"
    assert result["final_risk_class"] == "High"


def test_two_flags_are_elevated():
    result = evaluate_alerts({**QUIET, "Stress Level (1-10)": 9, "Diet Quality (1-10)": 2}, "Medium", THRESHOLDS)
    assert result["alert_flag_count"] == 2
    assert result["attention_level"] == "elevated"
    assert result["final_risk_class"] == "Medium"


def test_one_flag_is_notice():
    result = evaluate_alerts({**QUIET, "Caffeine Intake (mg/day)": 600}, "Low", THRESHOLDS)
    assert result["alert_flag_count"] == 1
    assert result["attention_level"] == "notice"
    assert result["final_risk_class"] == "Low"


def test_only_sleep_overrides_the_class():
    everything_but_sleep = {
        **QUIET, "Stress Level (1-10)": 10, "Heart Rate (bpm)": 130, "Breathing Rate (breaths/min)": 30,
        "Caffeine Intake (mg/day)": 700, "Diet Quality (1-10)": 1,
    }
    result = evaluate_alerts(everything_but_sleep, "Low", THRESHOLDS)
    assert result["alert_flag_count"] == 5
    assert result["attention_level"] == "elevated"
    assert result["final_risk_class"] == "Low"


@pytest.mark.parametrize("missing", [None, math.nan, "n/a"])
def test_missing_values_skip_their_flag(missing):
    features = {**QUIET, "Sleep Hours": missing, "Heart Rate (bpm)": 130}
    del features["Diet Quality (1-10)"]
    result = evaluate_alerts(features, "Low", THRESHOLDS)
    assert [f["name"] for f in result["alert_flags"]] == ["high_heart_rate"]
    assert result["attention_level"] == "notice"


def test_empty_features_are_clear():
    assert evaluate_alerts({}, "Low", THRESHOLDS)["attention_level"] == "clear"


def test_bad_config_fails_loudly(tmp_path):
    missing_key = tmp_path / "missing.toml"
    missing_key.write_text("sleep_hours_max = 3\n")
    with pytest.raises(ValueError, match="missing"):
        load_thresholds(missing_key)
    not_a_number = tmp_path / "text.toml"
    not_a_number.write_text(
        'sleep_hours_max = "3"\nstress_min = 8\nheart_rate_min = 115\nbreathing_rate_min = 27\n'
        "caffeine_mg_min = 520\ndiet_quality_below = 4\n"
    )
    with pytest.raises(ValueError, match="must be a number"):
        load_thresholds(not_a_number)


# --- API ----------------------------------------------------------------------------------------

PAYLOAD = {
    "Age": 34, "Sleep Hours": 8.2, "Physical Activity (hrs/week)": 5.5,
    "cups_of_coffee": 1, "cups_of_tea": 0, "energy_drinks": 0, "cans_of_soda": 0,
    "pss_uncontrollable": 0, "pss_confident": 3, "pss_going_your_way": 4, "pss_difficulties_piling_up": 0,
    "Heart Rate (bpm)": 68, "Breathing Rate (breaths/min)": 14, "Therapy Sessions (per month)": 0,
    "Diet Quality (1-10)": 9, "Occupation": "Teacher", "Family History of Anxiety": "No",
}

# Every route of the service and whether it may carry the alert fields. Only psychologist-facing
# prediction routes may. A new route fails this test until it is consciously added here.
ROUTES_WITH_ALERTS = {"/predict": True, "/patient-summary": True, "/health": False, "/form": False}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_predict_returns_alert_fields(client):
    body = client.post("/predict", json=PAYLOAD).json()
    assert ALERT_FIELDS <= body.keys()
    assert body["model_class"] == body["predicted_class"]
    assert body["attention_level"] == "clear"
    assert body["final_risk_class"] == body["predicted_class"]


def test_predict_uses_the_computed_caffeine_and_stress(client):
    # 6 cups of coffee = 570 mg; PSS answers 4,0,0,4 = the most stressed pattern = Stress Level 10.
    payload = {**PAYLOAD, "cups_of_coffee": 6, "pss_uncontrollable": 4, "pss_confident": 0,
               "pss_going_your_way": 0, "pss_difficulties_piling_up": 4}
    body = client.post("/predict", json=payload).json()
    flags = {f["name"]: f["value"] for f in body["alert_flags"]}
    assert flags == {"high_caffeine": 570, "high_stress": 10}


def test_sleep_two_through_the_api_keeps_the_model_class(client):
    body = client.post("/predict", json={**PAYLOAD, "Sleep Hours": 2}).json()
    assert body["attention_level"] == "urgent"
    assert body["final_risk_class"] == "High"
    assert body["model_class"] == body["predicted_class"]


def test_patient_summary_returns_alert_fields(client):
    body = client.post("/patient-summary", json={**PAYLOAD, "Sleep Hours": 2}).json()
    assert ALERT_FIELDS <= body.keys()
    assert body["final_risk_class"] == "High"


def test_no_other_route_returns_alert_fields(client):
    routes = {route.path: route for route in app.routes if isinstance(route, APIRoute)}
    assert set(routes) == set(ROUTES_WITH_ALERTS), "new route: decide whether it may carry alert fields"
    for path, allowed in ROUTES_WITH_ALERTS.items():
        model = routes[path].response_model
        has_fields = model is not None and ALERT_FIELDS <= set(model.model_fields)
        assert has_fields is allowed, path
    health = client.get("/health").json()
    assert not ALERT_FIELDS & health.keys()
    assert "attention_level" not in client.get("/form").text
