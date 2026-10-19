"""Does the alert layer cover the low-caffeine true-High gap found by SHAP, and at what cost?

Validation/CV only: the 1,650 test rows are never loaded (the 3-class test set is spent). Uses the alert
layer and its DRAFT thresholds exactly as committed (src/inference/alerts.py,
src/config/alert_thresholds.toml); changes no served file, threshold or alert rule.

Out-of-fold predictions are rebuilt exactly as src/explainability/shap_v2.py does (branch ai/shap-v2):
the 9,350 train + validation rows, 5-fold stratified on the 3-class label, shuffled, seed 42, the served
v2 XGBoost hyperparameters, preprocessing fitted inside each fold. Two guards stop the script if the
rebuild drifts:
- the low-caffeine group (true High, caffeine <= 200 mg/day) must be the same 23 rows with 0 predicted
  High and 12 review-flagged (reports/shap_v2.md, section 5);
- the review flag over all rows must catch 931 of 968 true High and flag 2,361 patients
  (reports/calibration_review_flag_11feature_v2.md, out-of-fold, threshold 0.025).

Coverage: the alert layer on the 23 rows. Cost: stress >= 8 and attention levels by true class over all
9,350 rows, and the catch rate and volume of "review flag OR any alert".

Caveat: Stress Level here is the dataset's raw 1-10 column. In the live API it is computed from the four
PSS-4 answers, so whether the stress alert fires for a real patient depends on those answers.

Run from MindCare AI/: python -m src.experiments.alert_coverage_shap_gap
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level
from src.inference.alerts import ATTENTION_LEVELS, evaluate_alerts, load_thresholds

SEED = 42
FOLDS = 5
HIGH = 2
CLASSES = ["Low", "Medium", "High"]
REVIEW_THRESHOLD = 0.025  # read-only copy of the served HIGH_PROBA_THRESHOLD
CAFFEINE_LIMIT = 200
GUARD_GROUP = {"rows": 23, "predicted_high": 0, "review_flagged": 12}
GUARD_ALL = {"true_high_caught": 931, "true_high": 968, "flagged": 2361}

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
V2_TUNING_PATH = ROOT / "reports" / "tuning_results_12feature.json"
REPORT_MD = ROOT / "reports" / "alert_coverage_shap_gap.md"

NUMERIC = [
    "Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
    "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
    "Diet Quality (1-10)", "Age",
]
CATEGORICAL = ["Occupation", "Family History of Anxiety"]
FEATURES = NUMERIC + CATEGORICAL


def out_of_fold() -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as s:
        rows = np.concatenate([s["train_original_idx"], s["val_original_idx"]])  # no test rows
    assert len(rows) == 9350
    df = raw.iloc[rows].reset_index(drop=True)
    y = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    params = json.loads(V2_TUNING_PATH.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]
    proba = np.zeros((len(df), 3))
    for tr, te in StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y):
        pre = ColumnTransformer([("num", StandardScaler(), NUMERIC),
                                 ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
        model = XGBClassifier(**params, objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
        model.fit(pre.fit_transform(df.iloc[tr][FEATURES]), y[tr])
        proba[te] = model.predict_proba(pre.transform(df.iloc[te][FEATURES]))
    return df, rows, y, proba


def main() -> None:
    thresholds = load_thresholds()
    df, rows, y, proba = out_of_fold()
    pred = proba.argmax(axis=1)
    review = proba[:, HIGH] >= REVIEW_THRESHOLD

    alerts = [evaluate_alerts({f: (float(df.at[i, f]) if f in NUMERIC else df.at[i, f]) for f in FEATURES},
                              CLASSES[pred[i]], thresholds) for i in range(len(df))]
    any_alert = np.array([a["alert_flag_count"] > 0 for a in alerts])
    stress_alert = np.array([any(f["name"] == "high_stress" for f in a["alert_flags"]) for a in alerts])
    attention = np.array([a["attention_level"] for a in alerts])
    either = review | any_alert
    is_high = y == HIGH

    # ---- Guards: the rebuild must match shap_v2 and the calibration report. ----
    group = np.where(is_high & (df["Caffeine Intake (mg/day)"].to_numpy() <= CAFFEINE_LIMIT))[0]
    guard_group = {"rows": len(group), "predicted_high": int((pred[group] == HIGH).sum()),
                   "review_flagged": int(review[group].sum())}
    guard_all = {"true_high_caught": int((review & is_high).sum()), "true_high": int(is_high.sum()),
                 "flagged": int(review.sum())}
    print("guards:", guard_group, guard_all)
    if guard_group != GUARD_GROUP or guard_all != GUARD_ALL:
        raise SystemExit(f"STOP: out-of-fold rebuild does not match: {guard_group} / {guard_all}")

    # ---- Coverage: the 23 rows. ----
    group_rows = [{"row": int(rows[i]), "stress": float(df.at[i, "Stress Level (1-10)"]), "sleep": float(df.at[i, "Sleep Hours"]),
                   "caffeine": float(df.at[i, "Caffeine Intake (mg/day)"]), "model_class": CLASSES[pred[i]],
                   "p_high": float(proba[i, HIGH]), "review": bool(review[i]),
                   "alerts": [f["name"] for f in alerts[i]["alert_flags"]], "attention": alerts[i]["attention_level"],
                   "final_risk_class": alerts[i]["final_risk_class"]} for i in group]
    g = {"stress_alert": int(stress_alert[group].sum()), "any_alert": int(any_alert[group].sum()),
         "review": int(review[group].sum()), "either": int(either[group].sum()),
         "alerts_only": int((any_alert & ~review)[group].sum()), "neither": int((~either)[group].sum()),
         "attention": {lvl: int((attention[group] == lvl).sum()) for lvl in ATTENTION_LEVELS},
         "final_high": sum(r["final_risk_class"] == "High" for r in group_rows)}

    # ---- Cost: all 9,350 rows by true class. ----
    by_class = {}
    for k, c in enumerate(CLASSES):
        m = y == k
        by_class[c] = {"rows": int(m.sum()), "stress_alert": int((stress_alert & m).sum()),
                       "any_alert": int((any_alert & m).sum()), "review": int((review & m).sum()),
                       "either": int((either & m).sum()), "stress_and_review": int((stress_alert & review & m).sum()),
                       "attention": {lvl: int(((attention == lvl) & m).sum()) for lvl in ATTENTION_LEVELS}}
    n = len(df)
    totals = {"rows": n, "stress_alert": int(stress_alert.sum()), "any_alert": int(any_alert.sum()),
              "review": int(review.sum()), "either": int(either.sum()), "stress_and_review": int((stress_alert & review).sum()),
              "attention": {lvl: int((attention == lvl).sum()) for lvl in ATTENTION_LEVELS}}
    catch = {"review": int((review & is_high).sum()), "any_alert": int((any_alert & is_high).sum()),
             "either": int((either & is_high).sum()), "true_high": int(is_high.sum())}
    print("coverage of the 23:", g)
    print("catch of all true High:", catch, "| totals:", {k: v for k, v in totals.items() if k != "attention"})
    write_markdown(group_rows, g, by_class, totals, catch, thresholds)
    print(f"wrote {REPORT_MD.relative_to(ROOT)}")


def pct(a: int, b: int) -> str:
    return f"{a:,} ({a / b:.1%})"


def write_markdown(group_rows, g, by_class, totals, catch, t) -> None:
    n23 = len(group_rows)
    row_lines = ["| Row | Stress | Sleep (h) | Caffeine (mg) | Model class | P(High) | Review flag | Attention | Alerts |",
                 "|---|---|---|---|---|---|---|---|---|"]
    row_lines += [f"| {r['row']} | {r['stress']:.0f} | {r['sleep']:.1f} | {r['caffeine']:.0f} | {r['model_class']} | {r['p_high']:.4f} | "
                  f"{'yes' if r['review'] else 'no'} | {r['attention']} | {', '.join(r['alerts']) or '—'} |" for r in group_rows]
    att_lines = ["| True class | Rows | " + " | ".join(ATTENTION_LEVELS) + " |", "|---" * (2 + len(ATTENTION_LEVELS)) + "|"]
    for c, v in [*by_class.items(), ("**All**", totals)]:
        att_lines.append(f"| {c} | {v['rows']:,} | " + " | ".join(pct(v["attention"][lvl], v["rows"]) for lvl in ATTENTION_LEVELS) + " |")
    cost_lines = ["| True class | Rows | Stress ≥ 8 alert | Any alert | Review flag (P(High) ≥ 0.025) | Review flag OR any alert | Stress alert AND review flag |",
                  "|---|---|---|---|---|---|---|"]
    for c, v in [*by_class.items(), ("**All**", totals)]:
        cost_lines.append(f"| {c} | {v['rows']:,} | {pct(v['stress_alert'], v['rows'])} | {pct(v['any_alert'], v['rows'])} | "
                          f"{pct(v['review'], v['rows'])} | {pct(v['either'], v['rows'])} | {pct(v['stress_and_review'], v['rows'])} |")
    hi = catch["true_high"]
    lo, me = by_class["Low"], by_class["Medium"]

    REPORT_MD.write_text(f"""# Alert layer vs the low-caffeine true-High gap: coverage and cost

