"""Derived-feature stage vs the served 11-feature v2 model, by 5-fold CV on train + validation.

Validation/CV only: the 1,650 test rows are never loaded (the 3-class test set is spent).

Five stateless, row-wise derived features are added on top of the 11 v2 inputs:
  sleep_deficit      = max(0, 8 - Sleep Hours)
  stress_x_sleepdef  = Stress Level (1-10) * sleep_deficit
  arousal_index      = (Heart Rate - 70) / 70 + (Breathing Rate - 16) / 16
  lifestyle_score    = (min(Sleep/8, 1) + min(Physical Activity/5, 1) + Diet Quality/10) / 3
  caffeine_per_sleep = Caffeine Intake (mg/day) / Sleep Hours
They use fixed constants only (nothing learned), so computing them before the fold split leaks
nothing. The scaler/encoder IS fitted inside each fold, on that fold's training part only.

Both arms use the served v2 XGBoost hyperparameters (reports/tuning_results_12feature.json, unweighted,
the same as src/models/adopt_11feature_v2_model.py) and the same folds: 5-fold stratified on the
3-class label, shuffled, seed 42, over the 9,350 train + validation rows - the convention of
src/evaluation/nested_cv_12feature_xgb.py.

Decision rule (from the task): keep the derived features only if the mean balanced-accuracy gain is
larger than one standard deviation - here the std of the per-fold paired gains, which is the spread
that matters for a paired comparison; the std of the baseline's own fold scores is reported too.

Run from MindCare AI/: python -m src.experiments.derived_features_11feature
"""

from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.metrics import balanced_accuracy_score, f1_score, recall_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level

SEED = 42
FOLDS = 5
HIGH = 2
ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
TUNING_PATH = ROOT / "reports" / "tuning_results_12feature.json"
REPORT_JSON = ROOT / "reports" / "derived_features_11feature.json"
REPORT_MD = ROOT / "reports" / "derived_features_11feature.md"

BASE_NUMERIC = [
    "Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
    "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
    "Diet Quality (1-10)", "Age",
]
CATEGORICAL = ["Occupation", "Family History of Anxiety"]
DERIVED = ["sleep_deficit", "stress_x_sleepdef", "arousal_index", "lifestyle_score", "caffeine_per_sleep"]


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    sleep = out["Sleep Hours"]
    assert (sleep > 0).all(), "caffeine_per_sleep needs Sleep Hours > 0"
    out["sleep_deficit"] = np.maximum(0.0, 8.0 - sleep)
    out["stress_x_sleepdef"] = out["Stress Level (1-10)"] * out["sleep_deficit"]
    out["arousal_index"] = (out["Heart Rate (bpm)"] - 70) / 70 + (out["Breathing Rate (breaths/min)"] - 16) / 16
    out["lifestyle_score"] = (
        np.minimum(sleep / 8, 1) + np.minimum(out["Physical Activity (hrs/week)"] / 5, 1) + out["Diet Quality (1-10)"] / 10
    ) / 3
    out["caffeine_per_sleep"] = out["Caffeine Intake (mg/day)"] / sleep
    return out


