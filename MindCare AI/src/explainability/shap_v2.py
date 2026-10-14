"""Phase 17 (SHAP) for the served 11-feature v2 XGBoost, 3-class Anxiety Level target.

Validation/CV only: the 1,650 test rows are never loaded (the 3-class test set is spent). Changes no
served file. Adapted from shap_analysis_3class.py (the earlier Random Forest analysis).

1. Guard: the loaded served files must reproduce v2's documented validation numbers (balanced
   accuracy 0.8055; 411 flagged and 158/165 true High flagged at P(High) >= 0.025). Otherwise stop.
2. SHAP via XGBoost's exact TreeSHAP (`pred_contribs=True`), checked for additivity: per row and
   class, contributions + bias = the raw margin. Units are the High-class margin (softmax logit).
   Computed on the validation split (served files) and out-of-fold over the 9,350 train + validation
   rows (5-fold stratified on the 3-class label, shuffled, seed 42, v2 params, preprocessing fitted
   inside each fold). One-hot columns (Occupation x13, Family History x2) are added back into one
   feature by summing each row's signed contributions (exact), not by summing mean |SHAP|.
3. Ranking of the 11 features by mean |SHAP| for the High class, plus an all-class view (mean |SHAP|
   averaged over Low/Medium/High) that matches how the earlier rankings were computed, compared with
   reports/shap_full_ranking_3class.md (17-feature Random Forest) and
   reports/model_comparison_12feature.md (12-feature Random Forest and XGBoost).
4. Stress Level dominance = its share of total mean |SHAP|.
5. Caffeine shortcut, two forms: (a) observed - true-High rows whose caffeine is <= 200 mg/day, how
   many are predicted High; (b) counterfactual - every true-High validation row with caffeine set to
   0 / 100 / 200 mg/day, how many are still predicted High (the form behind the documented "RF 0 of
   165 vs XGBoost 127-129", whose original script is not in the repo).
6. The true-High validation rows predicted Medium: which features pulled them from High to Medium,
   measured by the contributions to (High margin - Medium margin), which is what decides between them.
7. Direction check for the modifiable features (Sleep, Caffeine, Physical Activity, Diet Quality):
   Spearman correlation between the raw value and its High-class SHAP, and mean SHAP by quintile.

SHAP explains this model's behaviour on this (very likely synthetic) dataset. It is association, not
cause: a direction that matches clinical expectation does not show that changing the input changes
anyone's anxiety.

Run from MindCare AI/: python -m src.explainability.shap_v2
"""

from __future__ import annotations

import json
import platform
import re
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import xgboost
from scipy.stats import mannwhitneyu, spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import DMatrix, XGBClassifier

from src.build_3class_target import bin_anxiety_level

SEED = 42
FOLDS = 5
LOW, MEDIUM, HIGH = 0, 1, 2
CLASSES = ["Low", "Medium", "High"]
REVIEW_THRESHOLD = 0.025  # read-only copy of the served HIGH_PROBA_THRESHOLD, used for the guard
ADDITIVITY_TOL = 1e-4
EXPECTED = {"balanced_accuracy": 0.8055, "flagged": 411, "flagged_true_high": 158, "true_high": 165}

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
V2_SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits_11feature_v2.npz"
PREPROCESSOR_PATH = ROOT / "data" / "processed" / "mindcare_preprocessor_11feature_v2.pkl"
MODEL_PATH = ROOT / "data" / "processed" / "mindcare_final_model_11feature_v2_xgb.pkl"
V2_TUNING_PATH = ROOT / "reports" / "tuning_results_12feature.json"
RF17_RANKING = ROOT / "reports" / "shap_full_ranking_3class.md"
COMPARISON_12 = ROOT / "reports" / "model_comparison_12feature.md"
REPORT_JSON = ROOT / "reports" / "shap_v2.json"
REPORT_MD = ROOT / "reports" / "shap_v2.md"
PLOT_PATH = ROOT / "reports" / "shap_v2_summary.png"

