"""Is the served 11-feature v2 XGBoost still well tuned? Re-tune on the 11 features and compare.

Its hyperparameters (reports/tuning_results_12feature.json) were chosen on the 12-feature set, before
Sweating Level was removed. This repeats the search on the 11 v2 features. Validation/CV only: the
1,650 test rows are never loaded (the 3-class test set is spent; CLAUDE.md).

Procedure
- Rows: the 9,350 train + validation rows (mindcare_processed_splits.npz). Folds: 5-fold stratified on
  the 3-class label, shuffled, seed 42 - the same folds for every trial and for the v2 comparison.
- Search: 60 random trials (sklearn ParameterSampler, seed 42) over the 12-feature script's XGBoost
  space, with n_estimators replaced by early stopping, and sample weighting {none, balanced} as one
  more dimension (as in the 12-feature search, where it was searched in two halves).
- Inside each fold: the fold's training part is split again (85/15, stratified, seed 42); the
  scaler/encoder is fitted on the 85% only; XGBoost trains up to 2,000 rounds and stops after 50
  rounds without improvement in mlogloss on the 15% early-stopping part; balanced accuracy is scored
  on the held-out fold. The held-out fold never influences fitting or stopping.
- Comparison: the best trial is refitted in deployable form (fixed n_estimators = median best
  round count from its folds, fitted on the whole fold training part, no early-stopping set) and
  compared with the served v2 params fitted the same way, on the same folds.
- Decision: if the mean paired balanced-accuracy difference is within one standard deviation of the
  paired differences, v2 is kept. The std of each arm's own fold scores is reported too.

Writes reports/tuning_trials_11feature.csv (every trial and fold), reports/tuning_results_11feature.json
and .md. Saves no model and changes no served file.

Run from MindCare AI/: python -m src.models.tune_models_11feature
"""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.metrics import balanced_accuracy_score, f1_score, recall_score
from sklearn.model_selection import ParameterSampler, StratifiedKFold, train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level

SEED = 42
FOLDS = 5
TRIALS = 60
MAX_ROUNDS = 2000
EARLY_STOPPING_ROUNDS = 50
ES_FRACTION = 0.15
HIGH = 2
ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
V2_TUNING_PATH = ROOT / "reports" / "tuning_results_12feature.json"
TRIALS_CSV = ROOT / "reports" / "tuning_trials_11feature.csv"
RESULTS_JSON = ROOT / "reports" / "tuning_results_11feature.json"
RESULTS_MD = ROOT / "reports" / "tuning_results_11feature.md"

NUMERIC = [
    "Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
    "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
    "Diet Quality (1-10)", "Age",
]
CATEGORICAL = ["Occupation", "Family History of Anxiety"]
FEATURES = NUMERIC + CATEGORICAL

# tune_models_12feature.py's XGB_SPACE, minus n_estimators (early stopping decides it), plus weighting.
SPACE = {
    "max_depth": [3, 4, 6, 8],
    "learning_rate": [0.03, 0.05, 0.1, 0.2],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
    "min_child_weight": [1, 3, 5],
    "gamma": [0, 0.1],
    "sample_weighting": ["none", "balanced"],
}


def preprocessor() -> ColumnTransformer:
    return ColumnTransformer([("num", StandardScaler(), NUMERIC),
                              ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])


def scores(y_true, y_pred) -> dict:
    return {"balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
            "high_recall": float(recall_score(y_true, y_pred, labels=[HIGH], average=None)[0])}


def xgb_params(trial: dict) -> dict:
    return {k: v for k, v in trial.items() if k != "sample_weighting"}