def run_arm(df: pd.DataFrame, y: np.ndarray, numeric: list[str], params: dict, folds) -> list[dict]:
    scores = []
    for train, test in folds:
        pre = ColumnTransformer([("num", StandardScaler(), numeric),
                                 ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
        x_tr = pre.fit_transform(df.iloc[train][numeric + CATEGORICAL])  # fitted on this fold's train part only
        x_te = pre.transform(df.iloc[test][numeric + CATEGORICAL])
        model = XGBClassifier(**params, objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
        model.fit(x_tr, y[train])
        pred = model.predict(x_te)
        scores.append({
            "balanced_accuracy": float(balanced_accuracy_score(y[test], pred)),
            "macro_f1": float(f1_score(y[test], pred, average="macro")),
            "high_recall": float(recall_score(y[test], pred, labels=[HIGH], average=None)[0]),
        })
    return scores


def summary(values: list[float]) -> dict:
    return {"mean": float(np.mean(values)), "std": float(np.std(values, ddof=1)), "folds": [float(v) for v in values]}


def main() -> None:
    params = json.loads(TUNING_PATH.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as splits:
        rows = np.concatenate([splits["train_original_idx"], splits["val_original_idx"]])  # no test rows
    assert len(rows) == 9350
    df = add_derived(raw.iloc[rows].reset_index(drop=True))
    y = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    folds = list(StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y))

    base = run_arm(df, y, BASE_NUMERIC, params, folds)
    derived = run_arm(df, y, BASE_NUMERIC + DERIVED, params, folds)

    metrics = ["balanced_accuracy", "macro_f1", "high_recall"]
    result = {"rows": len(df), "folds": FOLDS, "seed": SEED, "xgb_params": params, "derived_features": DERIVED,
              "library_versions": {"python": platform.python_version(), "xgboost": xgboost.__version__,
                                   "scikit-learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
              "baseline_11": {}, "with_derived_16": {}, "paired_gain": {}}
    for m in metrics:
        b, d = [s[m] for s in base], [s[m] for s in derived]
        result["baseline_11"][m] = summary(b)
        result["with_derived_16"][m] = summary(d)
        result["paired_gain"][m] = summary(list(np.subtract(d, b)))
    gain = result["paired_gain"]["balanced_accuracy"]
    keep = gain["mean"] > gain["std"]
    result["decision"] = {"keep_derived_features": bool(keep),
                          "rule": "keep only if mean paired balanced-accuracy gain > std of the paired gains"}

    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows_md = []
    for m in metrics:
        b, d, g = result["baseline_11"][m], result["with_derived_16"][m], result["paired_gain"][m]
        rows_md.append(f"| {m} | {b['mean']:.4f} ± {b['std']:.4f} | {d['mean']:.4f} ± {d['std']:.4f} | "
                       f"{g['mean']:+.4f} ± {g['std']:.4f} | " + ", ".join(f"{v:+.4f}" for v in g["folds"]) + " |")
    REPORT_MD.write_text(
        "# Derived-feature stage vs the 11-feature v2 model (5-fold CV, train + validation)\n\n"
        "Script: `src/experiments/derived_features_11feature.py`. **Validation/CV only; the test set was not "
        "loaded.** 9,350 rows, 5-fold stratified on the 3-class label (shuffled, seed 42); scaler and encoder "
        "fitted inside each fold; both arms use the served v2 XGBoost hyperparameters, unweighted.\n\n"
        "Derived features (fixed constants, nothing learned): `sleep_deficit = max(0, 8 - sleep)`, "
        "`stress_x_sleepdef = stress * sleep_deficit`, `arousal_index = (HR-70)/70 + (BR-16)/16`, "
        "`lifestyle_score = (min(sleep/8,1) + min(activity/5,1) + diet/10)/3`, "
        "`caffeine_per_sleep = caffeine / sleep`.\n\n"
        "| Metric | 11 features (mean ± std) | 11 + 5 derived | Paired gain (mean ± std) | Gain per fold |\n"
        "|---|---|---|---|---|\n" + "\n".join(rows_md) + "\n\n"
        f"**Decision:** {'KEEP' if keep else 'DO NOT KEEP'} the derived features. Rule: keep only if the mean "
        f"paired balanced-accuracy gain ({gain['mean']:+.4f}) is larger than one standard deviation of the paired "
        f"gains ({gain['std']:.4f}).\n\n"
        f"Libraries: {', '.join(f'{k} {v}' for k, v in result['library_versions'].items())}. "
        "Very likely synthetic dataset: prototype-level evidence only.\n",
        encoding="utf-8", newline="\n",
    )
    print(REPORT_MD.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