NUMERIC = [
    "Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
    "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
    "Diet Quality (1-10)", "Age",
]
CATEGORICAL = ["Occupation", "Family History of Anxiety"]
FEATURES = NUMERIC + CATEGORICAL
# Clinical expectation for High risk: +1 = more of it should raise risk, -1 = lower it.
MODIFIABLE = {"Sleep Hours": -1, "Caffeine Intake (mg/day)": +1, "Physical Activity (hrs/week)": -1,
              "Diet Quality (1-10)": -1}
CAFFEINE = "Caffeine Intake (mg/day)"
CAFFEINE_LIMIT = 200
CAFFEINE_COUNTERFACTUALS = [0, 100, 200]


def preprocessor() -> ColumnTransformer:
    return ColumnTransformer([("num", StandardScaler(), NUMERIC),
                              ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])


def group_index(column_names: list[str]) -> np.ndarray:
    """Map each transformed column to its raw feature (index into FEATURES)."""
    out = []
    for name in column_names:
        raw = name.split("__", 1)[1]
        match = next((i for i, f in enumerate(FEATURES) if raw == f or raw.startswith(f + "_")), None)
        assert match is not None, name
        out.append(match)
    return np.array(out)


def contributions(model: XGBClassifier, x: np.ndarray, groups: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Exact TreeSHAP per class, grouped to the 11 raw features. Returns (rows, 3, 11) contributions,
    (rows, 3) bias, and the largest additivity error against the raw margin."""
    booster = model.get_booster()
    dm = DMatrix(x)
    raw = booster.predict(dm, pred_contribs=True)  # (rows, classes, columns + 1)
    margin = booster.predict(dm, output_margin=True)  # (rows, classes)
    error = float(np.max(np.abs(raw.sum(axis=2) - margin)))
    grouped = np.zeros((raw.shape[0], raw.shape[1], len(FEATURES)))
    for col, g in enumerate(groups):
        grouped[:, :, g] += raw[:, :, col]
    return grouped, raw[:, :, -1], error


def ranking(values: np.ndarray) -> list[dict]:
    """values: (rows, 11). Mean |SHAP| per feature, sorted, with share of the total."""
    mean_abs = np.abs(values).mean(axis=0)
    total = mean_abs.sum()
    order = np.argsort(-mean_abs)
    return [{"rank": r + 1, "feature": FEATURES[i], "mean_abs_shap": float(mean_abs[i]), "share": float(mean_abs[i] / total)}
            for r, i in enumerate(order)]


def parse_rf17_ranking() -> list[dict]:
    text = RF17_RANKING.read_text(encoding="utf-8").split("## Grouped Ranking", 1)[1].split("## Full", 1)[0]
    rows = re.findall(r"^\| (\d+) \| ([^|]+?) \| ([0-9.]+) \|", text, flags=re.M)
    total = sum(float(v) for _, _, v in rows)
    return [{"rank": int(r), "feature": f.strip(), "share": float(v) / total} for r, f, v in rows]


def parse_comparison_12() -> dict[str, list[dict]]:
    text = COMPARISON_12.read_text(encoding="utf-8").split("## 5. SHAP", 1)[1].split("## 6.", 1)[0]
    out = {"rf_current": [], "rf_retuned": [], "xgb_retuned": []}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0].isdigit():
            for key, cell in zip(out, cells[1:]):
                name, share = re.match(r"(.+) \(([0-9.]+)%\)", cell).groups()
                out[key].append({"rank": int(cells[0]), "feature": name, "share": float(share) / 100})
    return out


def main() -> None:
    raw_df = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as s:
        train_idx, val_idx = s["train_original_idx"], s["val_original_idx"]
    with np.load(V2_SPLITS_PATH) as s:
        assert "X_test" not in s.files
        assert np.array_equal(s["train_original_idx"], train_idx) and np.array_equal(s["val_original_idx"], val_idx)
    pre_served, model_served = joblib.load(PREPROCESSOR_PATH), joblib.load(MODEL_PATH)
    groups = group_index(list(pre_served.get_feature_names_out()))

    # ---- 1. Guard: the served files must reproduce v2's documented validation numbers. ----
    val = raw_df.iloc[val_idx].reset_index(drop=True)
    y_val = bin_anxiety_level(val["Anxiety Level (1-10)"].to_numpy())
    x_val = np.asarray(pre_served.transform(val[FEATURES]))
    p_val = model_served.predict_proba(x_val)
    pred_val = p_val.argmax(axis=1)
    flagged = p_val[:, HIGH] >= REVIEW_THRESHOLD
    guard = {"balanced_accuracy": round(float(balanced_accuracy_score(y_val, pred_val)), 4),
             "flagged": int(flagged.sum()), "flagged_true_high": int((flagged & (y_val == HIGH)).sum()),
             "true_high": int((y_val == HIGH).sum())}
    print("guard:", guard)
    if guard != EXPECTED:
        raise SystemExit(f"STOP: served v2 does not reproduce its validation numbers: {guard} != {EXPECTED}")

    # ---- 2. SHAP: validation (served files) and out-of-fold. ----
    shap_val, bias_val, err_val = contributions(model_served, x_val, groups)
    print(f"validation additivity max error {err_val:.2e}")
    assert err_val < ADDITIVITY_TOL

    df = raw_df.iloc[np.concatenate([train_idx, val_idx])].reset_index(drop=True)  # no test rows
    y = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    params = json.loads(V2_TUNING_PATH.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]
    shap_oof = np.zeros((len(df), 3, len(FEATURES)))
    pred_oof = np.zeros(len(df), dtype=int)
    p_high_oof = np.zeros(len(df))
    fold_errors = []
    for tr, te in StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y):
        pre = preprocessor()
        x_tr = np.asarray(pre.fit_transform(df.iloc[tr][FEATURES]))
        x_te = np.asarray(pre.transform(df.iloc[te][FEATURES]))
        m = XGBClassifier(**params, objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)
        m.fit(x_tr, y[tr])
        g = group_index(list(pre.get_feature_names_out()))
        shap_oof[te], _, err = contributions(m, x_te, g)
        proba = m.predict_proba(x_te)
        pred_oof[te] = proba.argmax(axis=1)
        p_high_oof[te] = proba[:, HIGH]
        fold_errors.append(err)
    print(f"out-of-fold additivity max error {max(fold_errors):.2e}")
    assert max(fold_errors) < ADDITIVITY_TOL

    # ---- 3/4. Rankings and Stress Level dominance. ----
    rank_val_high = ranking(shap_val[:, HIGH])
    rank_oof_high = ranking(shap_oof[:, HIGH])
    rank_val_all = ranking(np.abs(shap_val).mean(axis=1))  # mean |SHAP| over the 3 classes
    rank_oof_all = ranking(np.abs(shap_oof).mean(axis=1))
    stress = "Stress Level (1-10)"

    def share(rows: list[dict], f: str) -> float:
        return next(r["share"] for r in rows if r["feature"] == f)

    dominance = {name: {"stress_share": share(r, stress), "stress_rank": next(x["rank"] for x in r if x["feature"] == stress),
                        "ratio_to_second": r[0]["mean_abs_shap"] / r[1]["mean_abs_shap"] if r[0]["feature"] == stress else None}
                 for name, r in (("validation_high", rank_val_high), ("oof_high", rank_oof_high),
                                 ("validation_all_classes", rank_val_all), ("oof_all_classes", rank_oof_all))}
    rf17, cmp12 = parse_rf17_ranking(), parse_comparison_12()

    # ---- 5. Caffeine shortcut. ----
    caf_val = val[CAFFEINE].to_numpy()
    caf_oof = df[CAFFEINE].to_numpy()
    observed = {
        "validation": {"true_high_low_caffeine": int(((y_val == HIGH) & (caf_val <= CAFFEINE_LIMIT)).sum()),
                       "predicted_high": int(((y_val == HIGH) & (caf_val <= CAFFEINE_LIMIT) & (pred_val == HIGH)).sum()),
                       "flagged_at_0.025": int(((y_val == HIGH) & (caf_val <= CAFFEINE_LIMIT) & (p_val[:, HIGH] >= REVIEW_THRESHOLD)).sum()),
                       "true_high_all": int((y_val == HIGH).sum()),
                       "predicted_high_all": int(((y_val == HIGH) & (pred_val == HIGH)).sum())},
        "oof": {"true_high_low_caffeine": int(((y == HIGH) & (caf_oof <= CAFFEINE_LIMIT)).sum()),
                "predicted_high": int(((y == HIGH) & (caf_oof <= CAFFEINE_LIMIT) & (pred_oof == HIGH)).sum()),
                "flagged_at_0.025": int(((y == HIGH) & (caf_oof <= CAFFEINE_LIMIT) & (p_high_oof >= REVIEW_THRESHOLD)).sum()),
                "true_high_all": int((y == HIGH).sum()),
                "predicted_high_all": int(((y == HIGH) & (pred_oof == HIGH)).sum())},
    }
    # Data coverage: how common is low caffeine in each class, and how do the low-caffeine true-High
    # rows differ from the other true-High rows on the top features? (train + validation only)
    coverage = {}
    for k, c in enumerate(CLASSES):
        in_class = y == k
        n_low = int((in_class & (caf_oof <= CAFFEINE_LIMIT)).sum())
        coverage[c] = {"rows": int(in_class.sum()), "caffeine_le_limit": n_low, "share": n_low / int(in_class.sum())}
    low_high = (y == HIGH) & (caf_oof <= CAFFEINE_LIMIT)
    other_high = (y == HIGH) & (caf_oof > CAFFEINE_LIMIT)
    profile = {}
    for f in ["Stress Level (1-10)", "Therapy Sessions (per month)", "Sleep Hours", CAFFEINE, "Physical Activity (hrs/week)"]:
        a, b = df.loc[low_high, f].to_numpy(dtype=float), df.loc[other_high, f].to_numpy(dtype=float)
        profile[f] = {"low_caffeine_high": {"n": len(a), "mean": float(a.mean()), "median": float(np.median(a))},
                      "other_high": {"n": len(b), "mean": float(b.mean()), "median": float(np.median(b))},
                      "mannwhitney_p": float(mannwhitneyu(a, b).pvalue)}
    a, b = p_high_oof[low_high], p_high_oof[other_high]
    profile["P(High), out-of-fold"] = {"low_caffeine_high": {"n": len(a), "mean": float(a.mean()), "median": float(np.median(a))},
                                       "other_high": {"n": len(b), "mean": float(b.mean()), "median": float(np.median(b))},
                                       "mannwhitney_p": float(mannwhitneyu(a, b).pvalue)}

    high_rows = val[y_val == HIGH].copy()
    counterfactual = {}
    for mg in CAFFEINE_COUNTERFACTUALS:
        cf = high_rows.copy()
        cf[CAFFEINE] = mg
        p = model_served.predict_proba(np.asarray(pre_served.transform(cf[FEATURES])))
        counterfactual[str(mg)] = {"predicted_high": int((p.argmax(axis=1) == HIGH).sum()),
                                   "flagged_at_0.025": int((p[:, HIGH] >= REVIEW_THRESHOLD).sum()),
                                   "of": int(len(cf))}

    # ---- 6. True-High validation rows predicted Medium: what pulled them from High to Medium. ----
    missed = np.where((y_val == HIGH) & (pred_val == MEDIUM))[0]
    contrast = shap_val[missed, HIGH] - shap_val[missed, MEDIUM]  # contributions to (High - Medium) margin
    missed_rows = []
    for k, i in enumerate(missed):
        order = np.argsort(contrast[k])  # most negative first = pulled hardest toward Medium
        missed_rows.append({
            "val_row": int(i), "p_high": float(p_val[i, HIGH]), "p_medium": float(p_val[i, MEDIUM]),
            "flagged_at_0.025": bool(p_val[i, HIGH] >= REVIEW_THRESHOLD),
            "age": int(val.iloc[i]["Age"]),
            "pulled_toward_medium": [{"feature": FEATURES[j], "contribution": float(contrast[k, j]),
                                      "value": (val.iloc[i][FEATURES[j]].item() if hasattr(val.iloc[i][FEATURES[j]], "item")
                                                else val.iloc[i][FEATURES[j]])}
                                     for j in order[:3] if contrast[k, j] < 0],
        })
    top2_counts = {f: 0 for f in FEATURES}
    for row in missed_rows:
        for item in row["pulled_toward_medium"][:2]:
            top2_counts[item["feature"]] += 1
    missed_summary = sorted(({"feature": f, "mean_contribution": float(contrast[:, j].mean()), "in_top_2": top2_counts[f]}
                             for j, f in enumerate(FEATURES)), key=lambda r: r["mean_contribution"])

    # ---- 7. Direction check for modifiable features. ----
    direction = {}
    for f, expected_sign in MODIFIABLE.items():
        j = FEATURES.index(f)
        out = {}
        for view, frame, sv in (("validation", val, shap_val), ("oof", df, shap_oof)):
            x = frame[f].to_numpy(dtype=float)
            s = sv[:, HIGH, j]
            rho = float(spearmanr(x, s).statistic)
            quint = pd.qcut(x, 5, duplicates="drop")
            by_q = pd.Series(s).groupby(quint, observed=True).mean()
            out[view] = {"spearman": rho, "quintile_mean_shap": [float(v) for v in by_q.to_numpy()],
                         "quintile_bins": [str(b) for b in by_q.index],
                         "monotonic": bool(np.all(np.diff(by_q.to_numpy()) * expected_sign >= 0))}
        matches = all(np.sign(out[v]["spearman"]) == expected_sign for v in out)
        direction[f] = {"clinical_expectation": "higher -> more risk" if expected_sign > 0 else "higher -> less risk",
                        "matches": bool(matches), **out}

    result = {
        "model": "served 11-feature v2 XGBoost (data/processed/mindcare_final_model_11feature_v2_xgb.pkl)",
        "guard": guard, "units": "contributions to the raw class margin (softmax logit); exact TreeSHAP",
        "additivity_max_error": {"validation": err_val, "oof_folds": fold_errors},
        "rows": {"validation": len(val), "oof": len(df)},
        "ranking_high": {"validation": rank_val_high, "oof": rank_oof_high},
        "ranking_all_classes": {"validation": rank_val_all, "oof": rank_oof_all},
        "stress_dominance": dominance,
        "earlier_rankings": {"rf_17_feature (shap_full_ranking_3class.md, mean |SHAP| over 3 classes, 500 val rows)": rf17,
                             **{f"{k} (model_comparison_12feature.md, 300 val rows)": v for k, v in cmp12.items()}},
        "caffeine_shortcut": {"limit_mg": CAFFEINE_LIMIT, "observed": observed, "counterfactual_validation_true_high": counterfactual,
                              "coverage_train_val": coverage, "low_caffeine_high_profile": profile},
        "true_high_predicted_medium": {"count": len(missed), "rows": missed_rows, "summary": missed_summary},
        "direction_check": direction,
        "library_versions": {"python": platform.python_version(), "xgboost": xgboost.__version__,
                             "scikit-learn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__},
        "test_set_used": False,
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    plot(rank_val_high, rank_oof_high)
    write_markdown(result)
    print(f"wrote {REPORT_MD.relative_to(ROOT)}, {REPORT_JSON.relative_to(ROOT)}, {PLOT_PATH.relative_to(ROOT)}")


def plot(val_rank: list[dict], oof_rank: list[dict]) -> None:
    names = [r["feature"] for r in val_rank][::-1]
    oof = {r["feature"]: r["mean_abs_shap"] for r in oof_rank}
    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(y + 0.2, [next(r["mean_abs_shap"] for r in val_rank if r["feature"] == n) for n in names], 0.4,
            label="Validation (served files, 1,650 rows)", color="#1f6f8b")
    ax.barh(y - 0.2, [oof[n] for n in names], 0.4, label="Out-of-fold (9,350 rows)", color="#99c1b9")
    ax.set_yticks(y, names)
    ax.set_xlabel("Mean |SHAP| for the High class (margin units)")
    ax.set_title("11-feature v2 XGBoost: feature importance for High anxiety")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=160)
    plt.close(fig)


def write_markdown(r: dict) -> None:
    def rank_table(rows_a: list[dict], rows_b: list[dict], a: str, b: str) -> str:
        b_by = {x["feature"]: x for x in rows_b}
        lines = [f"| Rank | Feature | {a}: mean \\|SHAP\\| (share) | {b}: rank (share) |", "|---|---|---|---|"]
        for x in rows_a:
            y = b_by[x["feature"]]
            lines.append(f"| {x['rank']} | {x['feature']} | {x['mean_abs_shap']:.4f} ({x['share']:.1%}) | {y['rank']} ({y['share']:.1%}) |")
        return "\n".join(lines)

    earlier = r["earlier_rankings"]
    v2_all = r["ranking_all_classes"]["validation"]
    keys = list(earlier)
    comp_lines = ["| Rank | v2 XGBoost, all classes (validation) | " + " | ".join(k.split(" (")[0] for k in keys) + " |",
                  "|---" * (2 + len(keys)) + "|"]
    for i in range(max(len(v2_all), *(len(earlier[k]) for k in keys))):
        cells = [f"{v2_all[i]['feature']} ({v2_all[i]['share']:.1%})" if i < len(v2_all) else ""]
        cells += [f"{earlier[k][i]['feature']} ({earlier[k][i]['share']:.1%})" if i < len(earlier[k]) else "" for k in keys]
        comp_lines.append(f"| {i + 1} | " + " | ".join(cells) + " |")

    d = r["stress_dominance"]
    cs = r["caffeine_shortcut"]
    ob, cf = cs["observed"], cs["counterfactual_validation_true_high"]
    th = r["true_high_predicted_medium"]
    n_old = sum(1 for m in th["rows"] if m["age"] >= 50)
    o = ob["oof"]
    caffeine_note = (
        f"**Reading the two forms together.** v2 does not *require* high caffeine: with caffeine set to 0 mg/day, "
        f"{cf['0']['predicted_high']} of {cf['0']['of']} true-High patients are still predicted High, so there is no hard "
        f"shortcut like the Random Forest's. But the few true-High patients who actually report ≤ {cs['limit_mg']} mg/day "
        f"(unusual in this data) are never labelled High ({o['predicted_high']} of {o['true_high_low_caffeine']} out-of-fold), "
        f"and the review flag catches only {o['flagged_at_0.025']} of {o['true_high_low_caffeine']} of them, far below its "
        f"96.2% catch rate for all true-High patients (`reports/calibration_review_flag_11feature_v2.md`). The sample is "
        f"small ({o['true_high_low_caffeine']} patients), but this is a **safety gap for low-caffeine High patients** to "
        f"tell the psychologist reviewer about, and caffeine is only estimated from drink counts in the API.")
    cov, prof = cs["coverage_train_val"], cs["low_caffeine_high_profile"]
    cov_lines = ["| Class | Rows (train + validation) | Caffeine ≤ " + str(cs["limit_mg"]) + " mg/day | Share of the class |", "|---|---|---|---|"]
    cov_lines += [f"| {c} | {v['rows']:,} | {v['caffeine_le_limit']:,} | {v['share']:.1%} |" for c, v in cov.items()]
    prof_lines = ["| Feature | Low-caffeine true High: median (mean) | Other true High: median (mean) | Mann-Whitney p |", "|---|---|---|---|"]
    for f, v in prof.items():
        a, b = v["low_caffeine_high"], v["other_high"]
        prof_lines.append(f"| {f} | {a['median']:.3g} ({a['mean']:.3g}), n = {a['n']} | {b['median']:.3g} ({b['mean']:.3g}), n = {b['n']} | {v['mannwhitney_p']:.2g} |")
    st, tp, sl, pa, ph = (prof[k] for k in ("Stress Level (1-10)", "Therapy Sessions (per month)", "Sleep Hours",
                                           "Physical Activity (hrs/week)", "P(High), out-of-fold"))
    diff = [x for x in (tp, sl, pa) if x["mannwhitney_p"] < 0.001]
    coverage_note = (
        f"**Conclusion: a data-coverage gap, not a caffeine effect alone.** Low reported caffeine is rare among High "
        f"patients in this data: {cov['High']['caffeine_le_limit']} of {cov['High']['rows']} true-High rows "
        f"({cov['High']['share']:.1%}), against {cov['Low']['share']:.1%} of Low and {cov['Medium']['share']:.1%} of Medium. "
        f"These {st['low_caffeine_high']['n']} patients have the same stress level as other High patients (median "
        f"{st['low_caffeine_high']['median']:.3g} vs {st['other_high']['median']:.3g}, p = {st['mannwhitney_p']:.2g}), but "
        f"differ on the other top features: therapy sessions {tp['low_caffeine_high']['median']:.3g} vs "
        f"{tp['other_high']['median']:.3g} per month, sleep {sl['low_caffeine_high']['median']:.3g} vs "
        f"{sl['other_high']['median']:.3g} h, physical activity {pa['low_caffeine_high']['median']:.3g} vs "
        f"{pa['other_high']['median']:.3g} h/week ({'all p < 0.001' if len(diff) == 3 else 'see table'}). The model gives them "
        f"a median P(High) of {ph['low_caffeine_high']['median']:.3f} against {ph['other_high']['median']:.3f} for other High "
        f"patients. So the training data contain very few High patients with high stress but lower values on the "
        f"model's other risk signals ({cov['High']['caffeine_le_limit']} in 9,350 rows), and high stress alone does not move the model to "
        f"High. This is likely an artifact of the (very likely synthetic) data; real patients with that profile could be "
        f"under-detected in the same way. Small sample: a pattern to review, not an established effect. "
        f'The under-detected group is better described as "high reported stress with otherwise lower-risk lifestyle signals (more sleep, fewer therapy sessions, more activity)"; low caffeine is a correlate, not the cause.')
    missed_lines = ["| Val row | Age | P(High) | P(Medium) | Flagged at 0.025 | Pulled toward Medium (contribution to High − Medium margin; raw value) |",
                    "|---|---|---|---|---|---|"]
    for m in th["rows"]:
        pulls = "; ".join(f"{p['feature']} {p['contribution']:+.2f} (= {p['value']})" for p in m["pulled_toward_medium"])
        missed_lines.append(f"| {m['val_row']} | {m['age']}{' (50+, refused by the API)' if m['age'] >= 50 else ''} | {m['p_high']:.3f} | {m['p_medium']:.3f} | {'yes' if m['flagged_at_0.025'] else 'no'} | {pulls} |")
    summary_lines = ["| Feature | Mean contribution to (High − Medium) | Among the top 2 pulls toward Medium |", "|---|---|---|"]
    summary_lines += [f"| {s['feature']} | {s['mean_contribution']:+.3f} | {s['in_top_2']} of {th['count']} |" for s in th["summary"]]
    dir_lines = ["| Feature | Clinical expectation | Spearman (validation / out-of-fold) | Mean High SHAP by quintile, low → high (validation) | Monotonic (val / oof) | Matches |",
                 "|---|---|---|---|---|---|"]
    for f, v in r["direction_check"].items():
        dir_lines.append(f"| {f} | {v['clinical_expectation']} | {v['validation']['spearman']:+.3f} / {v['oof']['spearman']:+.3f} | "
                         + ", ".join(f"{q:+.3f}" for q in v["validation"]["quintile_mean_shap"])
                         + f" | {'yes' if v['validation']['monotonic'] else 'no'} / {'yes' if v['oof']['monotonic'] else 'no'} | "
                         + f"{'**yes**' if v['matches'] else '**NO - conflict**'} |")
    conflicts = [f for f, v in r["direction_check"].items() if not v["matches"]]
    non_mono = [f for f, v in r["direction_check"].items() if v["matches"] and not (v["validation"]["monotonic"] and v["oof"]["monotonic"])]

    REPORT_MD.write_text(f"""# SHAP (Phase 17) for the served 11-feature v2 XGBoost

Script: `src/explainability/shap_v2.py`. **The test set was not used.** Validation = the served files on the
{r['rows']['validation']:,} validation rows; out-of-fold = {r['rows']['oof']:,} train + validation rows, 5-fold
stratified on the 3-class label (shuffled, seed 42), v2 params, preprocessing fitted inside each fold.
Exact TreeSHAP from XGBoost (`pred_contribs`); {r['units']}. Occupation (13 one-hot columns) and Family History
(2) are added back into one feature by summing each row's signed contributions. Synthetic-looking dataset:
SHAP describes this model on this data and is association, not cause.

## 1. Guard: the served files reproduce v2's validation numbers

Balanced accuracy {r['guard']['balanced_accuracy']}, {r['guard']['flagged']} flagged at P(High) ≥ 0.025,
{r['guard']['flagged_true_high']}/{r['guard']['true_high']} true High flagged — matches the documented 0.8055 / 411 / 158 of 165.

## 2. Additivity check

Contributions + bias = raw margin for every row and class: largest error {r['additivity_max_error']['validation']:.1e}
(validation) and {max(r['additivity_max_error']['oof_folds']):.1e} (out-of-fold folds).

## 3. Ranking for the High class (mean |SHAP|)

{rank_table(r['ranking_high']['validation'], r['ranking_high']['oof'], 'Validation', 'Out-of-fold')}

![SHAP summary](shap_v2_summary.png)

### Compared with the earlier models (all-class view: mean |SHAP| averaged over Low/Medium/High, shares of total)

The earlier reports averaged over all three classes, so v2 is shown the same way here. Sources:
`shap_full_ranking_3class.md` is the **17-feature** Random Forest (500 validation rows); the three 12-feature
columns are from `model_comparison_12feature.md` (300 validation rows).

{chr(10).join(comp_lines)}

## 4. Stress Level dominance (share of total mean |SHAP|)

| View | Stress Level share | Rank | Times the 2nd feature |
|---|---|---|---|
""" + "\n".join(f"| {k.replace('_', ' ')} | {v['stress_share']:.1%} | {v['stress_rank']} | "
                f"{(f'{v['ratio_to_second']:.2f}x' if v['ratio_to_second'] else '—')} |" for k, v in d.items()) + f"""

## 5. Caffeine shortcut (does v2 need high caffeine to predict High?)

**Observed:** true-High patients whose caffeine is ≤ {cs['limit_mg']} mg/day.

| View | True High with caffeine ≤ {cs['limit_mg']} | Of those, predicted High | Of those, flagged at 0.025 | All true High predicted High (for comparison) |
|---|---|---|---|---|
| Validation | {ob['validation']['true_high_low_caffeine']} | {ob['validation']['predicted_high']} | {ob['validation']['flagged_at_0.025']} | {ob['validation']['predicted_high_all']} of {ob['validation']['true_high_all']} |
| Out-of-fold | {ob['oof']['true_high_low_caffeine']} | {ob['oof']['predicted_high']} | {ob['oof']['flagged_at_0.025']} | {ob['oof']['predicted_high_all']} of {ob['oof']['true_high_all']} |

**Counterfactual:** every true-High validation patient with caffeine set to a fixed value (the form behind the
documented "Random Forest 0 of 165, 12-feature XGBoost 127–129"; that original script is not in the repo, so this
is a re-implementation, not a re-run).

| Caffeine set to | Still predicted High | Still flagged at 0.025 |
|---|---|---|
""" + "\n".join(f"| {mg} mg/day | {v['predicted_high']} of {v['of']} | {v['flagged_at_0.025']} of {v['of']} |" for mg, v in cf.items()) + f"""

{caffeine_note}

**Coverage in the training data (train + validation, 9,350 rows).**

{chr(10).join(cov_lines)}

**The {prof['Stress Level (1-10)']['low_caffeine_high']['n']} low-caffeine true-High rows vs the other true-High rows (out-of-fold).**

{chr(10).join(prof_lines)}

{coverage_note}

## 6. The {th['count']} true-High validation patients predicted Medium

Contributions to (High margin − Medium margin), which is what decides between High and Medium; negative values
pulled the patient toward Medium. Up to three strongest pulls per patient. {n_old} of the {th['count']} are aged 50+,
which the live API refuses (supported range 18–49), so {th['count'] - n_old} are in the range the API serves.

{chr(10).join(missed_lines)}

Across the {th['count']}:

{chr(10).join(summary_lines)}

## 7. Direction check for modifiable features (the recommendation engine depends on this)

Spearman correlation between each raw value and its High-class SHAP (positive = more of it pushes toward High),
and the mean High-class SHAP across value quintiles.

{chr(10).join(dir_lines)}

**Conflicts with the clinical direction:** {', '.join(conflicts) if conflicts else 'none'}.
{('**Right overall direction but not monotonic across quintiles:** ' + ', '.join(non_mono) + '.') if non_mono else 'All four are monotonic across quintiles in both views.'}
A matching direction only shows the model's association on this dataset; it is not evidence that changing the
input would change a patient's risk.

Libraries: {', '.join(f'{k} {v}' for k, v in r['library_versions'].items())}.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
