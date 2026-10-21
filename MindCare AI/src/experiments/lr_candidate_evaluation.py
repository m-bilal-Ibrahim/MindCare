"""Logistic regression as a candidate to replace the served v2 XGBoost, held to the standards v2 was held to.

Train + validation rows only (the test set is never loaded). No served file or threshold is changed; the served
v2 is reproduced by retraining on the training split and guarded against its documented numbers.

1. Nested 5-fold CV for LR, same outer folds and procedure as src/evaluation/nested_cv_12feature_xgb.py: inside
   each outer training fold, GridSearchCV (inner cv=5, balanced accuracy) over C and class_weight, then the review
   threshold from the chosen configuration's inner out-of-fold P(High) (highest threshold flagging >= 158/165 of
   High). v2's figures are read from reports/nested_cv_11feature_v2_xgb.json (same folds, same metrics).
2. The checks behind the XGBoost choice, for LR and v2:
   - caffeine shortcut, both forms from src/explainability/shap_v2.py: observed (true High with caffeine <= 200
     mg/day: predicted High / flagged; validation and out-of-fold) and counterfactual (validation true High with
     caffeine set to 0 / 100 / 200);
   - age artifact: validation true-High rows under 50 with Age set to 49 / 50 / 55, mean P(High);
   - Occupation fairness (Scientist vs other occupations): model High recall and flag catch rate;
   - low-therapy (<= 2 sessions) and low-caffeine (<= 200 mg/day) true-High subgroups, out-of-fold.
3. Feature effects: LR's coefficients for High on standardised inputs vs v2's out-of-fold SHAP ranking
   (reports/shap_v2.json), and the direction check for Sleep, Caffeine, Physical Activity and Diet.

Thresholds. v2 uses the served 0.025 everywhere. LR has no served threshold, so it gets the same rule that
produced 0.025: on the validation split, the highest threshold flagging >= 158/165 true High; out-of-fold, the
highest threshold catching at least v2's out-of-fold share at 0.025.

LR candidate settings for sections 2-3: GridSearchCV on the 7,700 training rows (cv=5, balanced accuracy), as
src/models/tune_models_12feature.py tuned v2 on the training split.

Run from MindCare AI/: python -m src.experiments.lr_candidate_evaluation   (--report-only rebuilds the Markdown)
"""

from __future__ import annotations

import json
import math
import sys

import numpy as np
import pandas as pd
import sklearn
from scipy.stats import fisher_exact, spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level
from src.evaluation.nested_cv_12feature_xgb import METRICS, TARGET_COVERAGE, coverage_threshold, score
from src.experiments.ablation_study import (DATA_PATH, FOLDS, HIGH, REVIEW_THRESHOLD, ROOT, SEED, SPLITS_PATH,
                                            TUNING_12, V2_CATEGORICAL, V2_NUMERIC)
from src.experiments.sota_baselines import pipeline

REPORT_JSON = ROOT / "reports" / "lr_candidate_evaluation.json"
REPORT_MD = ROOT / "reports" / "lr_candidate_evaluation.md"
V2_NESTED_JSON = ROOT / "reports" / "nested_cv_11feature_v2_xgb.json"
SHAP_V2_JSON = ROOT / "reports" / "shap_v2.json"
FEATURES = V2_NUMERIC + V2_CATEGORICAL
CAFFEINE, THERAPY, AGE = "Caffeine Intake (mg/day)", "Therapy Sessions (per month)", "Age"
CAFFEINE_LIMIT, CAFFEINE_COUNTERFACTUALS, AGES = 200, (0, 100, 200), (49, 50, 55)
MODIFIABLE = {"Sleep Hours": -1, "Caffeine Intake (mg/day)": +1, "Physical Activity (hrs/week)": -1, "Diet Quality (1-10)": -1}
LR_GRID = {"model__C": [0.001, 0.01, 0.1, 1, 10, 100], "model__class_weight": [None, "balanced"]}
INNER_CV = 5
# v2 guards (documented elsewhere; recomputed here, must match)
GUARD_VAL = {"balanced_accuracy": 0.8055, "flagged": 411, "flagged_true_high": 158, "true_high": 165}
GUARD_LOW_THERAPY = {"rows": 54, "predicted_high": 0, "flagged": 33}  # reports/robustness_v2.md
GUARD_LOW_CAFFEINE = {"rows": 23, "predicted_high": 0, "flagged": 12}  # reports/shap_v2.md


def lr() -> LogisticRegression:
    return LogisticRegression(max_iter=5000)


def v2_model(params: dict) -> XGBClassifier:
    return XGBClassifier(**params, objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)