def fit_early_stopped(x: pd.DataFrame, y: np.ndarray, trial: dict, x_out: pd.DataFrame) -> tuple[np.ndarray, int]:
    fit_idx, es_idx = train_test_split(np.arange(len(y)), test_size=ES_FRACTION, random_state=SEED, stratify=y)
    pre = preprocessor()
    x_fit = pre.fit_transform(x.iloc[fit_idx])
    weights = compute_sample_weight("balanced", y[fit_idx]) if trial["sample_weighting"] == "balanced" else None
    model = XGBClassifier(**xgb_params(trial), n_estimators=MAX_ROUNDS, early_stopping_rounds=EARLY_STOPPING_ROUNDS,
                          objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
    model.fit(x_fit, y[fit_idx], sample_weight=weights, eval_set=[(pre.transform(x.iloc[es_idx]), y[es_idx])], verbose=False)
    return model.predict(pre.transform(x_out)), int(model.best_iteration) + 1


def fit_fixed(x: pd.DataFrame, y: np.ndarray, params: dict, weighting: str, x_out: pd.DataFrame) -> np.ndarray:
    pre = preprocessor()
    weights = compute_sample_weight("balanced", y) if weighting == "balanced" else None
    model = XGBClassifier(**params, objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
    model.fit(pre.fit_transform(x), y, sample_weight=weights)
    return model.predict(pre.transform(x_out))


def summarise(values) -> dict:
    return {"mean": float(np.mean(values)), "std": float(np.std(values, ddof=1)), "folds": [float(v) for v in values]}


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as splits:
        rows = np.concatenate([splits["train_original_idx"], splits["val_original_idx"]])  # no test rows
    assert len(rows) == 9350
    df = raw.iloc[rows].reset_index(drop=True)
    x, y = df[FEATURES], bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    folds = list(StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(x, y))

    trial_rows, trial_summaries = [], []
    started = time.time()
    for t, trial in enumerate(ParameterSampler(SPACE, n_iter=TRIALS, random_state=SEED)):
        fold_scores, rounds = [], []
        for f, (tr, te) in enumerate(folds):
            pred, n_rounds = fit_early_stopped(x.iloc[tr], y[tr], trial, x.iloc[te])
            s = scores(y[te], pred)
            fold_scores.append(s)
            rounds.append(n_rounds)
            trial_rows.append({"trial": t, "fold": f, **trial, "rounds": n_rounds, **s})
        ba = [s["balanced_accuracy"] for s in fold_scores]
        trial_summaries.append({"trial": t, "params": trial, "balanced_accuracy": summarise(ba),
                                "macro_f1_mean": float(np.mean([s["macro_f1"] for s in fold_scores])),
                                "high_recall_mean": float(np.mean([s["high_recall"] for s in fold_scores])),
                                "rounds": rounds})
        print(f"trial {t + 1:2d}/{TRIALS}: balanced accuracy {np.mean(ba):.4f} ± {np.std(ba, ddof=1):.4f}, "
              f"rounds {rounds}  ({time.time() - started:.0f}s)", flush=True)
    pd.DataFrame(trial_rows).to_csv(TRIALS_CSV, index=False)

    best = max(trial_summaries, key=lambda s: s["balanced_accuracy"]["mean"])
    best_n = int(np.median(best["rounds"]))
    best_fixed = {**xgb_params(best["params"]), "n_estimators": best_n}
    v2 = json.loads(V2_TUNING_PATH.read_text(encoding="utf-8"))["models"]["xgboost"]
    v2_params, v2_weighting = v2["best_params"], v2["sample_weighting"]

    arms = {"v2_served": [], "best_trial_deployable": []}
    for tr, te in folds:
        arms["v2_served"].append(scores(y[te], fit_fixed(x.iloc[tr], y[tr], v2_params, v2_weighting, x.iloc[te])))
        arms["best_trial_deployable"].append(
            scores(y[te], fit_fixed(x.iloc[tr], y[tr], best_fixed, best["params"]["sample_weighting"], x.iloc[te])))
    comparison = {}
    for metric in ("balanced_accuracy", "macro_f1", "high_recall"):
        a = [s[metric] for s in arms["v2_served"]]
        b = [s[metric] for s in arms["best_trial_deployable"]]
        comparison[metric] = {"v2_served": summarise(a), "best_trial": summarise(b), "paired_diff_best_minus_v2": summarise(np.subtract(b, a))}
    diff = comparison["balanced_accuracy"]["paired_diff_best_minus_v2"]
    keep_v2 = abs(diff["mean"]) <= diff["std"] or diff["mean"] <= 0

    result = {
        "rows": len(df), "folds": FOLDS, "trials": TRIALS, "seed": SEED,
        "procedure": "5-fold stratified CV on train+val; preprocessing fitted inside each fold; early stopping "
                     f"({EARLY_STOPPING_ROUNDS} rounds, mlogloss) on a {ES_FRACTION:.0%} split of each fold's training part",
        "search_space": SPACE,
        "library_versions": {"python": platform.python_version(), "xgboost": xgboost.__version__,
                             "scikit-learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
        "best_trial": {**best, "deployable_params": best_fixed},
        "top_5": sorted(trial_summaries, key=lambda s: -s["balanced_accuracy"]["mean"])[:5],
        "v2_served": {"params": v2_params, "sample_weighting": v2_weighting},
        "comparison_same_folds": comparison,
        "decision": {"keep_v2": bool(keep_v2),
                     "rule": "keep v2 if the mean paired balanced-accuracy difference (best - v2) is within one std of "
                             "the paired differences, or not positive"},
        "test_set_used": False,
    }
    RESULTS_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")

    def row(name: str, metric: str) -> str:
        c = comparison[metric]
        return (f"| {name} | {c['v2_served']['mean']:.4f} ± {c['v2_served']['std']:.4f} | "
                f"{c['best_trial']['mean']:.4f} ± {c['best_trial']['std']:.4f} | "
                f"{c['paired_diff_best_minus_v2']['mean']:+.4f} ± {c['paired_diff_best_minus_v2']['std']:.4f} |")

    top = "\n".join(
        f"| {i + 1} | {s['balanced_accuracy']['mean']:.4f} ± {s['balanced_accuracy']['std']:.4f} | "
        f"{s['high_recall_mean']:.4f} | {int(np.median(s['rounds']))} | `{json.dumps(s['params'])}` |"
        for i, s in enumerate(result["top_5"]))
    RESULTS_MD.write_text(
        "# Re-tuning XGBoost on the 11 v2 features (CV only)\n\n"
        "Script: `src/models/tune_models_11feature.py`. **The test set was not used.** "
        f"{len(df):,} train + validation rows; {result['procedure']}; {TRIALS} random-search trials scored by "
        "balanced accuracy. Every trial and fold: `reports/tuning_trials_11feature.csv`.\n\n"
        "## Top 5 trials (search CV, early-stopped)\n\n"
        "| Rank | Balanced accuracy (mean ± std) | High recall | Median rounds | Params |\n|---|---|---|---|---|\n"
        + top + "\n\n"
        "## Best trial vs served v2, same folds, both fitted in deployable form\n\n"
        f"Best trial refitted with `n_estimators = {best_n}` (median early-stopped rounds) on each whole fold "
        "training part; v2 with its served params "
        f"(`{json.dumps(v2_params)}`, sample weighting `{v2_weighting}`).\n\n"
        "| Metric | v2 served | Best trial | Paired difference (best − v2) |\n|---|---|---|---|\n"
        + "\n".join(row(m, m) for m in ("balanced_accuracy", "macro_f1", "high_recall")) + "\n\n"
        f"**Decision: {'KEEP v2' if keep_v2 else 'the best trial is better by more than one std - consider replacing v2'}.** "
        f"Mean paired balanced-accuracy difference {diff['mean']:+.4f}, std of the paired differences {diff['std']:.4f}. "
        "No served file was changed.\n\n"
        f"Libraries: {', '.join(f'{k} {v}' for k, v in result['library_versions'].items())}. "
        "Very likely synthetic dataset: prototype-level evidence only.\n",
        encoding="utf-8", newline="\n",
    )
    # The report has non-ASCII characters (±, −); a Windows console may not encode them.
    print(RESULTS_MD.read_text(encoding="utf-8").encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
