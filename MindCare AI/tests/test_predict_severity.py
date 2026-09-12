"""Behavioral tests for Severity-only production inference."""

import pandas as pd

from scripts.predict_severity import REQUIRED_FIELDS, predict_severity


def _profile(**overrides):
    profile = {
        "Age": 35,
        "Gender": "Female",
        "Occupation": "Engineer",
        "Sleep Hours": 7.5,
        "Physical Activity (hrs/week)": 4.0,
        "Caffeine Intake (mg/day)": 100,
        "Alcohol Consumption (drinks/week)": 2,
        "Smoking": "No",
        "Diet Quality (1-10)": 8,
        "Heart Rate (bpm)": 70,
        "Breathing Rate (breaths/min)": 14,
        "Sweating Level (1-5)": 1,
        "Family History of Anxiety": "No",
        "Dizziness": "No",
        "Medication": "No",
        "Therapy Sessions (per month)": 0,
        "Recent Major Life Event": "No",
    }
    profile.update(overrides)
    return profile


def test_low_risk_profile_returns_minimal_or_mild_with_explanation() -> None:
    result = predict_severity(_profile())

    assert result["severity"] in {"Minimal (1-2)", "Mild (3-4)"}
    assert 0 <= result["confidence"] <= 1
    assert len(result["top_features"]) == 5


def test_high_risk_profile_returns_high_or_severe() -> None:
    result = predict_severity(_profile(**{
        "Age": 29,
        "Sleep Hours": 3.0,
        "Physical Activity (hrs/week)": 0.5,
        "Caffeine Intake (mg/day)": 500,
        "Alcohol Consumption (drinks/week)": 20,
        "Smoking": "Yes",
        "Diet Quality (1-10)": 2,
        "Heart Rate (bpm)": 150,
        "Breathing Rate (breaths/min)": 35,
        "Sweating Level (1-5)": 5,
        "Family History of Anxiety": "Yes",
        "Dizziness": "Yes",
        "Medication": "Yes",
        "Therapy Sessions (per month)": 0,
        "Recent Major Life Event": "Yes",
    }))

    assert result["severity"] in {"High (7-8)", "Severe (9-10)"}


def test_real_processed_test_row_uses_known_severity_label() -> None:
    row = pd.read_csv("data/processed/test.csv").iloc[1]
    gender = next(
        value for value in ("Female", "Male", "Other")
        if row[f"Gender_{value}"] == 1
    )
    occupation = next(
        value for value in (
            "Artist", "Athlete", "Chef", "Doctor", "Engineer", "Freelancer",
            "Lawyer", "Musician", "Nurse", "Other", "Scientist", "Student", "Teacher",
        )
        if row[f"Occupation_{value}"] == 1
    )
    patient = _profile(
        Age=int(row["Age"]),
        **{
            field: row[field]
            for field in REQUIRED_FIELDS
            if field not in {"Age", "Gender", "Occupation"}
        },
    )
    patient["Gender"] = gender
    patient["Occupation"] = occupation
    result = predict_severity(patient)

    assert result["severity"] == row["Severity"]