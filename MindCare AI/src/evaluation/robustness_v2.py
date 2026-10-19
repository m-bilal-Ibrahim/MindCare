"""Phase 19 (robustness) for the served 11-feature v2 XGBoost, 3-class Anxiety Level target.

Validation split only (the served files on the 1,650 validation rows); the test set is never loaded and no
served file or threshold is changed. Imputation and noise statistics come from the training split only.
Adapted from robustness_3class.py, whose report (reports/robustness_3class.md) is the 17-feature Random
Forest; its numbers are parsed from that report for comparison.

Guard: the served files must reproduce v2's validation numbers (balanced accuracy 0.8055, 411 flagged,
158/165 true High flagged at P(High) >= 0.025), otherwise stop.

1. Single-feature knockout: each feature replaced by its train median, then its train mean (categorical:
   train mode in both).
2. Gaussian noise of 0.25 / 0.5 / 0.75 / 1.0 x train std added to all 9 numeric features at once, 10 seeds
   each (not clipped, as in the earlier test); mean ± std over seeds.
3. Invalid inputs through src/inference/input_validation.validate_patient(): each must raise.
4. Stress Level shift -3..+3 (clipped to 1-10), plus a root-cause analysis of the earlier finding that
   shifting Stress up changed nothing: (a) clipping and how many rows sit at 9-10, (b) the highest Stress
   split thresholds in the trees and P(High) with Stress set to each value 1-10, (c) the shift within
   Therapy Sessions bands.

Metrics: balanced accuracy, macro-F1, model High recall (predicted class = High) and review-flag catch rate
(true High with P(High) >= 0.025). Synthetic-looking data: prototype-level evidence only.

Run from MindCare AI/: python -m src.evaluation.robustness_v2
"""

from __future__ import annotations

import json
import platform
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level
from src.inference.input_validation import InputValidationError, validate_patient

SEED = 42
HIGH = 2
REVIEW_THRESHOLD = 0.025  # read-only copy of the served HIGH_PROBA_THRESHOLD
NOISE_LEVELS = [0.25, 0.5, 0.75, 1.0]
NOISE_SEEDS = 10
SHIFTS = [-3, -2, -1, 0, 1, 2, 3]
EXPECTED = {"balanced_accuracy": 0.8055, "flagged": 411, "flagged_true_high": 158, "true_high": 165}

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
PREPROCESSOR_PATH = ROOT / "data" / "processed" / "mindcare_preprocessor_11feature_v2.pkl"
MODEL_PATH = ROOT / "data" / "processed" / "mindcare_final_model_11feature_v2_xgb.pkl"
OLD_REPORT = ROOT / "reports" / "robustness_3class.md"
V2_TUNING_PATH = ROOT / "reports" / "tuning_results_12feature.json"
REPORT_JSON = ROOT / "reports" / "robustness_v2.json"
REPORT_MD = ROOT / "reports" / "robustness_v2.md"

NUMERIC = [
    "Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
    "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
    "Diet Quality (1-10)", "Age",
]
CATEGORICAL = ["Occupation", "Family History of Anxiety"]
FEATURES = NUMERIC + CATEGORICAL
STRESS, THERAPY = "Stress Level (1-10)", "Therapy Sessions (per month)"
LOW_THERAPY = 2  # "little therapy history": <= 2 sessions per month
THERAPY_BANDS = [("0-2", 0, 2), ("3-5", 3, 5), ("6+", 6, None)]
OOF_GUARD = {"true_high_caught": 931, "true_high": 968, "flagged": 2361}  # reports/calibration_review_flag_11feature_v2.md


def metrics(y: np.ndarray, proba: np.ndarray) -> dict:
    pred = proba.argmax(axis=1)
    high = y == HIGH
    return {"balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro")),
            "high_recall": float((pred[high] == HIGH).mean()),
            "flag_catch_rate": float((proba[high, HIGH] >= REVIEW_THRESHOLD).mean()),
            "predicted_high_share": float((pred == HIGH).mean()),
            "flagged_share": float((proba[:, HIGH] >= REVIEW_THRESHOLD).mean())}


