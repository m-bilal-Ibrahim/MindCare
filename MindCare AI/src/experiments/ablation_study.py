"""Ablation study, PCA check and significance tests for the served 11-feature v2 XGBoost.

Validation/CV only: the 1,650 test rows are never loaded. No served file or threshold is changed; the served
files are only read (guard). Every variant is re-run here, never copied from an old report; old report numbers
are shown next to the re-run with a flag where the configuration is the same and the numbers differ.

- Guard: the served files reproduce validation balanced accuracy 0.8055, 411 flagged, 158/165 true High flagged
  at P(High) >= 0.025; v2 retrained here on the training split must reproduce the same 0.8055.
- Validation split: each variant fitted on the 7,700 training rows, scored on the 1,650 validation rows.
- Paired CV: the 9,350 train + validation rows, 5-fold stratified on the 3-class label, shuffled, seed 42, the
  same folds for every variant, preprocessing fitted inside each fold. Change = variant - v2, per fold.
- Significance: paired t-test on the 5 fold balanced accuracies (folds share training data, so p-values are
  approximate) and an exact McNemar test (binomial on discordant pairs) on validation-split correctness.
- Therapy Sessions removed: low-therapy detection, its own review threshold (no 0.025), SHAP and a Stress check.
- PCA: v2's XGBoost on PCA components (95% / 99% variance) fitted inside each fold on training rows only.

Run from MindCare AI/: python -m src.experiments.ablation_study
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from scipy.stats import binomtest, ttest_rel
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import DMatrix, XGBClassifier

from src.build_3class_target import bin_anxiety_level

SEED = 42
FOLDS = 5
HIGH = 2
REVIEW_THRESHOLD = 0.025  # read-only copy of the served HIGH_PROBA_THRESHOLD
GUARD = {"balanced_accuracy": 0.8055, "flagged": 411, "flagged_true_high": 158, "true_high": 165}
V2_OOF_LOW_THERAPY = {"rows": 54, "predicted_high": 0, "flagged": 33}  # reports/robustness_v2.md, section 5

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
PREPROCESSOR_PATH = ROOT / "data" / "processed" / "mindcare_preprocessor_11feature_v2.pkl"
MODEL_PATH = ROOT / "data" / "processed" / "mindcare_final_model_11feature_v2_xgb.pkl"
TUNING_12 = ROOT / "reports" / "tuning_results_12feature.json"
ADVANCED = ROOT / "reports" / "advanced_models_3class.json"
REPORT_JSON = ROOT / "reports" / "ablation_study.json"
REPORT_MD = ROOT / "reports" / "ablation_study.md"

V2_NUMERIC = ["Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
              "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
              "Diet Quality (1-10)", "Age"]
V2_CATEGORICAL = ["Occupation", "Family History of Anxiety"]
DROPPED_17_NUMERIC = ["Alcohol Consumption (drinks/week)", "Sweating Level (1-5)"]
DROPPED_17_CATEGORICAL = ["Smoking", "Dizziness", "Medication", "Recent Major Life Event"]
DERIVED = ["sleep_deficit", "stress_x_sleepdef", "arousal_index", "lifestyle_score", "caffeine_per_sleep"]
STRESS, THERAPY, CAFFEINE = "Stress Level (1-10)", "Therapy Sessions (per month)", "Caffeine Intake (mg/day)"
THERAPY_BANDS = [("0-2", 0, 2), ("3-5", 3, 5), ("6+", 6, None)]


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Same stateless features as src/experiments/derived_features_11feature.py (branch #57)."""
    out = df.copy()
    sleep = out["Sleep Hours"]
    out["sleep_deficit"] = np.maximum(0.0, 8.0 - sleep)
    out["stress_x_sleepdef"] = out[STRESS] * out["sleep_deficit"]
    out["arousal_index"] = (out["Heart Rate (bpm)"] - 70) / 70 + (out["Breathing Rate (breaths/min)"] - 16) / 16
    out["lifestyle_score"] = (np.minimum(sleep / 8, 1) + np.minimum(out["Physical Activity (hrs/week)"] / 5, 1)
                              + out["Diet Quality (1-10)"] / 10) / 3
    out["caffeine_per_sleep"] = out[CAFFEINE] / sleep
    return out