def tune_lr(x: pd.DataFrame, y: np.ndarray) -> GridSearchCV:
    return GridSearchCV(pipeline(lr()), LR_GRID, scoring="balanced_accuracy", cv=INNER_CV, n_jobs=-1, refit=True).fit(x, y)


def share_threshold(p_high: np.ndarray, is_high: np.ndarray, share: float) -> float:
    """Highest threshold whose catch share of true High is >= share (rounded down to 4 decimals)."""
    hp = np.sort(p_high[is_high])
    t = float(np.floor(hp[int(np.floor((1 - share) * len(hp) + 1e-9))] * 1e4) / 1e4)
    assert (p_high[is_high] >= t).mean() >= share
    return t


def group(mask_rows: np.ndarray, y: np.ndarray, p: np.ndarray, t: float) -> dict:
    m = mask_rows & (y == HIGH)
    return {"rows": int(m.sum()), "predicted_high": int((p[m].argmax(1) == HIGH).sum()), "flagged": int((p[m, HIGH] >= t).sum())}


def nested_lr(x: pd.DataFrame, y: np.ndarray, eligible: np.ndarray) -> list[dict]:
    folds = []
    for k, (tr, te) in enumerate(StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(x, y), start=1):
        search = tune_lr(x.iloc[tr], y[tr])
        oof = cross_val_predict(pipeline(lr()).set_params(**search.best_params_), x.iloc[tr], y[tr], cv=INNER_CV,
                                method="predict_proba")
        t = coverage_threshold(oof[:, HIGH], y[tr] == HIGH)
        prob = search.best_estimator_.predict_proba(x.iloc[te])
        e = eligible[te]
        folds.append({"fold": k, "params": {kk.removeprefix("model__"): v for kk, v in search.best_params_.items()},
                      "inner_cv": float(search.best_score_), "threshold": t,
                      "all": score(y[te], prob, t), "eligible": score(y[te][e], prob[e], t)})
        print(f"nested fold {k}: {folds[-1]['params']}, threshold {t:.4f}, "
              f"bal_acc {folds[-1]['all']['balanced_accuracy']:.4f}", flush=True)
    return folds


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as s:
        tr_idx, val_idx = s["train_original_idx"], s["val_original_idx"]
    train, val = raw.iloc[tr_idx].reset_index(drop=True), raw.iloc[val_idx].reset_index(drop=True)
    df = pd.concat([train, val], ignore_index=True)  # no test rows
    y_tr, y_val = (bin_anxiety_level(f["Anxiety Level (1-10)"].to_numpy()) for f in (train, val))
    y = np.concatenate([y_tr, y_val])
    x = df[FEATURES]
    params = json.loads(TUNING_12.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]

    # ---- 1. Nested CV ----
    nested = nested_lr(x, y, (df[AGE] <= 49).to_numpy())
    v2_nested = json.loads(V2_NESTED_JSON.read_text(encoding="utf-8"))["folds"]

    # ---- Models on the training split (validation views) ----
    v2_val = pipeline(v2_model(params)).fit(train[FEATURES], y_tr)
    search = tune_lr(train[FEATURES], y_tr)
    lr_params = {k.removeprefix("model__"): v for k, v in search.best_params_.items()}
    lr_val = search.best_estimator_
    p_v2, p_lr = v2_val.predict_proba(val[FEATURES]), lr_val.predict_proba(val[FEATURES])
    g = {"balanced_accuracy": round(float(balanced_accuracy_score(y_val, p_v2.argmax(1))), 4),
         "flagged": int((p_v2[:, HIGH] >= REVIEW_THRESHOLD).sum()),
         "flagged_true_high": int(((p_v2[:, HIGH] >= REVIEW_THRESHOLD) & (y_val == HIGH)).sum()), "true_high": int((y_val == HIGH).sum())}
    if g != GUARD_VAL:
        raise SystemExit(f"STOP: v2 retrained on the training split does not reproduce the served numbers: {g}")
    is_h_val = y_val == HIGH
    needed = math.ceil(TARGET_COVERAGE * is_h_val.sum())
    t_lr_val = float(np.sort(p_lr[is_h_val, HIGH])[::-1][needed - 1])
    thr_val = {"v2": REVIEW_THRESHOLD, "lr": t_lr_val}
    p_val = {"v2": p_v2, "lr": p_lr}
    val_scores = {k: score(y_val, p, thr_val[k]) for k, p in p_val.items()}

    # ---- Out-of-fold on the same folds (LR with the training-split settings) ----
    oof = {k: np.zeros((len(df), 3)) for k in ("v2", "lr")}
    for tr, te in StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y):
        oof["v2"][te] = pipeline(v2_model(params)).fit(x.iloc[tr], y[tr]).predict_proba(x.iloc[te])
        oof["lr"][te] = pipeline(lr()).set_params(**search.best_params_).fit(x.iloc[tr], y[tr]).predict_proba(x.iloc[te])
    is_h = y == HIGH
    v2_share = float((oof["v2"][is_h, HIGH] >= REVIEW_THRESHOLD).mean())
    thr_oof = {"v2": REVIEW_THRESHOLD, "lr": share_threshold(oof["lr"][:, HIGH], is_h, v2_share)}

    # ---- 2. Checks ----
    caf, ther = df[CAFFEINE].to_numpy(), df[THERAPY].to_numpy()
    low_caf = {k: group(caf <= CAFFEINE_LIMIT, y, oof[k], thr_oof[k]) for k in oof}
    low_ther = {k: group(ther <= 2, y, oof[k], thr_oof[k]) for k in oof}
    if low_caf["v2"] != GUARD_LOW_CAFFEINE or low_ther["v2"] != GUARD_LOW_THERAPY:
        raise SystemExit(f"STOP: v2 subgroup numbers differ from shap_v2/robustness_v2: {low_caf['v2']} {low_ther['v2']}")
    caf_val_obs = {k: group(val[CAFFEINE].to_numpy() <= CAFFEINE_LIMIT, y_val, p_val[k], thr_val[k]) for k in p_val}
    high_val = val[is_h_val]
    models_val = {"v2": v2_val, "lr": lr_val}
    counterfactual = {}
    for mg in CAFFEINE_COUNTERFACTUALS:
        cf = high_val.copy()
        cf[CAFFEINE] = mg
        counterfactual[str(mg)] = {}
        for k, m in models_val.items():
            p = m.predict_proba(cf[FEATURES])
            counterfactual[str(mg)][k] = {"predicted_high": int((p.argmax(1) == HIGH).sum()),
                                          "flagged": int((p[:, HIGH] >= thr_val[k]).sum()), "of": int(len(cf))}
    shap_cf = json.loads(SHAP_V2_JSON.read_text(encoding="utf-8"))["caffeine_shortcut"]["counterfactual_validation_true_high"]
    if any(counterfactual[m]["v2"]["predicted_high"] != shap_cf[m]["predicted_high"]
           or counterfactual[m]["v2"]["flagged"] != shap_cf[m]["flagged_at_0.025"] for m in shap_cf):
        raise SystemExit("STOP: v2 caffeine counterfactual differs from reports/shap_v2.json")

    under50 = high_val[high_val[AGE] < 50]
    age = {}
    for a in AGES:
        frame = under50.copy()
        frame[AGE] = a
        age[str(a)] = {k: {"mean_p_high": float(m.predict_proba(frame[FEATURES])[:, HIGH].mean()),
                           "predicted_high": int((m.predict(frame[FEATURES]) == HIGH).sum())} for k, m in models_val.items()}
    age_rows = int(len(under50))

    sci_oof, sci_val = (df["Occupation"] == "Scientist").to_numpy(), (val["Occupation"] == "Scientist").to_numpy()
    fairness = {}
    for view, mask, yy, pp, tt in (("oof", sci_oof, y, oof, thr_oof), ("validation", sci_val, y_val, p_val, thr_val)):
        fairness[view] = {}
        for k in pp:
            s, o = group(mask, yy, pp[k], tt[k]), group(~mask, yy, pp[k], tt[k])
            fairness[view][k] = {"scientist": s, "other": o,
                                 "recall_gap": s["predicted_high"] / s["rows"] - o["predicted_high"] / o["rows"],
                                 "catch_gap": s["flagged"] / s["rows"] - o["flagged"] / o["rows"]}

    # ---- 3. Feature effects ----
    lr_full = pipeline(lr()).set_params(**search.best_params_).fit(x, y)  # all 9,350 rows, training-split settings
    names = list(lr_full.named_steps["pre"].get_feature_names_out())
    coef = lr_full.named_steps["model"].coef_[HIGH]
    coefs = {}
    for f in FEATURES:
        cols = [j for j, n in enumerate(names) if n.split("__", 1)[1] == f or n.split("__", 1)[1].startswith(f + "_")]
        coefs[f] = ({"coef": float(coef[cols[0]])} if f in V2_NUMERIC
                    else {"range": float(coef[cols].max() - coef[cols].min()),
                          "levels": {names[j].split("__", 1)[1].removeprefix(f + "_"): float(coef[j]) for j in cols}})
    eff = {f: abs(v["coef"]) if "coef" in v else v["range"] for f, v in coefs.items()}
    lr_rank = [f for f, _ in sorted(eff.items(), key=lambda kv: -kv[1])]
    shap = json.loads(SHAP_V2_JSON.read_text(encoding="utf-8"))
    shap_rank = [r["feature"] for r in shap["ranking_high"]["oof"]]
    rho = float(spearmanr([lr_rank.index(f) for f in FEATURES], [shap_rank.index(f) for f in FEATURES]).statistic)
    direction = {f: {"expected": "higher -> less risk" if sgn < 0 else "higher -> more risk",
                     "lr_coef": coefs[f]["coef"], "lr_matches": bool(np.sign(coefs[f]["coef"]) == sgn),
                     "v2_matches": bool(shap["direction_check"][f]["matches"]),
                     "v2_oof_spearman": float(shap["direction_check"][f]["oof"]["spearman"])} for f, sgn in MODIFIABLE.items()}

    result = {
        "rows_cv": len(df), "rows_validation": len(val), "seed": SEED, "test_set_used": False,
        "lr_grid": {k.removeprefix("model__"): [str(v) for v in vs] for k, vs in LR_GRID.items()},
        "lr_training_split_params": {k: (v if v is not None else "none") for k, v in lr_params.items()},
        "lr_training_split_inner_cv": float(search.best_score_),
        "nested": {"lr": nested, "v2": [{k: f[k] for k in ("fold", "threshold", "all", "eligible")} for f in v2_nested]},
        "thresholds": {"validation": thr_val, "oof": thr_oof, "v2_oof_catch_share": v2_share},
        "validation_scores": val_scores,
        "caffeine_observed": {"validation": caf_val_obs, "oof": low_caf}, "caffeine_counterfactual": counterfactual,
        "age_artifact": {"rows": age_rows, "by_age": age},
        "fairness_scientist": fairness, "low_therapy_oof": low_ther,
        "lr_coefficients_high": coefs, "lr_rank": lr_rank, "v2_shap_rank_oof": shap_rank, "rank_spearman": rho,
        "direction": direction, "guards": {"validation": g, "low_caffeine": low_caf["v2"], "low_therapy": low_ther["v2"]},
        "library_versions": {"scikit-learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
    }
    result["scientist_stats"] = scientist_stats(result)
    REPORT_JSON.write_text(json.dumps(result, indent=2, default=float) + "\n", encoding="utf-8", newline="\n")
    write_markdown(result)
    print("guards passed; wrote", REPORT_MD.relative_to(ROOT), "and", REPORT_JSON.relative_to(ROOT))


BOOTSTRAP_RESAMPLES = 2000


def scientist_stats(r: dict) -> dict:
    """Out-of-fold Scientist - other model High recall gap: bootstrap 95% CI and Fisher exact test, per model.

    Each patient's result is 1 (predicted High) or 0, so resampling patients within each group (stratified bootstrap,
    group sizes fixed) needs only the stored counts. Percentile CI, seed 42; Fisher exact is two-sided on the 2x2 table.
    """
    out = {}
    for k in ("v2", "lr"):
        s, o = (r["fairness_scientist"]["oof"][k][g] for g in ("scientist", "other"))
        rng = np.random.default_rng(SEED)
        a = np.r_[np.ones(s["predicted_high"]), np.zeros(s["rows"] - s["predicted_high"])]
        b = np.r_[np.ones(o["predicted_high"]), np.zeros(o["rows"] - o["predicted_high"])]
        gaps = np.array([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(BOOTSTRAP_RESAMPLES)])
        odds, p = fisher_exact([[s["predicted_high"], s["rows"] - s["predicted_high"]],
                                [o["predicted_high"], o["rows"] - o["predicted_high"]]])
        out[k] = {"gap": a.mean() - b.mean(), "ci95": [float(np.percentile(gaps, 2.5)), float(np.percentile(gaps, 97.5))],
                  "fisher_p": float(p), "odds_ratio": float(odds), "scientist": s, "other": o}
    return {"resamples": BOOTSTRAP_RESAMPLES, "seed": SEED, "models": out}


def scientist_reading(ss: dict) -> str:
    parts = []
    for lab, k in (("v2", "v2"), ("LR", "lr")):
        m = ss["models"][k]
        excl = m["ci95"][1] < 0 or m["ci95"][0] > 0
        parts.append(f"{lab}: the CI {'excludes' if excl else 'includes'} zero and Fisher p is {m['fisher_p']:.3g} "
                     f"({'below' if m['fisher_p'] < 0.05 else 'not below'} 0.05)")
    n_occ = 13
    bonf = "; ".join(f"{lab} {min(1.0, ss['models'][k]['fisher_p'] * n_occ):.3g}" for lab, k in (("v2", "v2"), ("LR", "lr")))
    return ("**Reading.** " + "; ".join(parts) + ". Scientist was singled out because it was flagged earlier; if any of the "
            f"{n_occ} occupations could have been, a Bonferroni-adjusted p (× {n_occ}) is: {bonf}. The two models' tests share "
            "patients. Out-of-fold predictions come from five models, not one. The data "
            "are very likely synthetic, and occupation shows no link to Stress Level in this dataset (CLAUDE.md). So this "
            "result bears on whether the gap is sampling noise; it does not explain the gap.")


LABELS = {"accuracy": "Accuracy", "balanced_accuracy": "Balanced accuracy", "macro_f1": "Macro-F1",
          "recall_Low": "Recall Low", "recall_Medium": "Recall Medium", "recall_High": "Model High recall",
          "precision_High": "Precision High", "flag_catch_rate": "Review-flag catch rate", "flag_volume": "Flag volume",
          "brier_Low": "Brier Low", "brier_Medium": "Brier Medium", "brier_High": "Brier High"}


def write_markdown(r: dict) -> None:
    ms = lambda folds, scope, m: (np.mean([f[scope][m] for f in folds]), np.std([f[scope][m] for f in folds]))
    nl, nv = r["nested"]["lr"], r["nested"]["v2"]
    nest = {}
    for scope, title in (("all", "All ages"), ("eligible", "Ages 18-49")):
        rows = [f"**{title}**", "", "| Metric | v2 XGBoost | Logistic regression | LR − v2 |", "|---|---|---|---|"]
        for m in METRICS:
            a, b = ms(nv, scope, m), ms(nl, scope, m)
            rows.append(f"| {LABELS[m]} | {a[0]:.4f} ± {a[1]:.4f} | {b[0]:.4f} ± {b[1]:.4f} | {b[0] - a[0]:+.4f} |")
        nest[scope] = "\n".join(rows)
    fold_rows = ["| Fold | LR C | LR class_weight | LR threshold | v2 threshold |", "|---|---|---|---|---|"]
    fold_rows += [f"| {a['fold']} | {a['params']['C']} | {a['params']['class_weight'] or 'none'} | {a['threshold']:.4f} | {b['threshold']:.4f} |"
                  for a, b in zip(nl, nv)]
    th, vs = r["thresholds"], r["validation_scores"]
    co, cf, ag, fa = r["caffeine_observed"], r["caffeine_counterfactual"], r["age_artifact"], r["fairness_scientist"]
    lt = r["low_therapy_oof"]
    frac = lambda d: f"{d['predicted_high']}/{d['rows']} predicted High, {d['flagged']}/{d['rows']} flagged"
    pct = lambda n, d: f"{n / d:.1%}" if d else "—"

    side = ["| Check | v2 XGBoost | Logistic regression |", "|---|---|---|"]
    a, b = ms(nv, "all", "balanced_accuracy"), ms(nl, "all", "balanced_accuracy")
    side.append(f"| Nested CV balanced accuracy (all ages) | {a[0]:.4f} ± {a[1]:.4f} | {b[0]:.4f} ± {b[1]:.4f} |")
    a, b = ms(nv, "all", "recall_High"), ms(nl, "all", "recall_High")
    side.append(f"| Nested CV model High recall | {a[0]:.4f} ± {a[1]:.4f} | {b[0]:.4f} ± {b[1]:.4f} |")
    a, b = ms(nv, "all", "flag_catch_rate"), ms(nl, "all", "flag_catch_rate")
    c, d = ms(nv, "all", "flag_volume"), ms(nl, "all", "flag_volume")
    side.append(f"| Nested CV flag catch rate / flag volume | {a[0]:.4f} / {c[0]:.4f} | {b[0]:.4f} / {d[0]:.4f} |")
    side.append(f"| Caffeine ≤ 200, true High, out-of-fold (n={co['oof']['v2']['rows']}) | {frac(co['oof']['v2'])} | {frac(co['oof']['lr'])} |")
    side.append(f"| Caffeine set to 0, validation true High (of {cf['0']['v2']['of']}) | {cf['0']['v2']['predicted_high']} predicted High, {cf['0']['v2']['flagged']} flagged "
                f"| {cf['0']['lr']['predicted_high']} predicted High, {cf['0']['lr']['flagged']} flagged |")
    by = ag["by_age"]
    side.append(f"| Mean P(High), true High under 50 set to age 49 → 50 → 55 (n={ag['rows']}) | "
                + " → ".join(f"{by[x]['v2']['mean_p_high']:.3f}" for x in ("49", "50", "55")) + " | "
                + " → ".join(f"{by[x]['lr']['mean_p_high']:.3f}" for x in ("49", "50", "55")) + " |")
    fo = fa["oof"]
    side.append(f"| Scientist − other: model High recall gap, out-of-fold (Scientist n={fo['v2']['scientist']['rows']}) | "
                f"{fo['v2']['recall_gap']:+.3f} | {fo['lr']['recall_gap']:+.3f} |")
    side.append(f"| Scientist − other: flag catch gap, out-of-fold | {fo['v2']['catch_gap']:+.3f} | {fo['lr']['catch_gap']:+.3f} |")
    side.append(f"| Therapy ≤ 2, true High, out-of-fold (n={lt['v2']['rows']}) | {frac(lt['v2'])} | {frac(lt['lr'])} |")
    dr = r["direction"]
    side.append(f"| Direction check (Sleep, Caffeine, Activity, Diet) matches clinical expectation | "
                f"{sum(v['v2_matches'] for v in dr.values())}/4 | {sum(v['lr_matches'] for v in dr.values())}/4 |")

    caf_tbl = ["| View | Model | True High with caffeine ≤ 200 | Predicted High | Flagged |", "|---|---|---|---|---|"]
    for view in ("validation", "oof"):
        for k, lab in (("v2", "v2"), ("lr", "LR")):
            o = co[view][k]
            caf_tbl.append(f"| {'Validation' if view == 'validation' else 'Out-of-fold'} | {lab} | {o['rows']} | {o['predicted_high']} | {o['flagged']} |")
    cf_tbl = ["| Caffeine set to | v2: predicted High / flagged | LR: predicted High / flagged |", "|---|---|---|"]
    cf_tbl += [f"| {mg} mg/day | {cf[mg]['v2']['predicted_high']} / {cf[mg]['v2']['flagged']} of {cf[mg]['v2']['of']} | "
               f"{cf[mg]['lr']['predicted_high']} / {cf[mg]['lr']['flagged']} of {cf[mg]['lr']['of']} |" for mg in cf]
    age_tbl = ["| Age set to | v2: mean P(High) | v2: predicted High | LR: mean P(High) | LR: predicted High |", "|---|---|---|---|---|"]
    age_tbl += [f"| {x} | {by[x]['v2']['mean_p_high']:.3f} | {by[x]['v2']['predicted_high']} | {by[x]['lr']['mean_p_high']:.3f} | {by[x]['lr']['predicted_high']} |" for x in by]
    fair_tbl = ["| View | Model | Scientist: High recall / catch | Other: High recall / catch | Gap: recall / catch |", "|---|---|---|---|---|"]
    for view in ("validation", "oof"):
        for k, lab in (("v2", "v2"), ("lr", "LR")):
            s, o = fa[view][k]["scientist"], fa[view][k]["other"]
            fair_tbl.append(f"| {'Validation' if view == 'validation' else 'Out-of-fold'} | {lab} | "
                            f"{s['predicted_high']}/{s['rows']} ({pct(s['predicted_high'], s['rows'])}) / {s['flagged']}/{s['rows']} ({pct(s['flagged'], s['rows'])}) | "
                            f"{o['predicted_high']}/{o['rows']} ({pct(o['predicted_high'], o['rows'])}) / {o['flagged']}/{o['rows']} ({pct(o['flagged'], o['rows'])}) | "
                            f"{fa[view][k]['recall_gap']:+.3f} / {fa[view][k]['catch_gap']:+.3f} |")
    sub_tbl = ["| Out-of-fold true High | Rows | v2: model High recall | v2: flag catch (0.025) | LR: model High recall | LR: flag catch |", "|---|---|---|---|---|---|"]
    for lab, d in (("Therapy ≤ 2 sessions", lt), ("Caffeine ≤ 200 mg/day", co["oof"])):
        v, l = d["v2"], d["lr"]
        sub_tbl.append(f"| {lab} | {v['rows']} | {v['predicted_high']}/{v['rows']} ({pct(v['predicted_high'], v['rows'])}) | {v['flagged']}/{v['rows']} ({pct(v['flagged'], v['rows'])}) | "
                       f"{l['predicted_high']}/{l['rows']} ({pct(l['predicted_high'], l['rows'])}) | {l['flagged']}/{l['rows']} ({pct(l['flagged'], l['rows'])}) |")
    cfx = r["lr_coefficients_high"]
    eff_tbl = ["| Feature | LR coefficient for High (per train std; categorical = spread of levels) | LR rank | v2 SHAP rank (High, out-of-fold) |", "|---|---|---|---|"]
    for f in r["lr_rank"]:
        v = cfx[f]
        val_s = f"{v['coef']:+.3f}" if "coef" in v else f"range {v['range']:.3f}"
        eff_tbl.append(f"| {f} | {val_s} | {r['lr_rank'].index(f) + 1} | {r['v2_shap_rank_oof'].index(f) + 1} |")
    dir_tbl = ["| Feature | Clinical expectation | LR coefficient | LR matches | v2 (SHAP Spearman, out-of-fold) | v2 matches |", "|---|---|---|---|---|---|"]
    dir_tbl += [f"| {f} | {v['expected']} | {v['lr_coef']:+.3f} | {'yes' if v['lr_matches'] else '**no**'} | {v['v2_oof_spearman']:+.3f} | {'yes' if v['v2_matches'] else '**no**'} |"
                for f, v in dr.items()]
    p = r["lr_training_split_params"]
    ss = r["scientist_stats"]
    sci_rows = []
    for lab, k in (("v2", "v2"), ("LR", "lr")):
        m = ss["models"][k]
        sci_rows.append(f"| {lab} | {m['scientist']['predicted_high']}/{m['scientist']['rows']} | {m['other']['predicted_high']}/{m['other']['rows']} "
                        f"| {m['gap']:+.3f} | {m['ci95'][0]:+.3f} to {m['ci95'][1]:+.3f} | {m['fisher_p']:.3g} | {m['odds_ratio']:.2f} |")
    num_lr = [f for f in r["lr_rank"] if f in V2_NUMERIC]
    num_v2 = [f for f in r["v2_shap_rank_oof"] if f in V2_NUMERIC]
    rho_num = float(spearmanr([num_lr.index(f) for f in V2_NUMERIC], [num_v2.index(f) for f in V2_NUMERIC]).statistic)
    caf_sens = {k: cf["200"][k]["predicted_high"] - cf["0"][k]["predicted_high"] for k in ("v2", "lr")}

    REPORT_MD.write_text(f"""# Logistic regression as a candidate to replace v2

Script: `src/experiments/lr_candidate_evaluation.py` (`reports/lr_candidate_evaluation.json`). **The test set was not used; no
served file or threshold changed.** Seed 42. {r['rows_cv']:,} train + validation rows; the same 5 outer folds as the v2 nested CV
and the ablation study. Very likely synthetic data, and the target is a self-rated social anxiety level, so none of this is
clinical validation.

**Guards (all passed):** v2 retrained on the training split reproduces the served validation numbers
({r['guards']['validation']['balanced_accuracy']}, {r['guards']['validation']['flagged']} flagged, {r['guards']['validation']['flagged_true_high']}/{r['guards']['validation']['true_high']} true High);
v2's caffeine counterfactual matches `reports/shap_v2.json`; v2's low-caffeine (23 / 0 / 12) and low-therapy (54 / 0 / 33)
out-of-fold numbers match `reports/shap_v2.md` and `reports/robustness_v2.md`.

**Thresholds.** v2 uses the served 0.025 throughout. LR has no served threshold, so it gets the rule that produced 0.025: the
highest threshold flagging at least 158/165 true High on the validation split (**{th['validation']['lr']:.4f}**), and out-of-fold
the highest threshold catching at least v2's out-of-fold share at 0.025 ({th['v2_oof_catch_share']:.1%}): **{th['oof']['lr']:.4f}**.
In nested CV each fold derives its own threshold for both models.

**LR settings for sections 2-3:** tuned on the 7,700 training rows (GridSearchCV, cv=5, balanced accuracy; C in
{r['lr_grid']['C']}, class_weight none/balanced): **C = {p['C']}, class_weight = {p['class_weight']}** (inner CV {r['lr_training_split_inner_cv']:.4f}).

## Side by side

{chr(10).join(side)}

## 1. Nested 5-fold CV (same procedure and metrics as `reports/nested_cv_11feature_v2_xgb.md`)

LR: inside each outer training fold, GridSearchCV over C and class_weight (inner cv=5, balanced accuracy), then the review
threshold from the chosen configuration's inner out-of-fold P(High) (highest flagging ≥ 158/165). v2's numbers are read from
`reports/nested_cv_11feature_v2_xgb.json` (its own tuning: 40 XGBoost configurations per fold). Mean ± std over 5 folds
(population std, as in that report). Flag rows use each fold's own threshold.

{nest['all']}

{nest['eligible']}

{chr(10).join(fold_rows)}

## 2. The checks behind the XGBoost choice

**Caffeine shortcut, observed** (true-High patients with caffeine ≤ 200 mg/day):

{chr(10).join(caf_tbl)}

**Caffeine shortcut, counterfactual** (every true-High validation patient with caffeine set to a fixed value; models fitted on
the training split):

{chr(10).join(cf_tbl)}

**Age artifact** ({ag['rows']} true-High validation patients under 50, only Age changed; models fitted on the training split):

{chr(10).join(age_tbl)}

**Occupation fairness: Scientist vs all other occupations** (true High only):

{chr(10).join(fair_tbl)}

Scientist true-High counts are small, so a gap of a few points is one or two patients.

**Is the out-of-fold model High recall gap real?** Bootstrap 95% CI ({ss['resamples']:,} resamples, seed {ss['seed']},
patients resampled within each group) and a two-sided Fisher exact test on predicted-High vs not, Scientist vs other:

| Model | Scientist High recall | Other High recall | Gap | Bootstrap 95% CI | Fisher exact p | Odds ratio |
|---|---|---|---|---|---|---|
{chr(10).join(sci_rows)}

{scientist_reading(ss)}

**Under-detected subgroups** (out-of-fold):

{chr(10).join(sub_tbl)}

## 3. Feature effects

LR coefficients are for the High class on the model's own inputs: numeric features standardised (per training std), so a
coefficient is the change in the High logit per one std. For Occupation and Family History the figure is the spread between
their one-hot levels' coefficients, which is not on the same scale. LR fitted on all {r['rows_cv']:,} rows with the
training-split settings. v2's ranking is mean |SHAP| for High, out-of-fold (`reports/shap_v2.json`). Spearman correlation
of the two rankings: **{r['rank_spearman']:.2f}** over all 11 features, **{rho_num:.2f}** over the 9 numeric features only.
The overall figure is pulled down by Occupation, whose spread over 13 levels is not comparable to a per-std coefficient.

{chr(10).join(eff_tbl)}

**Direction check** (LR: sign of the coefficient; v2: sign of the Spearman correlation between the feature and its SHAP
value for High, from `reports/shap_v2.json`):

{chr(10).join(dir_tbl)}

A coefficient's sign is the model's association on this dataset, not evidence that changing the input changes anxiety.
LR's effect is the same direction at every value by construction; v2's can bend.

## Decision for supervisor

The served model is unchanged; this report does not choose. What the numbers above bear on:

- **Accuracy and coverage.** Compare the nested-CV rows in section 1. Both pipelines were re-tuned and re-thresholded inside
  every fold, so these are the like-for-like estimates.
- **Known safety gaps.** The low-caffeine and low-therapy rows show whether LR closes, keeps or widens the gaps already
  listed as model card limitations 15 and 16. The age table shows how strongly each model reacts to the 49/50 boundary.
  The supported age range stays 18-49 either way, because it is a data-coverage limit.
- **Caffeine dependence.** Moving every validation true-High patient from 0 to 200 mg/day of caffeine changes the
  predicted-High count by {caf_sens['v2']:+d} for v2 and {caf_sens['lr']:+d} for LR. The 2026-09-28 switch away from Random
  Forest was partly about this sensitivity, because the API only estimates caffeine from drink counts.
- **Scientist gap, recorded but not resolved here.** Out-of-fold, with {fo['v2']['scientist']['rows']} Scientist true-High
  patients, both models show a model High recall gap ({fo['v2']['recall_gap']:+.3f} for v2, {fo['lr']['recall_gap']:+.3f} for LR). CLAUDE.md
  treats the Scientist flag as likely noise, based on 16 validation patients. This larger sample is the cross-validated check
  that note asked for. The flag catch gap is smaller ({fo['v2']['catch_gap']:+.3f} / {fo['lr']['catch_gap']:+.3f}). No significance test was run.
- **Explainability.** LR's effects are one fixed coefficient per feature. v2's depend on the patient and need SHAP. Section 3
  shows whether the two models rank the same features as important.
- **Robustness and workload** (from `reports/sota_comparison.md`, "Why XGBoost if logistic regression ties?"): LR lost less
  balanced accuracy under noise and flagged fewer patients at matched coverage. v2 was better calibrated for High and Medium.
- **Cost of switching.** A switch would need a new served model, preprocessor and threshold, re-running the deployment
  manifest step (`docs/deployment.md`), and updating the model card, API docs and tests. The 0.025 threshold would not carry
  over. Calibration, SHAP-based explanations and fairness for the served model would need redoing.
- **Not covered:** the same caveats as v2's nested CV (feature set, label bins, age range and coverage target were decided
  on these rows), very likely synthetic data, and a self-rated social-anxiety target.

Libraries: {', '.join(f'{k} {v}' for k, v in r['library_versions'].items())}.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    if "--report-only" in sys.argv:  # recomputes the count-based Scientist statistics, no refitting
        saved = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        saved["scientist_stats"] = scientist_stats(saved)
        REPORT_JSON.write_text(json.dumps(saved, indent=2, default=float) + "\n", encoding="utf-8", newline="\n")
        write_markdown(saved)
    else:
        main()