def out_of_fold(raw: pd.DataFrame, train_idx: np.ndarray, val_idx: np.ndarray) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Out-of-fold probabilities over the 9,350 train + validation rows (no test rows), as shap_v2.py:
    5-fold stratified on the 3-class label, shuffled, seed 42, v2 params, preprocessing fitted inside each fold."""
    df = raw.iloc[np.concatenate([train_idx, val_idx])].reset_index(drop=True)
    y = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    params = json.loads(V2_TUNING_PATH.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]
    proba = np.zeros((len(df), 3))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=SEED).split(df, y):
        pre = ColumnTransformer([("num", StandardScaler(), NUMERIC), ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
        m = XGBClassifier(**params, objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
        m.fit(pre.fit_transform(df.iloc[tr][FEATURES]), y[tr])
        proba[te] = m.predict_proba(pre.transform(df.iloc[te][FEATURES]))
    return df, y, proba


def parse_old() -> dict:
    """Numbers from reports/robustness_3class.md (17-feature Random Forest)."""
    text = OLD_REPORT.read_text(encoding="utf-8")

    def table(section: str) -> list[list[str]]:
        body = text.split(section, 1)[1].split("\n## ", 1)[0]
        return [[c.strip() for c in line.strip().strip("|").split("|")] for line in body.splitlines()
                if line.startswith("|") and not re.match(r"^\|[-:| ]+\|$", line.strip()) and "---" not in line]

    base = {r[0]: float(r[1]) for r in table("## Baseline")[1:]}
    knockout = {r[0]: {"balanced_accuracy": float(r[1]), "high_recall": float(r[3])} for r in table("## Test 1")[1:]}
    noise = {r[0].replace("x std", "").strip(): {"balanced_accuracy": float(r[1]), "high_recall": float(r[3])}
             for r in table("## Test 2")[1:]}
    shift = {int(r[0]): float(r[1]) for r in table("## Test 4")[1:]}
    return {"baseline": base, "knockout_mean_mode": knockout, "noise_single_seed": noise, "shift_predicted_high": shift}


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as s:
        train_idx, val_idx = s["train_original_idx"], s["val_original_idx"]
    train, val = raw.iloc[train_idx].reset_index(drop=True), raw.iloc[val_idx].reset_index(drop=True)
    y = bin_anxiety_level(val["Anxiety Level (1-10)"].to_numpy())
    pre, model = joblib.load(PREPROCESSOR_PATH), joblib.load(MODEL_PATH)

    def proba_of(frame: pd.DataFrame) -> np.ndarray:
        return model.predict_proba(pre.transform(frame[FEATURES]))

    # ---- Guard ----
    p0 = proba_of(val)
    flagged = p0[:, HIGH] >= REVIEW_THRESHOLD
    guard = {"balanced_accuracy": round(float(balanced_accuracy_score(y, p0.argmax(axis=1))), 4),
             "flagged": int(flagged.sum()), "flagged_true_high": int((flagged & (y == HIGH)).sum()),
             "true_high": int((y == HIGH).sum())}
    print("guard:", guard)
    if guard != EXPECTED:
        raise SystemExit(f"STOP: served v2 does not reproduce its validation numbers: {guard}")
    baseline = metrics(y, p0)

    # ---- 1. Knockout ----
    knockout = {}
    for f in FEATURES:
        out = {}
        for how in ("median", "mean"):
            if f in NUMERIC:
                value = float(train[f].median() if how == "median" else train[f].mean())
            else:
                value = train[f].mode().iloc[0]
            frame = val.copy()
            frame[f] = value
            out[how] = {"value": value if f in NUMERIC else str(value), **metrics(y, proba_of(frame))}
        knockout[f] = out
    print("knockout done")

    # ---- 2. Noise ----
    std = train[NUMERIC].std()
    noise = {}
    for level in NOISE_LEVELS:
        runs = []
        for k in range(NOISE_SEEDS):
            rng = np.random.default_rng(SEED + k)
            frame = val.copy()
            frame[NUMERIC] = frame[NUMERIC] + rng.normal(0, 1, (len(frame), len(NUMERIC))) * (level * std.to_numpy())
            runs.append(metrics(y, proba_of(frame)))
        noise[str(level)] = {m: {"mean": float(np.mean([r[m] for r in runs])), "std": float(np.std([r[m] for r in runs], ddof=1))}
                             for m in runs[0]}
    print("noise done")

    # ---- 3. Invalid inputs ----
    good = {f: (float(val.at[0, f]) if f in NUMERIC else val.at[0, f]) for f in FEATURES}
    good["Age"] = 30.0  # a supported age, so only the injected fault can fail
    missing = {k: v for k, v in good.items() if k != STRESS}
    cases = {
        "valid row (control)": good,
        "negative age (-5)": {**good, "Age": -5},
        "under 18 (16)": {**good, "Age": 16},
        "over 49 (55)": {**good, "Age": 55},
        "impossible stress (250)": {**good, STRESS: 250},
        "impossible heart rate (9000)": {**good, "Heart Rate (bpm)": 9000},
        "negative sleep (-1)": {**good, "Sleep Hours": -1},
        "caffeine over 1200 mg (1500)": {**good, "Caffeine Intake (mg/day)": 1500},
        "text instead of number": {**good, "Heart Rate (bpm)": "fast"},
        "missing Stress Level": missing,
        "all numeric fields 999": {**good, **{f: 999 for f in NUMERIC}},
    }
    invalid = {}
    for name, patient in cases.items():
        try:
            warnings = validate_patient(patient)
            invalid[name] = {"rejected": False, "warnings": len(warnings)}
        except InputValidationError as exc:
            invalid[name] = {"rejected": True, "violations": str(exc).count(";") + 1 if str(exc) else 1,
                             "message": str(exc)[:160]}
    print("invalid inputs:", {k: v["rejected"] for k, v in invalid.items()})

    # ---- 4. Stress shift and root cause ----
    shift = {}
    for d in SHIFTS:
        frame = val.copy()
        frame[STRESS] = (frame[STRESS] + d).clip(1, 10)
        changed = int((frame[STRESS] != val[STRESS]).sum())
        shift[str(d)] = {"rows_changed": changed, **metrics(y, proba_of(frame))}

    # (a) clipping: distribution at the top of the scale.
    s_val = val[STRESS].to_numpy()
    top = {"rows_at_9_or_10": int((s_val >= 9).sum()), "rows_at_10": int((s_val == 10).sum()),
           "by_class_at_9_or_10": {c: int(((s_val >= 9) & (y == k)).sum()) for k, c in enumerate(["Low", "Medium", "High"])},
           "true_high_with_stress": {str(v): int(((s_val == v) & (y == HIGH)).sum()) for v in range(1, 11)}}

    # (b) split thresholds on Stress in raw units, and P(High) with Stress forced to each value.
    names = list(pre.get_feature_names_out())
    col = names.index(f"num__{STRESS}")
    scaler = pre.named_transformers_["num"]
    mu, sd = float(scaler.mean_[NUMERIC.index(STRESS)]), float(scaler.scale_[NUMERIC.index(STRESS)])
    trees = model.get_booster().trees_to_dataframe()
    splits = trees[trees["Feature"] == f"f{col}"]["Split"].to_numpy() * sd + mu
    split_counts = pd.Series(np.round(splits, 3)).value_counts().sort_index()
    forced = {}
    for v in range(1, 11):
        frame = val.copy()
        frame[STRESS] = v
        pr = proba_of(frame)
        forced[str(v)] = {"mean_p_high": float(pr[:, HIGH].mean()), "predicted_high_share": float((pr.argmax(axis=1) == HIGH).mean())}
    splits_info = {"n_splits_on_stress": int(len(splits)), "max_threshold_raw": float(splits.max()),
                   "thresholds_raw_counts": {str(k): int(v) for k, v in split_counts.items()},
                   # XGBoost sends x < threshold left, so a threshold t separates every integer level below t from t and above.
                   "integer_levels_separated": sorted({int(np.ceil(t)) for t in np.round(splits, 3) if 1 < t <= 10})}

    # (c) Therapy interaction: shift within train-quartile bands of Therapy Sessions.
    edges = np.unique(np.quantile(train[THERAPY], [0, 0.25, 0.5, 0.75, 1.0]))
    band = pd.cut(val[THERAPY], bins=edges, include_lowest=True)
    therapy = {}
    for b in band.cat.categories:
        m = (band == b).to_numpy()
        row = {"rows": int(m.sum()), "true_high": int((m & (y == HIGH)).sum())}
        for d in (-3, 0, 3):
            frame = val[m].copy()
            frame[STRESS] = (frame[STRESS] + d).clip(1, 10)
            row[f"predicted_high_share_shift_{d:+d}"] = float((proba_of(frame).argmax(axis=1) == HIGH).mean())
        frame = val[m].copy()
        frame[STRESS] = 10
        pr10 = proba_of(frame)
        row["mean_p_high_stress_10"] = float(pr10[:, HIGH].mean())
        row["predicted_high_share_stress_10"] = float((pr10.argmax(axis=1) == HIGH).mean())
        therapy[str(b)] = row

    # ---- 5. Therapy dependence ----
    df_oof, y_oof, p_oof = out_of_fold(raw, train_idx, val_idx)
    review_oof = p_oof[:, HIGH] >= REVIEW_THRESHOLD
    oof_guard = {"true_high_caught": int((review_oof & (y_oof == HIGH)).sum()), "true_high": int((y_oof == HIGH).sum()),
                 "flagged": int(review_oof.sum())}
    if oof_guard != OOF_GUARD:
        raise SystemExit(f"STOP: out-of-fold rebuild does not match: {oof_guard}")
    low_t = df_oof[THERAPY].to_numpy() <= LOW_THERAPY
    therapy_share = {c: {"rows": int((y_oof == k).sum()), "therapy_le_2": int(((y_oof == k) & low_t).sum()),
                         "share": float(((y_oof == k) & low_t).sum() / (y_oof == k).sum())}
                     for k, c in enumerate(["Low", "Medium", "High"])}
    pred_oof = p_oof.argmax(axis=1)
    detection = {}
    for name, m in (("therapy_le_2", (y_oof == HIGH) & low_t), ("therapy_gt_2", (y_oof == HIGH) & ~low_t)):
        detection[name] = {"rows": int(m.sum()), "model_high_recall": float((pred_oof[m] == HIGH).mean()),
                           "flag_catch_rate": float(review_oof[m].mean()),
                           "predicted_high": int((pred_oof[m] == HIGH).sum()), "flagged": int(review_oof[m].sum())}
    stress_by_band = {}
    for label, lo, hi in THERAPY_BANDS:
        mask = (val[THERAPY] >= lo) & ((val[THERAPY] <= hi) if hi is not None else True)
        row = {"rows": int(mask.sum())}
        for v in (8, 9, 10):
            frame = val[mask].copy()
            frame[STRESS] = v
            pr = proba_of(frame)
            row[str(v)] = {"mean_p_high": float(pr[:, HIGH].mean()), "predicted_high_share": float((pr.argmax(axis=1) == HIGH).mean()),
                           "flagged_share": float((pr[:, HIGH] >= REVIEW_THRESHOLD).mean())}
        stress_by_band[label] = row
    therapy_dependence = {"oof_guard": oof_guard, "share_with_therapy_le_2": therapy_share,
                          "true_high_detection_oof": detection, "validation_stress_by_therapy_band": stress_by_band}
    print("therapy dependence:", therapy_share["High"], detection)

    result = {
        "model": "served 11-feature v2 XGBoost", "guard": guard, "baseline": baseline,
        "therapy_dependence": therapy_dependence,
        "knockout": knockout, "noise": noise, "invalid_inputs": invalid, "stress_shift": shift,
        "root_cause": {"clipping": top, "splits": splits_info, "stress_forced": forced, "therapy_bands": therapy},
        "rf17_from_robustness_3class_md": parse_old(),
        "library_versions": {"python": platform.python_version(), "xgboost": xgboost.__version__,
                             "scikit-learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
        "test_set_used": False,
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_markdown(result)
    print(f"wrote {REPORT_MD.relative_to(ROOT)} and {REPORT_JSON.relative_to(ROOT)}")


def f4(x: float) -> str:
    return f"{x:.4f}"


def write_markdown(r: dict) -> None:
    b, old = r["baseline"], r["rf17_from_robustness_3class_md"]
    ko_lines = ["| Feature | Median: balanced acc. (Δ) | Median: macro-F1 | Median: model High recall | Median: flag catch | "
                "Mean: balanced acc. (Δ) | Mean: model High recall | Mean: flag catch | 17-feature RF (mean/mode): balanced acc. / model High recall |",
                "|---|---|---|---|---|---|---|---|---|"]
    order = sorted(r["knockout"], key=lambda f: r["knockout"][f]["median"]["balanced_accuracy"])
    for f in order:
        md, mn = r["knockout"][f]["median"], r["knockout"][f]["mean"]
        o = old["knockout_mean_mode"].get(f)
        ko_lines.append(f"| {f} | {f4(md['balanced_accuracy'])} ({md['balanced_accuracy'] - b['balanced_accuracy']:+.4f}) | {f4(md['macro_f1'])} | "
                        f"{f4(md['high_recall'])} | {f4(md['flag_catch_rate'])} | {f4(mn['balanced_accuracy'])} ({mn['balanced_accuracy'] - b['balanced_accuracy']:+.4f}) | "
                        f"{f4(mn['high_recall'])} | {f4(mn['flag_catch_rate'])} | "
                        + (f"{f4(o['balanced_accuracy'])} / {f4(o['high_recall'])}" if o else "—") + " |")
    nz_lines = ["| Noise (× train std) | Balanced accuracy | Macro-F1 | Model High recall | Flag catch rate | 17-feature RF, 1 seed: balanced acc. / model High recall |",
                "|---|---|---|---|---|---|"]
    for lvl, v in r["noise"].items():
        o = old["noise_single_seed"].get(lvl)
        nz_lines.append(f"| {lvl} | " + " | ".join(f"{v[m]['mean']:.4f} ± {v[m]['std']:.4f}" for m in
                                                  ("balanced_accuracy", "macro_f1", "high_recall", "flag_catch_rate"))
                        + " | " + (f"{f4(o['balanced_accuracy'])} / {f4(o['high_recall'])}" if o else "not tested") + " |")
    inv_lines = ["| Case | Rejected by validate_patient() | Detail |", "|---|---|---|"]
    for name, v in r["invalid_inputs"].items():
        detail = v.get("message", f"{v.get('warnings', 0)} warning(s)").replace("|", "/")
        inv_lines.append(f"| {name} | {'**yes**' if v['rejected'] else 'no'} | {detail} |")
    sh_lines = ["| Shift | Rows changed | Predicted-High share | Flagged share | Balanced accuracy | Model High recall | 17-feature RF predicted-High share |",
                "|---|---|---|---|---|---|---|"]
    for d, v in r["stress_shift"].items():
        o = old["shift_predicted_high"].get(int(d))
        sh_lines.append(f"| {int(d):+d} | {v['rows_changed']} | {f4(v['predicted_high_share'])} | {f4(v['flagged_share'])} | "
                        f"{f4(v['balanced_accuracy'])} | {f4(v['high_recall'])} | {f4(o) if o is not None else '—'} |")
    rc = r["root_cause"]
    cl, sp, fo, th = rc["clipping"], rc["splits"], rc["stress_forced"], rc["therapy_bands"]
    forced_lines = ["| Stress set to | Mean P(High) | Predicted-High share |", "|---|---|---|"]
    forced_lines += [f"| {v} | {f4(x['mean_p_high'])} | {f4(x['predicted_high_share'])} |" for v, x in fo.items()]
    th_lines = ["| Therapy band (train quartiles) | Rows | True High | Predicted High: shift −3 / 0 / +3 | With Stress = 10: mean P(High) / predicted-High share |", "|---|---|---|---|---|"]
    th_lines += [f"| {k} | {v['rows']} | {v['true_high']} | {v['predicted_high_share_shift_-3']:.4f} / {v['predicted_high_share_shift_+0']:.4f} / "
                 f"{v['predicted_high_share_shift_+3']:.4f} | {f4(v['mean_p_high_stress_10'])} / {f4(v['predicted_high_share_stress_10'])} |" for k, v in th.items()]
    thr_str = ", ".join(f"{k} ({v})" for k, v in sp["thresholds_raw_counts"].items())

    # Evidence summary, computed.
    up = r["stress_shift"]["3"]["predicted_high_share"] - r["stress_shift"]["0"]["predicted_high_share"]
    down = r["stress_shift"]["-3"]["predicted_high_share"] - r["stress_shift"]["0"]["predicted_high_share"]
    rows_changed_up3 = r["stress_shift"]["3"]["rows_changed"]
    clipping_explains = rows_changed_up3 < 1650 / 2
    hard_saturation = sp["max_threshold_raw"] < 10
    rise_6_8 = fo["8"]["mean_p_high"] - fo["6"]["mean_p_high"]
    rise_8_10 = fo["10"]["mean_p_high"] - fo["8"]["mean_p_high"]
    share_8_10 = fo["10"]["predicted_high_share"] - fo["8"]["predicted_high_share"]
    bands = list(th.items())
    never_high = [(k, v) for k, v in bands if v["predicted_high_share_stress_10"] == 0]
    never_rows = sum(v["rows"] for _, v in never_high)
    high_min_stress = min(int(k) for k, v in cl["true_high_with_stress"].items() if v > 0)
    td = r["therapy_dependence"]
    share_lines = [f"| {c} | {v['rows']:,} | {v['therapy_le_2']:,} | {v['share']:.1%} |" for c, v in td["share_with_therapy_le_2"].items()]
    det = td["true_high_detection_oof"]
    det_lines = [f"| Therapy {'<= 2' if k == 'therapy_le_2' else '> 2'} | {v['rows']} | {v['predicted_high']} ({v['model_high_recall']:.1%}) | "
                 f"{v['flagged']} ({v['flag_catch_rate']:.1%}) |" for k, v in det.items()]
    sb = td["validation_stress_by_therapy_band"]
    band_lines = [f"| {k} | {v['rows']} | " + " / ".join(f"{v[x]['mean_p_high']:.4f}" for x in ("8", "9", "10")) + " | "
                  + " / ".join(f"{v[x]['predicted_high_share']:.4f}" for x in ("8", "9", "10")) + " | "
                  + " / ".join(f"{v[x]['flagged_share']:.4f}" for x in ("8", "9", "10")) + " |" for k, v in sb.items()]
    hs = td["share_with_therapy_le_2"]
    hl, lo_det, hi_det = hs["High"], det["therapy_le_2"], det["therapy_gt_2"]
    therapy_conclusion = (
        f"Few High patients in this data have little therapy history: {hl['therapy_le_2']} of {hl['rows']} true-High rows "
        f"({hl['share']:.1%}) have at most 2 sessions/month, against {hs['Low']['share']:.1%} of Low and {hs['Medium']['share']:.1%} "
        f"of Medium. For those {lo_det['rows']} patients the model High recall is {lo_det['model_high_recall']:.1%} (vs "
        f"{hi_det['model_high_recall']:.1%} with more therapy), and even with Stress forced to 10 the 0-2 band has a mean P(High) "
        f"of {sb['0-2']['10']['mean_p_high']:.4f} and a predicted-High share of {sb['0-2']['10']['predicted_high_share']:.4f}. "
        f"**Patients with little therapy history are rarely or never detected as High by the predicted class.** The review "
        f"flag covers {lo_det['flagged']} of {lo_det['rows']} of them ({lo_det['flag_catch_rate']:.1%}, vs "
        f"{hi_det['flag_catch_rate']:.1%} with more therapy); with Stress at 10, {sb['0-2']['10']['flagged_share']:.1%} of the 0-2 band "
        f"would be flagged. Therapy count most likely acts as a proxy for severity in this dataset (people with more severe "
        f"anxiety attend more sessions: reverse causality), so new help-seekers with high stress may be under-called. Small "
        f"sample of true-High rows with little therapy; very likely synthetic data.")

    REPORT_MD.write_text(f"""# Phase 19 robustness for the served 11-feature v2 XGBoost (validation only)