Script: `src/experiments/alert_coverage_shap_gap.py`. **The test set was not used.** Out-of-fold over the 9,350
train + validation rows, rebuilt exactly as `src/explainability/shap_v2.py` does (5-fold stratified on the 3-class
label, shuffled, seed 42, served v2 hyperparameters, preprocessing fitted inside each fold); guarded to reproduce
the same 23 low-caffeine true-High rows (0 predicted High, 12 review-flagged) and the review flag's overall
931/968 catch with 2,361 flagged. Alert layer and **draft thresholds unchanged** (`src/config/alert_thresholds.toml`:
sleep ≤ {t.sleep_hours_max:g}, stress ≥ {t.stress_min:g}, HR ≥ {t.heart_rate_min:g}, BR ≥ {t.breathing_rate_min:g},
caffeine ≥ {t.caffeine_mg_min:g}, diet < {t.diet_quality_below:g}); attention level uses the out-of-fold model class.
Stress here is the dataset's raw 1-10 column; in the live API it comes from the four PSS-4 answers.

## 1. Coverage: the {n23} true-High patients with caffeine ≤ 200 mg/day

{chr(10).join(row_lines)}

- Stress ≥ 8 alert: **{g['stress_alert']} of {n23}**; any alert: {g['any_alert']} of {n23}.
- Attention level: {', '.join(f"{lvl} {g['attention'][lvl]}" for lvl in ATTENTION_LEVELS)}. Final risk class High: {g['final_high']} of {n23}.
- Review flag: {g['review']} of {n23}; **review flag OR any alert: {g['either']} of {n23}**
  ({g['alerts_only']} only through an alert, {g['neither']} caught by neither).

