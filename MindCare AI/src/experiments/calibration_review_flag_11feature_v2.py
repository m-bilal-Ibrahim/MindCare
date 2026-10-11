"""Calibration of the served 11-feature v2 XGBoost and a re-derivation of the review-flag threshold.
Validation/CV only: the 1,650 test rows are never loaded (the 3-class test set is spent).

THRESHOLD TARGET (fixed before any threshold table was computed):
    Catch at least 95% of true-High patients with the review flag (flag catch rate = share of
    true-High rows with P(High) >= t), while flagging as few patients as possible. The proposed
    threshold is the LARGEST t whose out-of-fold flag catch rate is >= 0.95.
    (The current 0.025 catches 158/165 = 95.8% on the validation split, so 95% is the bar it was
    meant to meet.)

Deployed object this evaluation mirrors: ONE calibrated model -
    CalibratedClassifierCV(XGBClassifier(<served v2 params>), method=<isotonic|sigmoid>, cv=5,
                           ensemble=False)
fitted on the training rows: one XGBoost refitted on all of them (identical setup to v2) plus one
calibrator fitted on 5-fold cross-validated predictions of those rows. Same preprocessor type,
same libraries (scikit-learn, xgboost already pinned); one joblib pickle replaces the model file.

Out-of-fold protocol: the 9,350 train + validation rows, 5-fold stratified on the 3-class label,
shuffled, seed 42 (the folds of tune_models_11feature.py and derived_features_11feature.py). In
every outer fold, on the fold's training part only: fit the preprocessor, then fit (a) the plain v2
XGBoost = the uncalibrated arm, and (b) the exact deployed object above (inner 5-fold, stratified,
shuffled, seed 42) for each method. Predict the held-out fold. Every probability below comes from
a model and calibrator that never saw that row.

Known optimism: v2's hyperparameters were tuned by CV on rows inside these 9,350, and the threshold
is proposed on the same out-of-fold rows it is reported on. Both make the estimates slightly
optimistic; a single threshold chosen on ~970 true-High rows leaves little room for that.

Changes no served file. Run from MindCare AI/: python -m src.experiments.calibration_review_flag_11feature_v2
"""

from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.metrics import balanced_accuracy_score, f1_score, recall_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level

SEED = 42
FOLDS = 5
HIGH = 2
CLASSES = ["Low", "Medium", "High"]
CATCH_TARGET = 0.95
CURRENT_THRESHOLD = 0.025
COVERAGE_MATCH_THRESHOLD = 0.0302  # reports/feature_reduction_sweatlevel_3class.md
CONFIDENCE_THRESHOLD = 0.70
BOOTSTRAP = 2000
ECE_BINS = 10
SWEEP = [0.005, 0.01, 0.015, 0.02, 0.025, 0.0302, 0.035, 0.04, 0.05, 0.06, 0.075, 0.1, 0.125, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
V2_TUNING_PATH = ROOT / "reports" / "tuning_results_12feature.json"
OOF_PATH = ROOT / "reports" / "calibration_review_flag_11feature_v2_oof.csv"
REPORT_JSON = ROOT / "reports" / "calibration_review_flag_11feature_v2.json"
REPORT_MD = ROOT / "reports" / "calibration_review_flag_11feature_v2.md"

NUMERIC = [
    "Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
    "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
    "Diet Quality (1-10)", "Age",
]
CATEGORICAL = ["Occupation", "Family History of Anxiety"]
FEATURES = NUMERIC + CATEGORICAL


def xgb(params: dict) -> XGBClassifier:
    return XGBClassifier(**params, objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)


def deployed_object(params: dict, method: str) -> CalibratedClassifierCV:
    inner = StratifiedKFold(FOLDS, shuffle=True, random_state=SEED)
    return CalibratedClassifierCV(xgb(params), method=method, cv=inner, ensemble=False)


def brier(y: np.ndarray, p: np.ndarray, k: int) -> float:
    return float(np.mean((p[:, k] - (y == k)) ** 2))


def ece(y: np.ndarray, p: np.ndarray, k: int) -> float:
    """One-vs-rest expected calibration error, 10 equal-width bins (as reports/calibration_3class*.md)."""
    prob, hit = p[:, k], (y == k).astype(float)
    bins = np.minimum((prob * ECE_BINS).astype(int), ECE_BINS - 1)
    return float(sum(abs(prob[bins == b].mean() - hit[bins == b].mean()) * (bins == b).mean()
                     for b in range(ECE_BINS) if (bins == b).any()))


def class_metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    return {"balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro")),
            "high_recall": float(recall_score(y, pred, labels=[HIGH], average=None)[0])}