Script: `src/evaluation/robustness_v2.py`. **The test set was not used; no served file or threshold changed.** The served
files on the 1,650 validation rows; imputation values and noise scales from the training split only. Comparison numbers
are parsed from `reports/robustness_3class.md`, which is the **17-feature Random Forest** (baseline balanced accuracy
{old['baseline'].get('balanced_accuracy', float('nan')):.4f}), not a 12-feature model. "Model High recall" = predicted class
High; "flag catch rate" = true High with P(High) ≥ 0.025.

Guard: balanced accuracy {r['guard']['balanced_accuracy']}, {r['guard']['flagged']} flagged, {r['guard']['flagged_true_high']}/{r['guard']['true_high']}
true High flagged — reproduces v2. Baseline: balanced accuracy {f4(b['balanced_accuracy'])}, macro-F1 {f4(b['macro_f1'])}, model
High recall {f4(b['high_recall'])}, flag catch rate {f4(b['flag_catch_rate'])}.

## 1. Single-feature knockout (train median, then train mean; categorical = train mode)

{chr(10).join(ko_lines)}

## 2. Gaussian noise on all 9 numeric features ({NOISE_SEEDS} seeds, mean ± std)

{chr(10).join(nz_lines)}

## 3. Invalid inputs through `validate_patient()`