## 2. Cost: all 9,350 patients by true class (out-of-fold)

{chr(10).join(cost_lines)}

Attention level by true class:

{chr(10).join(att_lines)}

Catch rate of true-High patients (n = {hi}): review flag alone {pct(catch['review'], hi)}; any alert alone
{pct(catch['any_alert'], hi)}; **review flag OR any alert {pct(catch['either'], hi)}**. Patients flagged by that
combination: **{pct(totals['either'], totals['rows'])}** of all 9,350, against {pct(totals['review'], totals['rows'])} for the
review flag alone.

## 3. Conclusion

The alert layer closes the coverage gap: every one of the {n23} low-caffeine true-High patients gets a stress ≥ 8
alert, so "review flag OR any alert" catches {g['either']} of {n23} where the review flag alone catches {g['review']}.
But it does so only at a low priority — {g['attention']['notice']} get "notice" and {g['attention']['elevated']} "elevated",
none "urgent", and all stay Medium — and the cost is volume: the stress alert fires for
{pct(lo['stress_alert'], lo['rows'])} of Low and {pct(me['stress_alert'], me['rows'])} of Medium patients, and "review
flag OR any alert" marks {pct(totals['either'], totals['rows'])} of all patients (review flag alone:
{pct(totals['review'], totals['rows'])}). In practice the combination raises the true-High catch rate from
{catch['review'] / hi:.1%} to {catch['either'] / hi:.1%} by putting most patients on the reviewer's list, so it is not a
targeted fix for this gap. Very likely synthetic data; draft thresholds pending psychologist review.

## 4. Open question for the psychologist (not implemented)

**Should a stress alert together with P(High) ≥ 0.025 raise the attention level** (for example to "elevated" or
"urgent")? For reference only, out-of-fold: {pct(totals['stress_and_review'], totals['rows'])} of all patients have both,
by true class Low {pct(lo['stress_and_review'], lo['rows'])}, Medium {pct(me['stress_and_review'], me['rows'])}, High
{pct(by_class['High']['stress_and_review'], by_class['High']['rows'])}. Of the {n23} low-caffeine true-High patients,
{sum(1 for r in group_rows if 'high_stress' in r['alerts'] and r['review'])} have both, so such a rule would raise only
those; the other {sum(1 for r in group_rows if 'high_stress' in r['alerts'] and not r['review'])} have the stress alert without
the review flag and would stay where they are. No rule was changed.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