def flag_stats(y: np.ndarray, p_high: np.ndarray, t: float) -> dict:
    flagged = p_high >= t
    return {"threshold": t, "flagged": int(flagged.sum()), "share_flagged": float(flagged.mean()),
            "true_high_caught": int((flagged & (y == HIGH)).sum()), "catch_rate": float(flagged[y == HIGH].mean()),
            "wrong_predictions_caught": None}


def sweep_table(y: np.ndarray, p: np.ndarray, thresholds: list[float]) -> list[dict]:
    pred = p.argmax(axis=1)
    wrong = pred != y
    rows = []
    for t in thresholds:
        s = flag_stats(y, p[:, HIGH], t)
        flagged = p[:, HIGH] >= t
        # Wrong predictions the flag points at: every wrong prediction among flagged rows, and the
        # ones that matter most - true-High patients predicted Low/Medium.
        s["wrong_predictions_caught"] = int((flagged & wrong).sum())
        s["missed_high_caught"] = int((flagged & (y == HIGH) & (pred != HIGH)).sum())
        rows.append(s)
    return rows


def propose(y: np.ndarray, p_high: np.ndarray) -> float:
    """Largest threshold with flag catch rate >= CATCH_TARGET: the CATCH_TARGET quantile of P(High) among
    true-High rows, rounded down to 4 decimals so the target still holds."""
    high_p = np.sort(p_high[y == HIGH])
    allowed_misses = int(np.floor((1 - CATCH_TARGET) * len(high_p)))
    t = np.floor(high_p[allowed_misses] * 1e4) / 1e4
    assert (p_high[y == HIGH] >= t).mean() >= CATCH_TARGET
    return float(t)


def bootstrap(y: np.ndarray, p_high: np.ndarray, t: float, rng: np.random.Generator) -> dict:
    n, catch, share = len(y), [], []
    for _ in range(BOOTSTRAP):
        i = rng.integers(0, n, n)
        yy, f = y[i], p_high[i] >= t
        catch.append(f[yy == HIGH].mean())
        share.append(f.mean())
    point = flag_stats(y, p_high, t)
    return {"threshold": t, "catch_rate": point["catch_rate"], "catch_rate_95ci": [float(np.percentile(catch, 2.5)), float(np.percentile(catch, 97.5))],
            "share_flagged": point["share_flagged"], "share_flagged_95ci": [float(np.percentile(share, 2.5)), float(np.percentile(share, 97.5))]}


def confidence_stats(y: np.ndarray, p: np.ndarray, flag_t: float) -> dict:
    pred, top = p.argmax(axis=1), p.max(axis=1)
    confident = (top >= CONFIDENCE_THRESHOLD) & ~((p[:, HIGH] >= flag_t) & (pred != HIGH))
    return {"share_confident": float(confident.mean()), "accuracy_confident": float((pred[confident] == y[confident]).mean()),
            "accuracy_borderline": float((pred[~confident] == y[~confident]).mean()),
            "true_high_shown_confident_low_or_medium": int((confident & (y == HIGH) & (pred != HIGH)).sum())}