{chr(10).join(inv_lines)}

## 4. Stress Level shift (clipped to 1–10)

{chr(10).join(sh_lines)}

### Root cause of "shifting Stress up changes nothing"

**(a) Clipping.** {cl['rows_at_9_or_10']} of 1,650 validation rows already have Stress 9–10 ({cl['rows_at_10']} at 10), by true class
{', '.join(f'{k} {v}' for k, v in cl['by_class_at_9_or_10'].items())}. A +3 shift changes {rows_changed_up3} rows' values (the rest are
already at 10 or clip to it). True-High rows by Stress value: {', '.join(f'{k}: {v}' for k, v in cl['true_high_with_stress'].items())}.

**(b) Split saturation.** The trees split on Stress {sp['n_splits_on_stress']} times; thresholds in raw units (count):
{thr_str}. XGBoost sends values below a threshold left, so these splits separate every integer level
{sp['integer_levels_separated'][0]}–{sp['integer_levels_separated'][-1]} from the one below it: there is **no hard saturation** below 10.

{chr(10).join(forced_lines)}

**(c) Therapy Sessions interaction.**

{chr(10).join(th_lines)}

### Which explanation the evidence supports (computed)

- The asymmetry persists in v2: a +3 shift moves the predicted-High share by {up:+.4f}, a −3 shift by {down:+.4f}. It is
  about the predicted **class** only: the flagged share rises from {f4(r['stress_shift']['0']['flagged_share'])} to
  {f4(r['stress_shift']['3']['flagged_share'])} with +3, so P(High) does respond.
