"""Fairness check of the served 11-feature v2 XGBoost (uncalibrated, review threshold 0.025) by Gender and
by Occupation. Validation/CV only: the 1,650 test rows are never loaded (the 3-class test set is spent).

Two views:
- Validation split: the SERVED files (preprocessor + model in data/processed/) scored on the 1,650
  validation rows they were not trained on.
- Out-of-fold: the 9,350 train + validation rows, 5-fold stratified on the 3-class label, shuffled, seed
  42 (the folds of the re-tuning, derived-feature and calibration reports); v2 params, preprocessing
  fitted inside each fold.

Per group: rows, true-High rows, balanced accuracy, High recall (labelled High), and the review flag's
catch rate of true High at 0.025. A group is FLAGGED when its balanced accuracy or High recall is more than
5 points (0.05) below the overall value for the same view. Every flag gets a bootstrap 95% interval
(2,000 resamples within the group, seed 42) so a small group's noise can be told apart from a real gap.

Gender is not a model input (it was never one of the 11 features), so a gap there could only come through
correlated inputs. Occupation is an input.

Run from MindCare AI/: python -m src.fairness.fairness_11feature_v2
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level

SEED = 42
FOLDS = 5
HIGH = 2
THRESHOLD = 0.025
GAP = 0.05
BOOTSTRAP = 2000
ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
PREPROCESSOR_PATH = ROOT / "data" / "processed" / "mindcare_preprocessor_11feature_v2.pkl"
MODEL_PATH = ROOT / "data" / "processed" / "mindcare_final_model_11feature_v2_xgb.pkl"
V2_TUNING_PATH = ROOT / "reports" / "tuning_results_12feature.json"
REPORT_JSON = ROOT / "reports" / "fairness_11feature_v2.json"
REPORT_MD = ROOT / "reports" / "fairness_11feature_v2.md"

NUMERIC = [
    "Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
    "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
    "Diet Quality (1-10)", "Age",
]
CATEGORICAL = ["Occupation", "Family History of Anxiety"]
FEATURES = NUMERIC + CATEGORICAL
GROUPINGS = ["Gender", "Occupation"]


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    pred = p.argmax(axis=1)
    high = y == HIGH
    return {"rows": int(len(y)), "true_high": int(high.sum()),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "high_recall": float((pred[high] == HIGH).mean()) if high.any() else float("nan"),
            "flag_catch_rate": float((p[high, HIGH] >= THRESHOLD).mean()) if high.any() else float("nan")}


def bootstrap(y: np.ndarray, p: np.ndarray, key: str, rng: np.random.Generator) -> list[float]:
    values = []
    for _ in range(BOOTSTRAP):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) == 3:
            values.append(metrics(y[i], p[i])[key])
    return [float(np.nanpercentile(values, 2.5)), float(np.nanpercentile(values, 97.5))]


def by_group(df: pd.DataFrame, y: np.ndarray, p: np.ndarray, rng: np.random.Generator) -> dict:
    overall = metrics(y, p)
    out = {"overall": overall}
    for grouping in GROUPINGS:
        groups = {}
        for value in sorted(df[grouping].unique()):
            mask = (df[grouping] == value).to_numpy()
            g = metrics(y[mask], p[mask])
            g["flags"] = [k for k in ("balanced_accuracy", "high_recall") if overall[k] - g[k] > GAP]
            g["ci95"] = {k: bootstrap(y[mask], p[mask], k, rng) for k in g["flags"]}
            groups[value] = g
        out[grouping] = groups
    return out


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as splits:
        train_idx, val_idx = splits["train_original_idx"], splits["val_original_idx"]
    rng = np.random.default_rng(SEED)

    # Validation split, served files.
    val = raw.iloc[val_idx].reset_index(drop=True)
    y_val = bin_anxiety_level(val["Anxiety Level (1-10)"].to_numpy())
    p_val = joblib.load(MODEL_PATH).predict_proba(joblib.load(PREPROCESSOR_PATH).transform(val[FEATURES]))
    validation = by_group(val, y_val, p_val, rng)

    # Out-of-fold over train + validation.
    df = raw.iloc[np.concatenate([train_idx, val_idx])].reset_index(drop=True)
    y = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    params = json.loads(V2_TUNING_PATH.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]
    p = np.zeros((len(y), 3))
    for tr, te in StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y):
        pre = ColumnTransformer([("num", StandardScaler(), NUMERIC), ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
        model = XGBClassifier(**params, objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
        model.fit(pre.fit_transform(df.iloc[tr][FEATURES]), y[tr])
        p[te] = model.predict_proba(pre.transform(df.iloc[te][FEATURES]))
    oof = by_group(df, y, p, rng)

    result = {"model": "served 11-feature v2 XGBoost, uncalibrated", "review_threshold": THRESHOLD, "gap_rule": GAP,
              "validation_split": validation, "out_of_fold": oof, "test_set_used": False}
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")

    def table(view: dict, grouping: str) -> str:
        o = view["overall"]
        lines = ["| Group | Rows | True High | Balanced accuracy | High recall | Flag catch (0.025) | Flag |",
                 "|---|---|---|---|---|---|---|",
                 f"| **All** | {o['rows']} | {o['true_high']} | {o['balanced_accuracy']:.4f} | {o['high_recall']:.4f} | {o['flag_catch_rate']:.4f} | |"]
        for value, g in view[grouping].items():
            flag = "; ".join(f"**{k} {g[k] - o[k]:+.3f}** (95% CI {g['ci95'][k][0]:.3f}–{g['ci95'][k][1]:.3f})" for k in g["flags"])
            lines.append(f"| {value} | {g['rows']} | {g['true_high']} | {g['balanced_accuracy']:.4f} | {g['high_recall']:.4f} | "
                         f"{g['flag_catch_rate']:.4f} | {flag or '—'} |")
        return "\n".join(lines)

    def high_range(view: dict) -> str:
        counts = [g["true_high"] for g in view["Occupation"].values()]
        return f"{min(counts)}–{max(counts)}"

    flagged = [(view, grouping, value) for view, data in (("validation split", validation), ("out-of-fold", oof))
               for grouping in GROUPINGS for value, g in data[grouping].items() if g["flags"]]
    REPORT_MD.write_text(
        "# Fairness: 11-feature v2 by Gender and Occupation (validation and CV only)\n\n"
        "Script: `src/fairness/fairness_11feature_v2.py`. **The test set was not used.** Model: the served v2 XGBoost, "
        "uncalibrated, review threshold 0.025. Validation split = the served files on the 1,650 validation rows; "
        "out-of-fold = 9,350 train + validation rows on the shared 5 folds (seed 42), preprocessing fitted inside each fold.\n\n"
        f"Rule: a group is flagged when its balanced accuracy or High recall is more than {GAP:.0%} points below the overall "
        f"value of the same view; flags carry a bootstrap 95% interval ({BOOTSTRAP} resamples within the group). Gender is not "
        "a model input; Occupation is.\n\n"
        + "\n\n".join(f"## {title}: {grouping}\n\n{table(data, grouping)}"
                      for title, data in (("Out-of-fold (9,350 rows)", oof), ("Validation split (1,650 rows)", validation))
                      for grouping in GROUPINGS)
        + "\n\n## Summary\n\n"
        + (("Flagged: " + "; ".join(f"{v} ({g}, {view})" for view, g, v in flagged) + ". "
            f"Occupations have {high_range(validation)} true-High validation rows and {high_range(oof)} out-of-fold, "
            "so read each flag with its interval. A flag whose interval still contains the overall value is "
            "consistent with noise. With 13 occupations, about one interval in 20 would exclude the overall value by "
            "chance alone, and the validation rows are part of the out-of-fold rows, so the two views are not "
            "independent confirmations.\n") if flagged
           else "No group is more than 5 points below the overall value on either metric, in either view.\n")
        + "\nVery likely synthetic dataset with near-uniform demographics: this checks the model, not real-world fairness.\n",
        encoding="utf-8", newline="\n",
    )
    print(REPORT_MD.read_text(encoding="utf-8").encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
