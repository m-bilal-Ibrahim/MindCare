"""Extremes sweep for the served 11-feature v2 XGBoost: which inputs the model ignores at
clinically extreme values.

Changes one numeric input at a time on four reference patients, from normal values out to the
extremes the API accepts, and records the predicted class and P(High). Requests go through the
real POST /predict pipeline in-process (validation, caffeine/PSS conversion, preprocessing,
model), so this measures the served behaviour, safety rules included.

Four hand-picked patients, not a population: the result says what the model cannot respond to,
not how accurate it is. Run with: python -m src.evaluation.extremes_sweep_11feature_v2
Writes reports/extremes_sweep_11feature_v2.{md,json}.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import COFFEE_MG_PER_CUP, HIGH_PROBA_THRESHOLD, app
from src.inference.input_validation import NUMERIC_RANGES
from src.inference.predict_single import EXAMPLE_PATIENTS

ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "reports" / "extremes_sweep_11feature_v2.md"
REPORT_JSON = ROOT / "reports" / "extremes_sweep_11feature_v2.json"


def _api_patient(name: str, **servings: int) -> dict:
    """An EXAMPLE_PATIENTS entry with its raw mg caffeine replaced by serving counts."""
    patient = {k: v for k, v in EXAMPLE_PATIENTS[name].items() if k != "Caffeine Intake (mg/day)"}
    for field in ("cups_of_coffee", "cups_of_tea", "energy_drinks", "cans_of_soda"):
        patient[field] = servings.get(field, 0)
    return patient


BASES = {
    "low_risk": _api_patient("clearly_low_risk", cups_of_coffee=1),
    "moderate": _api_patient("ambiguous_moderate", cups_of_coffee=2, cups_of_tea=2),
    # The manual test form's default values (src/api/static/manual_test_form.html).
    "form_default": {
        "Age": 30, "Sleep Hours": 7, "Physical Activity (hrs/week)": 3, "cups_of_coffee": 1,
        "cups_of_tea": 0, "energy_drinks": 0, "cans_of_soda": 0, "pss_uncontrollable": 2,
        "pss_confident": 2, "pss_going_your_way": 2, "pss_difficulties_piling_up": 2,
        "Heart Rate (bpm)": 80, "Breathing Rate (breaths/min)": 16,
        "Therapy Sessions (per month)": 1, "Diet Quality (1-10)": 6, "Occupation": "Student",
        "Family History of Anxiety": "No",
    },
    "high_risk": _api_patient("clearly_high_risk", cups_of_coffee=5, energy_drinks=1),
}

# Caffeine is swept as coffee cups (other servings set to 0): 0-12 cups = 0-1140 mg.
SWEEPS = {
    "Heart Rate (bpm)": [30, 40, 50, 60, 70, 80, 90, 100, 110, 119, 130, 150, 180, 220],
    "Breathing Rate (breaths/min)": [5, 8, 10, 12, 16, 20, 25, 29, 35, 40, 50, 60],
    "Sleep Hours": [0, 2, 2.3, 4, 6, 8, 10, 11.3, 14, 18, 24],
    "cups_of_coffee": list(range(13)),
    "Physical Activity (hrs/week)": [0, 2, 5, 10.1, 20, 40, 80, 168],
    "Therapy Sessions (per month)": [0, 2, 4, 8, 12, 20, 31],
    "Diet Quality (1-10)": [0, 1, 3, 5, 8, 10, 12],
}


def _observed_range(feature: str) -> tuple[float, float]:
    if feature == "cups_of_coffee":
        caffeine = NUMERIC_RANGES["Caffeine Intake (mg/day)"]
        return caffeine.observed_min / COFFEE_MG_PER_CUP, caffeine.observed_max / COFFEE_MG_PER_CUP
    bounds = NUMERIC_RANGES[feature]
    return bounds.observed_min, bounds.observed_max


def run_sweep() -> dict[str, dict[str, list[dict]]]:
    results: dict[str, dict[str, list[dict]]] = {}
    with TestClient(app) as client:
        for base_name, base in BASES.items():
            results[base_name] = {}
            for feature, values in SWEEPS.items():
                rows = []
                for value in values:
                    patient = dict(base)
                    if feature == "cups_of_coffee":
                        patient.update(cups_of_tea=0, energy_drinks=0, cans_of_soda=0)
                    patient[feature] = value
                    response = client.post("/predict", json=patient)
                    response.raise_for_status()
                    body = response.json()
                    rows.append({
                        "value": value,
                        "predicted_class": body["predicted_class"],
                        "p_high": body["probabilities"]["High"],
                        "review_reasons": body["review_reasons"],
                    })
                results[base_name][feature] = rows
    return results


def _summary(rows: list[dict], feature: str) -> dict:
    """P(High) span, and whether output is flat beyond the training range (same class and
    P(High) within 1e-4 of the nearest in-range sweep value)."""
    low, high = _observed_range(feature)
    inside = [r for r in rows if low <= r["value"] <= high]
    edge_low, edge_high = inside[0], inside[-1]

    def same(a: dict, b: dict) -> bool:
        return a["predicted_class"] == b["predicted_class"] and abs(a["p_high"] - b["p_high"]) < 1e-4

    below = [r for r in rows if r["value"] < low]
    above = [r for r in rows if r["value"] > high]
    return {
        "p_high_min": min(r["p_high"] for r in rows),
        "p_high_max": max(r["p_high"] for r in rows),
        "model_flag_values": [r["value"] for r in rows if r["p_high"] >= HIGH_PROBA_THRESHOLD],
        "flat_below_training_range": all(same(r, edge_low) for r in below) if below else None,
        "flat_above_training_range": all(same(r, edge_high) for r in above) if above else None,
    }


def write_report(results: dict) -> None:
    summaries = {b: {f: _summary(rows, f) for f, rows in feats.items()} for b, feats in results.items()}
    REPORT_JSON.write_text(json.dumps({"results": results, "summaries": summaries}, indent=1))

    lines = [
        "# Extremes sweep — 11-feature v2 XGBoost (served model)",
        "",
        f"Generated by `src/evaluation/extremes_sweep_11feature_v2.py`. One numeric input changed at a",
        "time on four reference patients, through the real `POST /predict` pipeline. **Four hand-picked",
        "patients, not a population**: this shows what the model cannot respond to, not how accurate",
        f"it is. Model review threshold: P(High) ≥ {HIGH_PROBA_THRESHOLD}. Caffeine is swept as cups of",
        f"coffee ({COFFEE_MG_PER_CUP} mg each). \"Flat\" = same class and P(High) within 0.0001 of the",
        "nearest in-range value; the training range is the observed min-max in the raw data.",
        "",
        "## Summary: P(High) span and flatness outside the training range",
        "",
        "| Patient | Input | P(High) min–max | Model flag at | Flat below range | Flat above range |",
        "|---|---|---|---|---|---|",
    ]
    for base, feats in summaries.items():
        for feature, s in feats.items():
            flag = ", ".join(str(v) for v in s["model_flag_values"]) or "never"
            def fmt(x):
                return "—" if x is None else ("yes" if x else "no")
            lines.append(f"| {base} | {feature} | {s['p_high_min']:.3f}–{s['p_high_max']:.3f} | {flag} | "
                         f"{fmt(s['flat_below_training_range'])} | {fmt(s['flat_above_training_range'])} |")

    lines += ["", "## Full results (class / P(High); * = review flag set by any rule)", ""]
    for feature in SWEEPS:
        lines += [f"### {feature}", "", "| Value | " + " | ".join(BASES) + " |",
                  "|---" * (len(BASES) + 1) + "|"]
        for i, value in enumerate(SWEEPS[feature]):
            cells = []
            for base in BASES:
                r = results[base][feature][i]
                cells.append(f"{r['predicted_class']} / {r['p_high']:.3f}{' *' if r['review_reasons'] else ''}")
            lines.append(f"| {value} | " + " | ".join(cells) + " |")
        lines.append("")

    lines += [
        "## Findings",
        "",
        "1. **Heart rate and breathing rate barely affect the model, even at dangerous values.** For the",
        "   low-risk, moderate and form-default patients, heart rate 30–220 bpm moves P(High) by at most",
        "   0.001 and breathing rate 5–60/min by nothing; neither ever reaches the review threshold.",
        "2. **Inputs stop having any effect outside their training range.** Tree models cannot",
        "   extrapolate, so for example 220 bpm is treated exactly like 119 bpm, and 0 hours of sleep",
        "   like 2.3. Caffeine shows \"no\" above only because its one step falls between the last",
        "   in-range sweep value (570 mg) and the first out-of-range one (665 mg); it is flat from",
        "   665 mg up.",
        "3. **Caffeine is the only input that triggers the model flag on its own**, at about 600 mg/day",
        "   (7 cups) for the moderate and form-default patients, and it is flat above that.",
        "4. **More therapy sessions raise P(High)**: the count acts as a marker of existing treatment.",
        "5. **Diet quality has no effect** on these patients.",
        "",
        "## What changed because of this",
        "",
        "A safety rule outside the model (`src/api/main.py`, added 2026-11-10) forces the review flag",
        "for heart rate below 40 or above 130 bpm, or breathing below 8 or above 30 per minute",
        "(`review_reasons: [\"abnormal_vital_signs\"]`), with a warning suggesting medical follow-up.",
        "It sits beside the severe-sleep rule (Sleep Hours < 4). **Both sets of cutoffs are provisional",
        "and need clinical sign-off.** Rows marked * above include flags from these rules.",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    write_report(run_sweep())
    print(f"Wrote {REPORT_MD.relative_to(ROOT)} and {REPORT_JSON.relative_to(ROOT)}")