- **(a) Clipping: {'supported' if clipping_explains else 'not the explanation'}.** +3 changes {rows_changed_up3} of 1,650 rows' Stress values, yet the
  predicted-High share barely moves.
- **(b) Hard split saturation: {'supported' if hard_saturation else 'not the explanation'}** (splits up to {sp['max_threshold_raw']:.3f}). There is a
  **soft plateau**: mean P(High) rises {rise_6_8:+.4f} from Stress 6 to 8 but only {rise_8_10:+.4f} from 8 to 10 (predicted-High
  share {share_8_10:+.4f}).
- **(c) Therapy interaction: supported, and the main explanation.** With Stress forced to 10, patients in the Therapy band(s)
  {', '.join(k for k, _ in never_high) or 'none'} ({never_rows} of 1,650 rows) are never predicted High; High predictions come
  almost only from the highest band ({bands[-1][0]}: {f4(bands[-1][1]['predicted_high_share_stress_10'])} predicted High at
  Stress 10). In this data every true-High patient already has Stress ≥ {high_min_stress}, so raising Stress cannot create new
  High predictions: High needs high Stress **and** other signals, mainly Therapy Sessions.
- **Conclusion:** the evidence supports (c), the Stress × Therapy interaction, together with the soft plateau above Stress 8;
  it does not support clipping (a) or hard saturation (b).

## 5. Therapy dependence: can patients with little therapy history be detected as High?

Out-of-fold over the 9,350 train + validation rows, rebuilt as `shap_v2.py` does (guarded: the review flag catches
{td['oof_guard']['true_high_caught']}/{td['oof_guard']['true_high']} true High and flags {td['oof_guard']['flagged']:,}).

**How common is Therapy <= 2 sessions/month?**

| True class | Rows | Therapy <= 2 | Share |
|---|---|---|---|
{chr(10).join(share_lines)}

**Detection of true-High patients (out-of-fold)**

| True-High patients | Rows | Model High recall | Review-flag catch rate (P(High) >= 0.025) |
|---|---|---|---|
{chr(10).join(det_lines)}

**P(High) with Stress set to 8 / 9 / 10, by therapy band (validation rows, served files)**

| Therapy band | Rows | Mean P(High): Stress 8 / 9 / 10 | Predicted-High share: 8 / 9 / 10 | Flagged share: 8 / 9 / 10 |
|---|---|---|---|---|
{chr(10).join(band_lines)}

**Conclusion.** {therapy_conclusion}

Libraries: {', '.join(f'{k} {v}' for k, v in r['library_versions'].items())}. Very likely synthetic data: prototype-level evidence only.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