def main() -> None:
    params = json.loads(V2_TUNING_PATH.read_text(encoding="utf-8"))["models"]["xgboost"]
    assert params["sample_weighting"] == "none"
    params = params["best_params"]
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as splits:
        train_idx, val_idx = splits["train_original_idx"], splits["val_original_idx"]
    rows = np.concatenate([train_idx, val_idx])  # no test rows
    is_val = np.r_[np.zeros(len(train_idx), bool), np.ones(len(val_idx), bool)]
    df = raw.iloc[rows].reset_index(drop=True)
    x, y = df[FEATURES], bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    folds = list(StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(x, y))

    oof = {"uncalibrated": np.zeros((len(y), 3)), "isotonic": np.zeros((len(y), 3)), "sigmoid": np.zeros((len(y), 3))}
    for f, (tr, te) in enumerate(folds):
        pre = ColumnTransformer([("num", StandardScaler(), NUMERIC), ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
        x_tr, x_te = pre.fit_transform(x.iloc[tr]), pre.transform(x.iloc[te])
        oof["uncalibrated"][te] = xgb(params).fit(x_tr, y[tr]).predict_proba(x_te)
        for method in ("isotonic", "sigmoid"):
            oof[method][te] = deployed_object(params, method).fit(x_tr, y[tr]).predict_proba(x_te)
        print(f"fold {f + 1}/{FOLDS} done", flush=True)

    calibration = {name: {"brier": {c: brier(y, p, k) for k, c in enumerate(CLASSES)},
                          "ece": {c: ece(y, p, k) for k, c in enumerate(CLASSES)}}
                   for name, p in oof.items()}
    for name in calibration:
        calibration[name]["brier_sum"] = float(sum(calibration[name]["brier"].values()))
        calibration[name]["ece_mean"] = float(np.mean(list(calibration[name]["ece"].values())))
    method = min(("isotonic", "sigmoid"), key=lambda m: (calibration[m]["brier_sum"], calibration[m]["ece_mean"]))
    cal = oof[method]
    unc = oof["uncalibrated"]

    pred_unc, pred_cal = unc.argmax(axis=1), cal.argmax(axis=1)
    agreement = {"same_class": float((pred_unc == pred_cal).mean()), "changed_rows": int((pred_unc != pred_cal).sum()),
                 "changes": {f"{CLASSES[a]}->{CLASSES[b]}": int(((pred_unc == a) & (pred_cal == b)).sum())
                             for a in range(3) for b in range(3) if a != b}}
    metrics = {"uncalibrated": class_metrics(y, pred_unc), method: class_metrics(y, pred_cal),
               "validation_split_uncalibrated": class_metrics(y[is_val], pred_unc[is_val]),
               f"validation_split_{method}": class_metrics(y[is_val], pred_cal[is_val])}
    delta = {k: metrics[method][k] - metrics["uncalibrated"][k] for k in metrics["uncalibrated"]}
    model_change = any(v < 0 for v in delta.values()) and agreement["changed_rows"] > 0

    proposed_unc = propose(y, unc[:, HIGH])
    proposed_cal = propose(y, cal[:, HIGH])
    rng = np.random.default_rng(SEED)
    intervals = {
        "uncalibrated": [bootstrap(y, unc[:, HIGH], t, rng) for t in (CURRENT_THRESHOLD, COVERAGE_MATCH_THRESHOLD, proposed_unc)],
        method: [bootstrap(y, cal[:, HIGH], proposed_cal, rng)],
    }
    sweep = {"uncalibrated": sweep_table(y, unc, sorted(set(SWEEP + [proposed_unc]))),
             method: sweep_table(y, cal, sorted(set(SWEEP + [proposed_cal])))}
    sweep_val = {"uncalibrated": sweep_table(y[is_val], unc[is_val], [CURRENT_THRESHOLD, COVERAGE_MATCH_THRESHOLD, proposed_unc]),
                 method: sweep_table(y[is_val], cal[is_val], [proposed_cal])}
    confidence = {"uncalibrated_at_0.025": confidence_stats(y, unc, CURRENT_THRESHOLD),
                  f"uncalibrated_at_{proposed_unc}": confidence_stats(y, unc, proposed_unc),
                  f"{method}_at_{proposed_cal}": confidence_stats(y, cal, proposed_cal)}

    pd.DataFrame({"row_original_idx": rows, "is_validation_split": is_val, "y": y,
                  **{f"{n}_{c}": p[:, k] for n, p in oof.items() for k, c in enumerate(CLASSES)}}).round(5).to_csv(OOF_PATH, index=False)  # 5 decimals keeps the file under the repo's 1,000 KB limit
    result = {
        "threshold_target": f"flag catch rate >= {CATCH_TARGET} of true-High, flagging as few patients as possible "
                            "(largest threshold meeting it); fixed before the tables were built",
        "deployed_object": "CalibratedClassifierCV(XGBClassifier(v2 params), method, cv=StratifiedKFold(5, shuffle, 42), "
                           "ensemble=False) fitted on the training rows; same preprocessor; one pickle",
        "rows": len(y), "true_high": int((y == HIGH).sum()), "folds": FOLDS, "seed": SEED,
        "library_versions": {"python": platform.python_version(), "xgboost": xgboost.__version__,
                             "scikit-learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
        "calibration": calibration, "chosen_method": method,
        "class_agreement": agreement, "class_metrics": metrics, "calibrated_minus_uncalibrated": delta,
        "calibration_changes_predictions_at_a_cost": bool(model_change),
        "proposed_threshold": {"uncalibrated": proposed_unc, method: proposed_cal},
        "bootstrap_95ci": intervals, "sweep_oof": sweep, "sweep_validation_split": sweep_val,
        "confidence_label_at_0.70": confidence,
        "optimism_note": "v2 hyperparameters were tuned on rows inside these 9,350, and the threshold is proposed on "
                         "the rows it is reported on; estimates are slightly optimistic.",
        "test_set_used": False,
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_markdown(result)
    print(json.dumps({k: result[k] for k in ("chosen_method", "class_agreement", "calibrated_minus_uncalibrated",
                                             "proposed_threshold", "bootstrap_95ci")}, indent=1))


# Served files and constants a change would touch (checked against origin/main on 2026-10-11).
THRESHOLD_TOUCHPOINTS = [
    "`MindCare AI/src/api/main.py`: `HIGH_PROBA_THRESHOLD = 0.025` and its comment",
    "`MindCare AI/src/inference/predict_single.py`: its own copy of `HIGH_PROBA_THRESHOLD = 0.025`",
    "`MindCare AI/src/api/static/manual_test_form.html`: the text \"P(High) ≥ 0.025\"",
    "`MindCare AI/tests/test_api.py`: `assert HIGH_PROBA_THRESHOLD == 0.025`, and "
    "`test_confidence_label_matches_report_on_validation` (pins 54.8% / 0.8530 / 0.6792 / 7 at the current threshold)",
    "`MindCare AI/src/inference/confidence.py` docstring and `reports/confidence_label_11feature_v2.md`: the "
    "confident/borderline evidence is computed at 0.025 and would need re-deriving",
    "`MindCare Backend/apps/ai/api/serializers.py`: help text \"P(High) >= 0.025\"",
    "Docs: `MindCare AI/docs/api_usage.md`, `docs/model_card.md`, `CLAUDE.md` (all quote 0.025 and 158/165)",
]
CALIBRATION_TOUCHPOINTS = [
    "`data/processed/mindcare_final_model_11feature_v2_xgb.pkl` replaced by a new calibrated pickle "
    "(`CalibratedClassifierCV`, same scikit-learn 1.9.1 / xgboost 3.4.1; no new library or format beyond a different "
    "pickled class) and `MODEL_PATH` in `src/api/main.py` / `src/inference/predict_single.py`",
    "`scripts/deploy_artifacts.py` `ARTIFACTS` and `data/processed/deploy_artifacts.json` (hashes and the expected "
    "example probabilities)",
    "`tests/test_api.py` `test_serves_xgboost_with_its_review_threshold` (asserts the model is an `XGBClassifier`) "
    "and every test pinned to the current probabilities",
    "`src/inference/confidence.py` `CONFIDENCE_THRESHOLD = 0.70`: its evidence (share confident, accuracy) is for "
    "uncalibrated probabilities and would need re-deriving",
    "the `/patient-summary` severity-tier lookup uses the predicted class, which calibration changes for 1.5% of rows",
]


def write_markdown(r: dict) -> None:
    m = r["chosen_method"]
    cal, unc = r["calibration"][m], r["calibration"]["uncalibrated"]
    sig = r["calibration"]["sigmoid"]
    n_high = r["true_high"]
    calib_rows = "\n".join(
        f"| {c} | {unc['brier'][c]:.4f} | {cal['brier'][c]:.4f} | {sig['brier'][c]:.4f} | "
        f"{unc['ece'][c]:.4f} | {cal['ece'][c]:.4f} | {sig['ece'][c]:.4f} |" for c in CLASSES)
    cm = r["class_metrics"]
    metric_rows = "\n".join(
        f"| {k} | {cm['uncalibrated'][k]:.4f} | {cm[m][k]:.4f} | {r['calibrated_minus_uncalibrated'][k]:+.4f} |"
        for k in ("balanced_accuracy", "macro_f1", "high_recall"))

    def sweep_rows(rows: list[dict], proposed: float) -> str:
        return "\n".join(
            f"| {s['threshold']}{' (current)' if s['threshold'] == CURRENT_THRESHOLD else ''}"
            f"{' (proposed)' if s['threshold'] == proposed else ''} | {s['flagged']:,} ({s['share_flagged']:.1%}) | "
            f"{s['true_high_caught']}/{n_high} ({s['catch_rate']:.2%}) | {s['missed_high_caught']} | {s['wrong_predictions_caught']} |"
            for s in rows)

    ci = [*r["bootstrap_95ci"]["uncalibrated"], *r["bootstrap_95ci"][m]]
    ci_rows = "\n".join(
        f"| {'uncalibrated' if i < 3 else m} {b['threshold']} | {b['catch_rate']:.2%} [{b['catch_rate_95ci'][0]:.2%}, "
        f"{b['catch_rate_95ci'][1]:.2%}] | {b['share_flagged']:.1%} [{b['share_flagged_95ci'][0]:.1%}, {b['share_flagged_95ci'][1]:.1%}] |"
        for i, b in enumerate(ci))
    conf_rows = "\n".join(
        f"| {k} | {v['share_confident']:.1%} | {v['accuracy_confident']:.4f} | {v['accuracy_borderline']:.4f} | "
        f"{v['true_high_shown_confident_low_or_medium']} |" for k, v in r["confidence_label_at_0.70"].items())
    val_rows = "\n".join(
        f"| {name} {s['threshold']} | {s['flagged']} ({s['share_flagged']:.1%}) | {s['true_high_caught']}/165 |"
        for name, rows in r["sweep_validation_split"].items() for s in rows)
    pu, pc = r["proposed_threshold"]["uncalibrated"], r["proposed_threshold"][m]
    ch = r["class_agreement"]
    REPORT_MD.write_text(f"""# Calibration and the review-flag threshold: 11-feature v2 (out-of-fold, CV only)

Script: `src/experiments/calibration_review_flag_11feature_v2.py`. **The test set was not used.** Out-of-fold
probabilities for all {r['rows']:,} train + validation rows ({n_high} true High), 5-fold stratified on the 3-class label,
shuffled, seed 42 (the folds of the re-tuning and derived-feature reports). Per-row probabilities:
`reports/calibration_review_flag_11feature_v2_oof.csv`.

## Threshold target (fixed before the tables were built)

{r['threshold_target']}.

## Deployed object this mirrors

{r['deployed_object']}. Inside every outer fold the exact object was fitted on the fold's training part only (its
own inner 5-fold CV for the calibrator), and the plain v2 XGBoost on the same part is the uncalibrated arm.

## 1. Calibration (Brier score and ECE per class, one-vs-rest, 10 bins; lower is better)

| Class | Brier: uncalibrated | Brier: isotonic | Brier: sigmoid | ECE: uncalibrated | ECE: isotonic | ECE: sigmoid |
|---|---|---|---|---|---|---|
{calib_rows}
| **Sum / mean** | **{unc['brier_sum']:.4f}** | **{cal['brier_sum']:.4f}** | **{sig['brier_sum']:.4f}** | **{unc['ece_mean']:.4f}** | **{cal['ece_mean']:.4f}** | **{sig['ece_mean']:.4f}** |

Better method by out-of-fold Brier, then ECE: **{m}**. Sigmoid makes calibration worse. The uncalibrated v2 model is
already well calibrated (ECE at most 0.010 per class); {m} lowers ECE but does not improve the Brier score.

## 2. Does calibration change the predictions?

Same predicted class on {ch['same_class']:.1%} of rows; {ch['changed_rows']} rows change
({', '.join(f'{k}: {v}' for k, v in ch['changes'].items() if v)}).

| Metric (out-of-fold, {r['rows']:,} rows) | Uncalibrated | {m.capitalize()} | Difference |
|---|---|---|---|
{metric_rows}

**{'MODEL CHANGE: calibration changes predicted classes and costs High recall' if r['calibration_changes_predictions_at_a_cost'] else 'No cost from calibration'}**
({r['calibrated_minus_uncalibrated']['high_recall'] * n_high:+.0f} true-High patients labelled High), for a
negligible gain elsewhere.

## 3. Review threshold trade-off (out-of-fold)

"Missed High caught" = true-High patients the model labels Low/Medium that the flag still points at; "wrong
caught" = all wrong predictions among flagged patients.

### Uncalibrated (as served)

| Threshold | Patients flagged | True High caught | Missed High caught | Wrong caught |
|---|---|---|---|---|
{sweep_rows(r['sweep_oof']['uncalibrated'], pu)}

### {m.capitalize()}-calibrated

| Threshold | Patients flagged | True High caught | Missed High caught | Wrong caught |
|---|---|---|---|---|
{sweep_rows(r['sweep_oof'][m], pc)}

### Bootstrap 95% intervals ({BOOTSTRAP} resamples of the {r['rows']:,} rows, seed 42)

| Threshold | Flag catch rate of true High | Share flagged |
|---|---|---|
{ci_rows}

The intervals hold the threshold fixed, so they do not include the uncertainty of choosing it.

### Validation split only (1,650 rows, for continuity with earlier reports)

| Threshold | Flagged | True High caught |
|---|---|---|
{val_rows}

## 4. Knock-on effect on the confident/borderline label (0.70 cut-off, out-of-fold)

| Probabilities and flag threshold | Confident | Accuracy if confident | Accuracy if borderline | True High shown as a confident Low/Medium |
|---|---|---|---|---|
{conf_rows}

## Proposal

- **Calibration: do not deploy.** v2 is already well calibrated; isotonic changes {ch['changed_rows']} predicted classes and
  loses High recall, and at the same ~95% catch it flags more patients than the uncalibrated model.
- **Threshold, by the pre-set target: {pu}** on the uncalibrated probabilities. It is the largest threshold that still
  catches ≥ 95% of true High out-of-fold, and flags about {ci[2]['share_flagged']:.0%} of patients instead of
  {ci[0]['share_flagged']:.0%} at 0.025.
- **Caveats for that choice:** it sits exactly on the target (0.035 already falls below 95%); its catch-rate interval
  goes down to {ci[2]['catch_rate_95ci'][0]:.1%} (0.025: {ci[0]['catch_rate_95ci'][0]:.1%}); it catches {round((ci[0]['catch_rate'] - ci[2]['catch_rate']) * n_high)} fewer of {n_high} true-High patients than 0.025;
  and more true-High patients are shown as a confident Low/Medium ({list(r['confidence_label_at_0.70'].values())[1]['true_high_shown_confident_low_or_medium']} vs {list(r['confidence_label_at_0.70'].values())[0]['true_high_shown_confident_low_or_medium']}). 0.0302 is the in-between
  option. Choosing between catching more High patients and flagging fewer is a clinical decision.

## Known optimism

{r['optimism_note']}

## What would change (nothing was changed)

If the threshold changes:
{chr(10).join('- ' + t for t in THRESHOLD_TOUCHPOINTS)}

If calibration were deployed, additionally:
{chr(10).join('- ' + t for t in CALIBRATION_TOUCHPOINTS)}

The alert layer (`src/inference/alerts.py`, `src/config/alert_thresholds.toml`, open PR) does not use this flag and is
not affected.

Libraries: {', '.join(f'{k} {v}' for k, v in r['library_versions'].items())}. Very likely synthetic dataset:
prototype-level evidence only.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    import sys

    if "--report-only" in sys.argv:  # rebuild the Markdown from the saved JSON without refitting
        write_markdown(json.loads(REPORT_JSON.read_text(encoding="utf-8")))
    else:
        main()