class Variant:
    def __init__(self, key: str, label: str, numeric: list[str], categorical: list[str], kind: str = "xgb",
                 weighting: str = "none", pca: float | None = None):
        self.key, self.label, self.numeric, self.categorical = key, label, numeric, categorical
        self.kind, self.weighting, self.pca = kind, weighting, pca

    def features(self) -> list[str]:
        return self.numeric + self.categorical

    def fit(self, frame: pd.DataFrame, y: np.ndarray, params: dict):
        steps = [("pre", ColumnTransformer([("num", StandardScaler(), self.numeric),
                                            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.categorical)]))]
        if self.pca:
            steps.append(("pca", PCA(n_components=self.pca, svd_solver="full", random_state=SEED)))
        if self.kind == "xgb":
            est = XGBClassifier(**params["xgb"], objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
        elif self.kind == "isotonic":
            est = CalibratedClassifierCV(
                XGBClassifier(**params["xgb"], objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1),
                method="isotonic", cv=StratifiedKFold(FOLDS, shuffle=True, random_state=SEED), ensemble=False)
        elif self.kind == "rf":
            est = RandomForestClassifier(**params["rf"], random_state=SEED, n_jobs=-1)
        else:
            est = MLPClassifier(**params["mlp"], max_iter=500, early_stopping=True, n_iter_no_change=15, random_state=SEED)
        pipe = Pipeline(steps + [("model", est)])
        fit_kw = {"model__sample_weight": compute_sample_weight("balanced", y)} if self.weighting == "balanced" else {}
        pipe.fit(frame[self.features()], y, **fit_kw)
        return pipe


def scores(y: np.ndarray, proba: np.ndarray) -> dict:
    pred = proba.argmax(axis=1)
    return {"balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro")),
            "high_recall": float((pred[y == HIGH] == HIGH).mean())}


def mcnemar(correct_a: np.ndarray, correct_b: np.ndarray) -> dict:
    b = int((correct_a & ~correct_b).sum())
    c = int((~correct_a & correct_b).sum())
    p = float(binomtest(min(b, c), b + c, 0.5).pvalue) if b + c else 1.0
    return {"only_first_correct": b, "only_second_correct": c, "p_value": p}


def git_json(ref_path: str) -> dict | None:
    try:
        out = subprocess.run(["git", "show", ref_path], capture_output=True, check=True, cwd=ROOT)
        return json.loads(out.stdout.decode("utf-8"))
    except Exception:
        return None


def md_delta(path: Path, metric: str) -> float:
    m = re.search(rf"^\| {re.escape(metric)} \| ([+-][0-9.]+) \|", path.read_text(encoding="utf-8"), flags=re.M)
    return float(m.group(1))


