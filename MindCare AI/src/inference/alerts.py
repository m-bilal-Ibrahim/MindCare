"""Alert layer: rule-based flags on single input values, next to the model's prediction.

Psychologist-facing only - like every output of this service, nothing here may reach a patient
without psychologist review. It changes nothing about the XGBoost model or its preprocessing: the
rules read the same inputs the model gets and only add fields to the response.

Each flag fires on one value alone, whatever the other inputs are. The thresholds live in
src/config/alert_thresholds.toml, are hand-picked clinical-guidance-style cut-offs (NOT learned from
data, not validated) and are drafts pending psychologist review.

attention_level, for sorting a review queue:
  urgent    the model predicts High, or the low-sleep flag fired
  elevated  not urgent, 2 or more flags
  notice    not urgent, exactly 1 flag
  clear     otherwise

final_risk_class is the model's class, except that the low-sleep flag overrides it to High. That
override is a rule, not a prediction: model_class always keeps the model's own answer.

Measured on all 11,000 dataset rows (docs/api_usage.md, "Alert layer"): about 69% of rows get at
least one flag and 29% two or more, mostly from the stress and diet rules, so "notice" and
"elevated" are common. Low sleep is rare (0.2%) and 94% of those rows are truly High.
"""

from __future__ import annotations

import math
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ALERT_THRESHOLDS_PATH = Path(__file__).resolve().parents[1] / "config" / "alert_thresholds.toml"

ATTENTION_LEVELS = ("urgent", "elevated", "notice", "clear")
LOW_SLEEP = "low_sleep"


@dataclass(frozen=True)
class AlertThresholds:
    sleep_hours_max: float
    stress_min: float
    heart_rate_min: float
    breathing_rate_min: float
    caffeine_mg_min: float
    diet_quality_below: float


def load_thresholds(path: Path = ALERT_THRESHOLDS_PATH) -> AlertThresholds:
    """Read the thresholds file. Raises ValueError on a missing, unknown or non-numeric key, so a
    bad edit stops the service at startup instead of silently disabling an alert."""
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    expected = set(AlertThresholds.__dataclass_fields__)
    if set(raw) != expected:
        raise ValueError(f"{path.name}: missing {sorted(expected - set(raw))}, unknown {sorted(set(raw) - expected)}")
    for key, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{path.name}: {key} must be a number, got {value!r}")
    return AlertThresholds(**raw)


def _rules(t: AlertThresholds) -> list[tuple[str, str, float, Callable[[float, float], bool]]]:
    # (flag name, input feature, threshold, fires(value, threshold))
    return [
        (LOW_SLEEP, "Sleep Hours", t.sleep_hours_max, lambda v, th: v <= th),
        ("high_stress", "Stress Level (1-10)", t.stress_min, lambda v, th: v >= th),
        ("high_heart_rate", "Heart Rate (bpm)", t.heart_rate_min, lambda v, th: v >= th),
        ("high_breathing_rate", "Breathing Rate (breaths/min)", t.breathing_rate_min, lambda v, th: v >= th),
        ("high_caffeine", "Caffeine Intake (mg/day)", t.caffeine_mg_min, lambda v, th: v >= th),
        ("low_diet_quality", "Diet Quality (1-10)", t.diet_quality_below, lambda v, th: v < th),
    ]


def _usable(value: object) -> bool:
    """A missing, null, non-numeric or NaN value skips its flag rather than failing."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return not math.isnan(value)


def evaluate_alerts(features: dict, model_class: str, thresholds: AlertThresholds) -> dict:
    """Return the alert fields for one patient. Pure: no I/O, no model call.

    features: feature name -> value, using the model's column names (Caffeine Intake (mg/day) and
    Stress Level (1-10) are the server-computed values). model_class: the model's predicted class.
    """
    flags = []
    for name, feature, threshold, fires in _rules(thresholds):
        value = features.get(feature)
        if _usable(value) and fires(value, threshold):
            flags.append({"name": name, "feature": feature, "value": value, "threshold": threshold})

    low_sleep = any(flag["name"] == LOW_SLEEP for flag in flags)
    if model_class == "High" or low_sleep:
        attention_level = "urgent"
    elif len(flags) >= 2:
        attention_level = "elevated"
    elif len(flags) == 1:
        attention_level = "notice"
    else:
        attention_level = "clear"

    return {
        "alert_flags": flags,
        "alert_flag_count": len(flags),
        "attention_level": attention_level,
        "model_class": model_class,
        "final_risk_class": "High" if low_sleep else model_class,
    }