def old_reports() -> dict:
    """Earlier numbers, converted to the same direction (variant - comparison model). 'same_config' marks rows
    where the old run used the same model and settings as here, so a difference is a real discrepancy."""
    rep = ROOT / "reports"
    out = {}
    for key, fname, sign in (("f17", "feature_reduction_3class.md", -1), ("no_age", "feature_addition_age_3class.md", -1),
                             ("no_caffeine", "feature_reduction_caffeine_3class.md", +1)):
        out[key] = {"source": f"reports/{fname} (tuned Random Forest, validation split)", "same_config": False,
                    "validation": {"balanced_accuracy": sign * md_delta(rep / fname, "Balanced accuracy"),
                                   "macro_f1": sign * md_delta(rep / fname, "Macro-F1"),
                                   "high_recall": sign * md_delta(rep / fname, "Recall High")}}
    sw = json.loads((rep / "feature_reduction_sweatlevel_3class.json").read_text(encoding="utf-8"))["validation"]
    out["with_sweat"] = {"source": "reports/feature_reduction_sweatlevel_3class.json (same XGBoost, validation split)", "same_config": True,
                         "validation": {"balanced_accuracy": sw["full_12"]["balanced_accuracy"] - sw["reduced_11"]["balanced_accuracy"],
                                        "macro_f1": sw["full_12"]["macro_f1"] - sw["reduced_11"]["macro_f1"],
                                        "high_recall": sw["full_12"]["recall_High"] - sw["reduced_11"]["recall_High"]}}
    d = git_json("origin/ai/derived-features-fairness:MindCare AI/reports/derived_features_11feature.json")
    if d:
        out["derived"] = {"source": "reports/derived_features_11feature.json (branch of PR #57; same XGBoost, same folds)", "same_config": True,
                          "cv": {m: {"mean": d["paired_gain"][m]["mean"], "std": d["paired_gain"][m]["std"]}
                                 for m in ("balanced_accuracy", "macro_f1", "high_recall")}}
    c = git_json("origin/ai/derived-features-fairness:MindCare AI/reports/calibration_review_flag_11feature_v2.json")
    if c:
        out["isotonic"] = {"source": "reports/calibration_review_flag_11feature_v2.json (branch of PR #57; pooled out-of-fold, not a fold mean)",
                           "same_config": False, "pooled_oof": c["calibrated_minus_uncalibrated"]}
    mc = json.loads((rep / "model_comparison_12feature.json").read_text(encoding="utf-8"))
    out["rf"] = {"source": "reports/model_comparison_12feature.json (12 features, validation split)", "same_config": False,
                 "validation": {m: mc["rf_retuned"]["validation"][m] - mc["xgb_retuned"]["validation"][m]
                                for m in ("balanced_accuracy", "macro_f1") if m in mc["rf_retuned"]["validation"]}}
    out["mlp"] = {"source": "reports/advanced_models_3class.md (17 features): MLP 0.8041 vs XGBoost 0.8074 balanced accuracy",
                  "same_config": False}
    return out


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as s:
        train_idx, val_idx = s["train_original_idx"], s["val_original_idx"]
    train = add_derived(raw.iloc[train_idx].reset_index(drop=True))
    val = add_derived(raw.iloc[val_idx].reset_index(drop=True))
    y_tr = bin_anxiety_level(train["Anxiety Level (1-10)"].to_numpy())
    y_val = bin_anxiety_level(val["Anxiety Level (1-10)"].to_numpy())

    # ---- 0. Guard on the served files ----
    pre, served = joblib.load(PREPROCESSOR_PATH), joblib.load(MODEL_PATH)
    p_served = served.predict_proba(pre.transform(val[V2_NUMERIC + V2_CATEGORICAL]))
    flagged = p_served[:, HIGH] >= REVIEW_THRESHOLD
    guard = {"balanced_accuracy": round(float(balanced_accuracy_score(y_val, p_served.argmax(axis=1))), 4),
             "flagged": int(flagged.sum()), "flagged_true_high": int((flagged & (y_val == HIGH)).sum()),
             "true_high": int((y_val == HIGH).sum())}
    print("guard:", guard)
    if guard != GUARD:
        raise SystemExit(f"STOP: served v2 does not reproduce its validation numbers: {guard}")

    t12 = json.loads(TUNING_12.read_text(encoding="utf-8"))["models"]
    mlp_p = json.loads(ADVANCED.read_text(encoding="utf-8"))["mlp"]["best_params"]
    mlp_p["hidden_layer_sizes"] = tuple(mlp_p["hidden_layer_sizes"])
    params = {"xgb": t12["xgboost"]["best_params"], "rf": t12["random_forest"]["best_params"], "mlp": mlp_p}
    num, cat = V2_NUMERIC, V2_CATEGORICAL
    variants = [
        Variant("v2", "Served v2 (11 features, XGBoost, unweighted)", num, cat),
        Variant("f17", "17 features instead of 11", num + DROPPED_17_NUMERIC, cat + DROPPED_17_CATEGORICAL),
        Variant("no_age", "Age removed (10 features)", [f for f in num if f != "Age"], cat),
        Variant("with_sweat", "Sweating Level kept (12 features)", num + ["Sweating Level (1-5)"], cat),
        Variant("no_caffeine", "Caffeine dropped (10 features)", [f for f in num if f != CAFFEINE], cat),
        Variant("derived", "Derived features added (16 features)", num + DERIVED, cat),
        Variant("balanced", "Balanced class weights", num, cat, weighting="balanced"),
        Variant("isotonic", "Isotonic calibration", num, cat, kind="isotonic"),
        Variant("rf", "Random Forest instead of XGBoost", num, cat, kind="rf"),
        Variant("mlp", "MLP instead of XGBoost", num, cat, kind="mlp"),
        Variant("no_therapy", "Therapy Sessions removed (10 features)", [f for f in num if f != THERAPY], cat),
        Variant("pca95", "PCA, 95% of variance", num, cat, pca=0.95),
        Variant("pca99", "PCA, 99% of variance", num, cat, pca=0.99),
    ]

    # ---- Validation split ----
    val_scores, val_correct, val_proba, fitted = {}, {}, {}, {}
    for v in variants:
        m = v.fit(train, y_tr, params)
        proba = m.predict_proba(val[v.features()])
        val_scores[v.key], val_proba[v.key], fitted[v.key] = scores(y_val, proba), proba, m
        val_correct[v.key] = proba.argmax(axis=1) == y_val
        print(f"validation {v.key}: {val_scores[v.key]}", flush=True)
    if round(val_scores["v2"]["balanced_accuracy"], 4) != GUARD["balanced_accuracy"]:
        raise SystemExit("STOP: v2 retrained here does not reproduce the served 0.8055")

    # ---- Paired CV on train + validation ----
    df = pd.concat([train, val], ignore_index=True)  # no test rows
    y = np.concatenate([y_tr, y_val])
    folds = list(StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y))
    cv = {v.key: [] for v in variants}
    oof = {k: np.zeros((len(df), 3)) for k in ("v2", "no_therapy")}
    pca_components = {"pca95": [], "pca99": []}
    for f, (tr, te) in enumerate(folds):
        for v in variants:
            m = v.fit(df.iloc[tr], y[tr], params)
            proba = m.predict_proba(df.iloc[te][v.features()])
            cv[v.key].append(scores(y[te], proba))
            if v.key in oof:
                oof[v.key][te] = proba
            if v.pca:
                pca_components[v.key].append(int(m.named_steps["pca"].n_components_))
        print(f"fold {f + 1}/{FOLDS} done", flush=True)

    metrics = ("balanced_accuracy", "macro_f1", "high_recall")
    table = {}
    for v in variants[1:]:
        diffs = {m: np.array([cv[v.key][i][m] - cv["v2"][i][m] for i in range(FOLDS)]) for m in metrics}
        table[v.key] = {
            "label": v.label,
            "validation_delta": {m: val_scores[v.key][m] - val_scores["v2"][m] for m in metrics},
            "cv_delta": {m: {"mean": float(diffs[m].mean()), "std": float(diffs[m].std(ddof=1))} for m in metrics},
            "t_test_balanced_accuracy_p": float(ttest_rel([c["balanced_accuracy"] for c in cv[v.key]],
                                                          [c["balanced_accuracy"] for c in cv["v2"]]).pvalue),
            "mcnemar_vs_v2": mcnemar(val_correct["v2"], val_correct[v.key]),
        }
    trio = {}
    for a, b in (("v2", "rf"), ("v2", "mlp"), ("rf", "mlp")):
        trio[f"{a}_vs_{b}"] = {
            "t_test_balanced_accuracy_p": float(ttest_rel([c["balanced_accuracy"] for c in cv[a]], [c["balanced_accuracy"] for c in cv[b]]).pvalue),
            "cv_mean_difference": float(np.mean([cv[a][i]["balanced_accuracy"] - cv[b][i]["balanced_accuracy"] for i in range(FOLDS)])),
            "mcnemar": mcnemar(val_correct[a], val_correct[b])}

    # ---- Therapy Sessions removed: extra detail ----
    nt_var = next(v for v in variants if v.key == "no_therapy")
    low_t = df[THERAPY].to_numpy() <= 2
    is_high = y == HIGH
    v2_review = oof["v2"][:, HIGH] >= REVIEW_THRESHOLD
    v2_low = {"rows": int((is_high & low_t).sum()), "predicted_high": int((oof["v2"].argmax(1)[is_high & low_t] == HIGH).sum()),
              "flagged": int(v2_review[is_high & low_t].sum())}
    if v2_low != V2_OOF_LOW_THERAPY:
        raise SystemExit(f"STOP: v2 out-of-fold low-therapy numbers do not match robustness_v2: {v2_low}")
    v2_catch = float(v2_review[is_high].mean())
    p_nt = oof["no_therapy"][:, HIGH]
    hp = np.sort(p_nt[is_high])
    own = float(hp[int(np.floor((1 - v2_catch) * len(hp) + 1e-9))])  # highest t with catch >= v2's share
    own = float(np.floor(own * 1e4) / 1e4)
    nt_review = p_nt >= own
    assert nt_review[is_high].mean() >= v2_catch
    pred_nt = oof["no_therapy"].argmax(axis=1)
    therapy_detail = {
        "v2_oof_catch_share": v2_catch,
        "own_threshold": own,
        "flagged_total": {"no_therapy_own_threshold": int(nt_review.sum()), "v2_at_0.025": int(v2_review.sum()), "rows": len(df)},
        "low_therapy_true_high": {"v2": v2_low, "no_therapy": {"rows": int((is_high & low_t).sum()),
                                                               "predicted_high": int((pred_nt[is_high & low_t] == HIGH).sum()),
                                                               "flagged_own_threshold": int(nt_review[is_high & low_t].sum())}},
        "other_true_high": {"v2": {"rows": int((is_high & ~low_t).sum()), "predicted_high": int((oof["v2"].argmax(1)[is_high & ~low_t] == HIGH).sum()),
                                   "flagged": int(v2_review[is_high & ~low_t].sum())},
                            "no_therapy": {"rows": int((is_high & ~low_t).sum()), "predicted_high": int((pred_nt[is_high & ~low_t] == HIGH).sum()),
                                           "flagged_own_threshold": int(nt_review[is_high & ~low_t].sum())}},
    }
    # SHAP (High class) for the no-therapy model fitted on the training split, on validation rows.
    m_nt = fitted["no_therapy"]
    x_val_nt = m_nt.named_steps["pre"].transform(val[nt_var.features()])
    booster = m_nt.named_steps["model"].get_booster()
    contrib = booster.predict(DMatrix(x_val_nt), pred_contribs=True)[:, HIGH, :-1]
    names = list(m_nt.named_steps["pre"].get_feature_names_out())
    raw_feats = nt_var.features()
    grouped = {f: np.zeros(len(val)) for f in raw_feats}
    for j, n in enumerate(names):
        rawn = n.split("__", 1)[1]
        f = next(f for f in raw_feats if rawn == f or rawn.startswith(f + "_"))
        grouped[f] += contrib[:, j]
    mean_abs = {f: float(np.abs(v).mean()) for f, v in grouped.items()}
    total = sum(mean_abs.values())
    shap_nt = sorted(({"feature": f, "mean_abs_shap": v, "share": v / total} for f, v in mean_abs.items()), key=lambda r: -r["mean_abs_shap"])
    # Stress forced to 8/9/10 by former therapy band (validation rows, no-therapy model trained on train).
    stress_bands = {}
    for label, lo, hi in THERAPY_BANDS:
        mask = (val[THERAPY] >= lo) & ((val[THERAPY] <= hi) if hi is not None else True)
        row = {"rows": int(mask.sum())}
        for s_val in (8, 9, 10):
            frame = val[mask].copy()
            frame[STRESS] = s_val
            pr_nt = m_nt.predict_proba(frame[nt_var.features()])
            pr_v2 = fitted["v2"].predict_proba(frame[V2_NUMERIC + V2_CATEGORICAL])
            row[str(s_val)] = {"no_therapy_predicted_high_share": float((pr_nt.argmax(1) == HIGH).mean()),
                               "v2_predicted_high_share": float((pr_v2.argmax(1) == HIGH).mean())}
        stress_bands[label] = row
    therapy_detail["shap_high_no_therapy"] = shap_nt
    therapy_detail["stress_forced_by_former_therapy_band"] = stress_bands

    result = {
        "guard": guard, "folds": FOLDS, "seed": SEED, "rows_cv": len(df), "rows_validation": len(val),
        "validation_scores": val_scores, "cv_scores": cv, "ablation": table, "model_family_tests": trio,
        "therapy_removed_detail": therapy_detail, "pca_components_per_fold": pca_components,
        "old_reports": old_reports(),
        "library_versions": {"python": platform.python_version(), "xgboost": xgboost.__version__,
                             "scikit-learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
        "test_set_used": False,
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_markdown(result)
    print(f"wrote {REPORT_MD.relative_to(ROOT)} and {REPORT_JSON.relative_to(ROOT)}")


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values (step-down, monotone, capped at 1)."""
    order = sorted(pvals, key=pvals.get)
    m, out, running = len(order), {}, 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvals[k]))
        out[k] = running
    return out


def reading(p: float, what: str) -> str:
    return (f"evidence of a real difference in {what} (p < 0.05)" if p < 0.05
            else f"no clear evidence of a difference in {what} (p ≥ 0.05)")


def write_markdown(r: dict) -> None:
    ab, old, vs = r["ablation"], r["old_reports"], r["validation_scores"]
    rows = [k for k in ab if not k.startswith("pca")]
    tbl = ["| Decision (variant − v2) | Val Δ macro-F1 | Val Δ balanced acc. | Val Δ model High recall | "
           "CV Δ macro-F1 | CV Δ balanced acc. | CV Δ model High recall | Earlier report |", "|---|---|---|---|---|---|---|---|"]
    flags = []
    for k in rows:
        a = ab[k]
        vd, cd = a["validation_delta"], a["cv_delta"]
        o = old.get(k)
        note = "—"
        if o:
            if "validation" in o and o.get("same_config"):
                diffs = {m: vd[m] - o["validation"][m] for m in o["validation"]}
                bad = {m: d for m, d in diffs.items() if abs(d) > 0.0005}
                note = ("matches" if not bad else "**differs**") + ": " + ", ".join(f"{m} {o['validation'][m]:+.4f}" for m in o["validation"])
                if bad:
                    flags.append(f"{a['label']}: " + ", ".join(f"{m} re-run {vd[m]:+.4f} vs earlier {o['validation'][m]:+.4f}" for m in bad))
            elif "cv" in o and o.get("same_config"):
                bad = {m: abs(cd[m]["mean"] - o["cv"][m]["mean"]) > 0.0005 for m in o["cv"]}
                note = ("matches" if not any(bad.values()) else "**differs**") + ": CV " + ", ".join(f"{m} {o['cv'][m]['mean']:+.4f}" for m in o["cv"])
                if any(bad.values()):
                    flags.append(f"{a['label']}: CV " + ", ".join(f"{m} re-run {cd[m]['mean']:+.4f} vs earlier {o['cv'][m]['mean']:+.4f}" for m, b in bad.items() if b))
            elif "validation" in o:
                note = "different model/config: " + ", ".join(f"{m} {v:+.4f}" for m, v in o["validation"].items())
            elif "pooled_oof" in o:
                note = "pooled out-of-fold: " + ", ".join(f"{m} {v:+.4f}" for m, v in o["pooled_oof"].items())
            else:
                note = "not comparable"
            note += f" ({o['source']})"
        tbl.append(f"| {a['label']} | {vd['macro_f1']:+.4f} | {vd['balanced_accuracy']:+.4f} | {vd['high_recall']:+.4f} | "
                   + " | ".join(f"{cd[m]['mean']:+.4f} ± {cd[m]['std']:.4f}" for m in ("macro_f1", "balanced_accuracy", "high_recall"))
                   + f" | {note} |")
    holm_t = holm({k: ab[k]["t_test_balanced_accuracy_p"] for k in rows})
    holm_mc = holm({k: ab[k]["mcnemar_vs_v2"]["p_value"] for k in rows})
    sig = ["| Variant vs v2 | Paired CV t-test p: raw / Holm | McNemar p (validation): raw / Holm | Only v2 right / only variant right | Reading (Holm-adjusted) |",
           "|---|---|---|---|---|"]
    for k in rows:
        a = ab[k]
        mc = a["mcnemar_vs_v2"]
        sig.append(f"| {a['label']} | {a['t_test_balanced_accuracy_p']:.3f} / {holm_t[k]:.3f} | {mc['p_value']:.3f} / {holm_mc[k]:.3f} | "
                   f"{mc['only_first_correct']} / {mc['only_second_correct']} | "
                   f"CV: {reading(holm_t[k], 'balanced accuracy')}; validation: {reading(holm_mc[k], 'errors')} |")
    raw_sig = [k for k in rows if ab[k]["t_test_balanced_accuracy_p"] < 0.05]
    borderline = [k for k in raw_sig if holm_t[k] >= 0.05]
    survive = [k for k in raw_sig if holm_t[k] < 0.05]
    mc_note = (
        f"**Multiple comparisons.** {len(rows)} variants are each tested against v2, so the p-values are adjusted with "
        f"Holm-Bonferroni (each test family separately). Raw t-test p < 0.05: "
        + (", ".join(f"{ab[k]['label']} (raw {ab[k]['t_test_balanced_accuracy_p']:.3f}, Holm {holm_t[k]:.3f})" for k in raw_sig) or "none")
        + ". "
        + (("These do not survive adjustment, so they are best described as **small, borderline-significant costs**: "
            + ", ".join(f"{ab[k]['label']} (CV Δ balanced acc. {ab[k]['cv_delta']['balanced_accuracy']['mean']:+.4f})" for k in borderline) + ". ")
           if borderline else "")
        + (("Still significant after adjustment: " + ", ".join(ab[k]["label"] for k in survive) + ". ") if survive else "")
        + f"No McNemar comparison is significant after adjustment (smallest Holm p {min(holm_mc.values()):.3f})."
        if all(v >= 0.05 for v in holm_mc.values()) else "")
    names = {"v2": "XGBoost (v2)", "rf": "Random Forest", "mlp": "MLP"}
    mf = r["model_family_tests"]
    holm_ft = holm({k: t["t_test_balanced_accuracy_p"] for k, t in mf.items()})
    holm_fm = holm({k: t["mcnemar"]["p_value"] for k, t in mf.items()})
    trio = ["| Pair | CV mean Δ balanced acc. (first − second) | Paired CV t-test p: raw / Holm | McNemar p: raw / Holm | Only first / only second right | Reading (Holm-adjusted) |",
            "|---|---|---|---|---|---|"]
    for k, t in mf.items():
        a, b = k.split("_vs_")
        mc = t["mcnemar"]
        trio.append(f"| {names[a]} vs {names[b]} | {t['cv_mean_difference']:+.4f} | {t['t_test_balanced_accuracy_p']:.3f} / {holm_ft[k]:.3f} | "
                    f"{mc['p_value']:.3f} / {holm_fm[k]:.3f} | {mc['only_first_correct']} / {mc['only_second_correct']} | "
                    f"CV: {reading(holm_ft[k], 'balanced accuracy')}; validation: {reading(holm_fm[k], 'errors')} |")
    td = r["therapy_removed_detail"]
    lo, oth = td["low_therapy_true_high"], td["other_true_high"]
    ft = td["flagged_total"]
    shap_rows = ["| Rank | Feature | Mean \\|SHAP\\| (High) | Share |", "|---|---|---|---|"]
    shap_rows += [f"| {i + 1} | {x['feature']} | {x['mean_abs_shap']:.4f} | {x['share']:.1%} |" for i, x in enumerate(td["shap_high_no_therapy"])]
    sb = td["stress_forced_by_former_therapy_band"]
    sb_rows = ["| Former therapy band | Rows | Predicted-High share, Stress 8 / 9 / 10: Therapy removed | Same: v2 |", "|---|---|---|---|"]
    sb_rows += [f"| {k} | {v['rows']} | " + " / ".join(f"{v[s]['no_therapy_predicted_high_share']:.4f}" for s in ("8", "9", "10")) + " | "
                + " / ".join(f"{v[s]['v2_predicted_high_share']:.4f}" for s in ("8", "9", "10")) + " |" for k, v in sb.items()]
    pc = r["pca_components_per_fold"]
    pca_rows = ["| Variant | Components per fold | Val Δ macro-F1 | Val Δ balanced acc. | Val Δ model High recall | CV Δ macro-F1 | CV Δ balanced acc. | CV Δ model High recall |",
                "|---|---|---|---|---|---|---|---|"]
    for k in ("pca95", "pca99"):
        a = ab[k]
        pca_rows.append(f"| {a['label']} | {', '.join(map(str, pc[k]))} | " + " | ".join(f"{a['validation_delta'][m]:+.4f}" for m in ("macro_f1", "balanced_accuracy", "high_recall"))
                        + " | " + " | ".join(f"{a['cv_delta'][m]['mean']:+.4f} ± {a['cv_delta'][m]['std']:.4f}" for m in ("macro_f1", "balanced_accuracy", "high_recall")) + " |")
    nt = ab["no_therapy"]
    top3 = ", ".join(x["feature"] for x in td["shap_high_no_therapy"][:3])
    n_low = lo["v2"]["rows"]
    gain_pred = lo["no_therapy"]["predicted_high"] - lo["v2"]["predicted_high"]
    gain_flag = lo["no_therapy"]["flagged_own_threshold"] - lo["v2"]["flagged"]
    fixes_gap = gain_pred >= n_low / 2
    trade = (
        f"Removing it costs overall accuracy and {'does' if fixes_gap else '**does not**'} fix the low-therapy gap: "
        f"{gain_pred:+d} predicted High and {gain_flag:+d} flagged among the {n_low} low-therapy High patients. "
        + ("" if fixes_gap else
           "Dropping the proxy alone does not make the model see them. ")
        + "Keeping it keeps the higher accuracy but leaves the reverse-causality gap to the review flag and the psychologist.")

    REPORT_MD.write_text(f"""# Ablation study, PCA check and significance tests: served 11-feature v2 XGBoost

Script: `src/experiments/ablation_study.py`. **The test set was not used; no served file or threshold changed.** Every variant
was re-run here. Validation split = fitted on the 7,700 training rows, scored on the 1,650 validation rows. Paired CV = the
{r['rows_cv']:,} train + validation rows, 5-fold stratified on the 3-class label, shuffled, seed 42, the same folds for every
variant, preprocessing fitted inside each fold. Δ = variant − v2. "Model High recall" = predicted class High.

Guard: the served files reproduce balanced accuracy {r['guard']['balanced_accuracy']}, {r['guard']['flagged']} flagged,
{r['guard']['flagged_true_high']}/{r['guard']['true_high']} true High flagged; v2 retrained here reproduces validation balanced
accuracy {vs['v2']['balanced_accuracy']:.4f} (macro-F1 {vs['v2']['macro_f1']:.4f}, model High recall {vs['v2']['high_recall']:.4f}).

## 1. Ablation table

{chr(10).join(tbl)}

{('**Re-runs that differ from an earlier report with the same configuration:** ' + '; '.join(flags) + '.') if flags else '**No re-run differs from an earlier report that used the same configuration.** Rows marked "different model/config" compare against earlier Random Forest or 12/17-feature runs and are shown for reference only.'}

## 2. Significance

Paired t-test on the 5 fold balanced accuracies, and an exact McNemar test on which validation patients each model gets right.
**The CV folds share training data, so they are not independent and these p-values are approximate** (they tend to be too small).
With 5 folds the t-test has little power, so "no clear evidence" is not proof of no difference.

{chr(10).join(sig)}

{mc_note}

**Model family (all on the same 11 features):**

{chr(10).join(trio)}

## 3. Therapy Sessions removed (11 → 10 features): detail

Out-of-fold over {r['rows_cv']:,} rows. The variant gets **its own review threshold**, re-derived to match v2's coverage target
(the highest threshold still catching ≥ {td['v2_oof_catch_share']:.1%} of true High, v2's out-of-fold catch share at 0.025): **{td['own_threshold']}**.
It flags **{ft['no_therapy_own_threshold']:,}** of {ft['rows']:,} patients ({ft['no_therapy_own_threshold'] / ft['rows']:.1%}), against {ft['v2_at_0.025']:,}
({ft['v2_at_0.025'] / ft['rows']:.1%}) for v2 at 0.025.

| True-High patients | Rows | v2: predicted High | v2: flagged (0.025) | Therapy removed: predicted High | Therapy removed: flagged (own threshold) |
|---|---|---|---|---|---|
| Therapy ≤ 2 | {lo['v2']['rows']} | {lo['v2']['predicted_high']} | {lo['v2']['flagged']} | {lo['no_therapy']['predicted_high']} | {lo['no_therapy']['flagged_own_threshold']} |
| Therapy > 2 | {oth['v2']['rows']} | {oth['v2']['predicted_high']} | {oth['v2']['flagged']} | {oth['no_therapy']['predicted_high']} | {oth['no_therapy']['flagged_own_threshold']} |

**SHAP for the Therapy-removed model** (High class, exact `pred_contribs`, validation rows; Occupation and Family History summed back):

{chr(10).join(shap_rows)}

**Stress forced to 8 / 9 / 10, by the patient's former therapy band** (validation rows; models fitted on the training split):

{chr(10).join(sb_rows)}

## 4. PCA check (evidence for the report only)

v2's XGBoost settings trained on PCA components of the preprocessed features, PCA fitted inside each fold on training rows only.

{chr(10).join(pca_rows)}

**What PCA loses:** each component mixes all 24 preprocessed columns, so SHAP can only rank components, not real features.
There is no per-feature explanation for the psychologist, no direction check for Sleep, Caffeine, Activity or Diet, and no
feature-level driver for the recommendation engine. The input-validation and alert rules would still work on raw inputs, but
the model's reasons could no longer be tied to them.

## 5. Therapy Sessions decision (for the supervisor; no decision is made here)

- **Overall accuracy cost of removing it:** CV Δ balanced accuracy {nt['cv_delta']['balanced_accuracy']['mean']:+.4f} ± {nt['cv_delta']['balanced_accuracy']['std']:.4f},
  Δ macro-F1 {nt['cv_delta']['macro_f1']['mean']:+.4f}, Δ model High recall {nt['cv_delta']['high_recall']['mean']:+.4f} (validation: {nt['validation_delta']['balanced_accuracy']:+.4f} /
  {nt['validation_delta']['macro_f1']:+.4f} / {nt['validation_delta']['high_recall']:+.4f}); paired t-test p = {nt['t_test_balanced_accuracy_p']:.3f} raw, {holm_t['no_therapy']:.3f} Holm-adjusted.
- **Detection of low-therapy High patients:** true-High patients with ≤ 2 sessions are predicted High {lo['v2']['predicted_high']} of
  {lo['v2']['rows']} times by v2 and {lo['no_therapy']['predicted_high']} of {lo['no_therapy']['rows']} without Therapy; the review flag catches
  {lo['v2']['flagged']} of {lo['v2']['rows']} (v2, 0.025) vs {lo['no_therapy']['flagged_own_threshold']} of {lo['no_therapy']['rows']} (own threshold {td['own_threshold']}),
  with {ft['v2_at_0.025']:,} (v2) vs {ft['no_therapy_own_threshold']:,} (Therapy removed) patients flagged overall. Without Therapy, the top High drivers are {top3}.
- **Reverse-causality risk of keeping it:** in this dataset therapy count most likely reflects severity (more severe patients
  attend more sessions), so a new help-seeker with high stress but no therapy history is under-called by v2.
- **Trade-off:** {trade}
- **What this means:** removing Therapy does not fix the low-therapy gap ({lo['no_therapy']['predicted_high']}/{n_low} predicted High,
  {lo['no_therapy']['flagged_own_threshold']}/{n_low} flagged), so the gap reflects the data, not the model's use of the feature; mitigation is
  psychologist review and the documented limitation (model card Known Limitations item 16).
- Very likely synthetic data; small low-therapy High sample ({lo['v2']['rows']} patients).

Libraries: {', '.join(f'{k} {v}' for k, v in r['library_versions'].items())}.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    import sys

    if "--report-only" in sys.argv:  # rebuild the Markdown from the saved JSON without refitting
        write_markdown(json.loads(REPORT_JSON.read_text(encoding="utf-8")))
    else:
        main()
