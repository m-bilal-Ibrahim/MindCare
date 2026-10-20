"""Comparison with published methods: published tabular setups re-implemented on the 11 v2 features.

CV only: the 1,650 test rows are never loaded, no served file or threshold is read or changed. Same folds as
src/experiments/ablation_study.py (the 9,350 train + validation rows, 5-fold stratified, shuffled, seed 42,
preprocessing fitted inside each fold).

- Guard: v2 (XGBoost, tuned settings) re-run here must reproduce the per-fold scores in reports/ablation_study.json.
- Baselines, with the settings each paper states on its own page (anything not stated = library default):
  - Qasrawi et al. 2022: RBF SVM, C=20, gamma=0.001; MLP, one hidden layer of 500 logistic units, max_iter 500.
  - Vu et al. 2025: LightGBM (tuned values not given; defaults), with and without their random undersampling.
  - Rois et al. 2021 / Vu et al. 2025: logistic regression (defaults).
- Paired comparison with v2: per-fold difference (mean ± std), paired t-test on fold balanced accuracy and exact
  McNemar on pooled out-of-fold correctness, both Holm-adjusted. Folds share training data: p-values approximate.

The literature table (Table A) is hand-entered from the source pages listed in SOURCES; Table B is computed here.

Run from MindCare AI/: python -m src.experiments.sota_baselines   (--report-only rebuilds the Markdown)
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import lightgbm
import numpy as np
import pandas as pd
import sklearn
import xgboost
from lightgbm import LGBMClassifier
from scipy.stats import ttest_rel
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level
from src.experiments.ablation_study import (DATA_PATH, FOLDS, HIGH, ROOT, SEED, SPLITS_PATH, TUNING_12,
                                            V2_CATEGORICAL, V2_NUMERIC, holm, mcnemar)

ABLATION_JSON = ROOT / "reports" / "ablation_study.json"
REPORT_JSON = ROOT / "reports" / "sota_baselines.json"
REPORT_MD = ROOT / "reports" / "sota_comparison.md"
METRICS = ("balanced_accuracy", "macro_f1", "high_recall")

# key, label, source, factory(params) -> estimator, undersample
BASELINES = [
    ("svm_rbf", "RBF SVM (C=20, γ=0.001)", "Qasrawi et al. 2022",
     lambda p: SVC(kernel="rbf", C=20, gamma=0.001, random_state=SEED), False),
    ("mlp_500", "MLP (1×500 logistic, max_iter 500)", "Qasrawi et al. 2022",
     lambda p: MLPClassifier(hidden_layer_sizes=(500,), activation="logistic", max_iter=500, random_state=SEED), False),
    ("lgbm", "LightGBM (defaults)", "Vu et al. 2025",
     lambda p: LGBMClassifier(random_state=SEED, n_jobs=-1, verbose=-1), False),
    ("lgbm_under", "LightGBM + random undersampling", "Vu et al. 2025",
     lambda p: LGBMClassifier(random_state=SEED, n_jobs=-1, verbose=-1), True),
    ("logreg", "Logistic regression (defaults)", "Rois et al. 2021; Vu et al. 2025",
     lambda p: LogisticRegression(max_iter=1000), False),
]


def pipeline(est) -> Pipeline:
    pre = ColumnTransformer([("num", StandardScaler(), V2_NUMERIC),
                             ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), V2_CATEGORICAL)])
    return Pipeline([("pre", pre), ("model", est)])


def undersample(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Row positions keeping every class at the size of the smallest one (Vu et al.: majority down to minority)."""
    n = np.bincount(y).min()
    return np.sort(np.concatenate([rng.choice(np.flatnonzero(y == c), n, replace=False) for c in np.unique(y)]))


def score(y: np.ndarray, pred: np.ndarray) -> dict:
    return {"balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro")),
            "high_recall": float((pred[y == HIGH] == HIGH).mean())}


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as s:
        idx = np.concatenate([s["train_original_idx"], s["val_original_idx"]])  # no test rows
    df = raw.iloc[idx].reset_index(drop=True)
    y = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    x = df[V2_NUMERIC + V2_CATEGORICAL]
    folds = list(StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y))
    xgb_params = json.loads(TUNING_12.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]

    models = [("v2", "Served v2: XGBoost (tuned)", "this project",
               lambda p: XGBClassifier(**xgb_params, objective="multi:softprob", eval_metric="mlogloss",
                                       random_state=SEED, n_jobs=-1), False)] + BASELINES
    cv = {k: [] for k, *_ in models}
    oof = {k: np.full(len(df), -1) for k, *_ in models}
    train_rows = {k: [] for k, *_ in models}
    for f, (tr, te) in enumerate(folds):
        rng = np.random.default_rng(SEED + f)
        for key, _, _, make, under in models:
            rows = tr[undersample(y[tr], rng)] if under else tr
            m = pipeline(make(xgb_params)).fit(x.iloc[rows], y[rows])
            pred = m.predict(x.iloc[te])
            cv[key].append(score(y[te], pred))
            oof[key][te] = pred
            train_rows[key].append(int(len(rows)))
            print(f"fold {f + 1} {key}: " + ", ".join(f"{m_} {v:.4f}" for m_, v in cv[key][-1].items()), flush=True)

    ref = json.loads(ABLATION_JSON.read_text(encoding="utf-8"))["cv_scores"]["v2"]
    if any(abs(cv["v2"][i][m] - ref[i][m]) > 1e-9 for i in range(FOLDS) for m in METRICS):
        raise SystemExit(f"STOP: v2 does not reproduce reports/ablation_study.json fold scores: {cv['v2']}")
    print("guard: v2 reproduces reports/ablation_study.json fold scores")

    correct = {k: oof[k] == y for k in oof}
    paired = {}
    for key, *_ in BASELINES:
        diffs = {m: np.array([cv[key][i][m] - cv["v2"][i][m] for i in range(FOLDS)]) for m in METRICS}
        paired[key] = {
            "cv_delta": {m: {"mean": float(d.mean()), "std": float(d.std(ddof=1))} for m, d in diffs.items()},
            "t_test_balanced_accuracy_p": float(ttest_rel([c["balanced_accuracy"] for c in cv[key]],
                                                          [c["balanced_accuracy"] for c in cv["v2"]]).pvalue),
            "mcnemar_oof_vs_v2": mcnemar(correct["v2"], correct[key]),
        }
    ht = holm({k: v["t_test_balanced_accuracy_p"] for k, v in paired.items()})
    hm = holm({k: v["mcnemar_oof_vs_v2"]["p_value"] for k, v in paired.items()})
    for k in paired:
        paired[k]["t_test_holm_p"], paired[k]["mcnemar_holm_p"] = ht[k], hm[k]

    result = {
        "rows_cv": len(df), "folds": FOLDS, "seed": SEED, "test_set_used": False,
        "models": {k: {"label": lab, "source": src, "undersampled": u, "train_rows_per_fold": train_rows[k]}
                   for k, lab, src, _, u in models},
        "cv_scores": cv,
        "summary": {k: {m: {"mean": float(np.mean([c[m] for c in cv[k]])), "std": float(np.std([c[m] for c in cv[k]], ddof=1))}
                        for m in METRICS} for k in cv},
        "paired_vs_v2": paired,
        "library_versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                             "xgboost": xgboost.__version__, "lightgbm": lightgbm.__version__,
                             "numpy": np.__version__, "pandas": pd.__version__},
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    write_markdown(result)
    print(f"wrote {REPORT_MD.relative_to(ROOT)} and {REPORT_JSON.relative_to(ROOT)}")


# ---- Table A: hand-entered from the source pages (opened 2026-10-20); not computed here ----
LITERATURE = [
    ("Nishwa, Abbas & Lee (2026), *Front. Psychiatry* 17:1727014 [1]",
     "Kaggle \"Social Anxiety Dataset\" (the source of **our** data), 11,000 adults aged 18-64",
     "7 regressors (gradient boosting, RF, lasso, linear, elastic net, SVR, MLP); 80/20 split, 5-fold CV tuning",
     "Anxiety Level 1-10 (regression)",
     "MAE, MAPE, RMSE, R² named but **no numeric values given** (normalised radar chart only); GB and RF ranked best"),
    ("Qasrawi et al. (2022), *JMIR Form. Res.* 6(8):e32736 [2]",
     "Real survey, 3,984 schoolchildren aged 10-15, West Bank, 2013-14",
     "RF, ANN, DT, SVM, NB; 70:20:10 split, CV grid search",
     "Anxiety normal vs abnormal (GAD-7 ≥ 5), binary",
     "Anxiety accuracy SVM 76.4%, RF 78.6% (Table 7; text gives 76.5% / 78.4%; abstract gives different figures)"),
    ("Rois et al. (2021), *J. Health Popul. Nutr.* 40:50 [3]",
     "Real online survey, 355 Bangladeshi university students",
     "DT, RF, SVM (poly-2, linear), LR; 70/30 split × 11 runs, plus 3/5/10-fold CV",
     "Perceived stress in last 12 months, yes/no (30.7% yes)",
     "RF hold-out accuracy 0.8929, sensitivity 0.8953, specificity 0.8853; RF AUC 0.8715 (one split); LR accuracy 0.7723 (abstract differs)"),
    ("Moon & Woo (2025), *Front. Public Health* 12:1504739 [4]",
     "Real national survey (KYRBS 2020-23), 213,820 Korean adolescents aged 12-18",
     "RF and ANN after LASSO / SelectKBest / XGBoost feature selection, SMOTE; validation scheme not stated",
     "GAD-7 ≥ 10, binary (17.9% positive)",
     "Best accuracy ANN+SelectKBest 82%, AUC 81%, sensitivity 44%; RF+XGBoost features AUC 82%, sensitivity 64%"),
    ("Vu et al. (2025), *BMC Med. Inform. Decis. Mak.* 25:83 [5]",
     "Real national survey (NHANES 2013-14), 5,372 US adults (9.5% depressed)",
     "LR, RF, NB, SVM, XGBoost, LightGBM; random undersampling; 80/20 split, 5-fold CV grid search",
     "Depression, PHQ-9 ≥ 10, binary",
     "XGBoost accuracy 0.69, AUC 0.69, F1 0.69, sensitivity 0.68; SVM 0.68 / 0.68 / 0.67; LR 0.66 / 0.66 / 0.65; LightGBM 0.62 / 0.62 / 0.63"),
    ("Almadhor et al. (2023), *Sensors* 23(15):6664 [6]",
     "WESAD lab recordings (chest sensor), 14 subjects as described",
     "SelectKBest + SMOTE + stacking ensemble; k-fold CV (k not given), no subject-independent split described",
     "Stress vs calm, binary",
     "Stacking accuracy 0.997, F1 0.998; LR alone accuracy 0.978"),
    ("Dahal, Bogue-Jimenez & Doblas (2023), *Sensors* 23(11):5220 [7]",
     "WESAD (15 subjects) and SWELL (22-25 subjects) HRV features",
     "mRMR (8 features) + RF; each subject's rows split 70/30, so subjects appear in train and test",
     "Stress vs no stress, binary",
     "≥ 99% per-subject accuracy; leave-one-subject-out on WESAD: accuracy 0.3143 to 0.949 by subject"),
]

SOURCES = [
    "[1] https://pmc.ncbi.nlm.nih.gov/articles/PMC13230050 — doi:10.3389/fpsyt.2026.1727014",
    "[2] https://formative.jmir.org/2022/8/e32736 — doi:10.2196/32736",
    "[3] https://pmc.ncbi.nlm.nih.gov/articles/PMC8627029/ — doi:10.1186/s41043-021-00276-5",
    "[4] https://www.frontiersin.org/articles/10.3389/fpubh.2024.1504739/full — doi:10.3389/fpubh.2024.1504739",
    "[5] https://link.springer.com/article/10.1186/s12911-025-02903-1 (and its /tables/2) — doi:10.1186/s12911-025-02903-1",
    "[6] https://pmc.ncbi.nlm.nih.gov/articles/PMC10422546/ — doi:10.3390/s23156664",
    "[7] https://pmc.ncbi.nlm.nih.gov/articles/PMC10255919/ — doi:10.3390/s23115220",
    "[8] https://www.kaggle.com/datasets/natezhang123/social-anxiety-dataset (Data Card and Code tab)",
]


def reading(pv: dict, mods: dict) -> str:
    """One-paragraph summary built from the paired results (Holm-adjusted t-test on balanced accuracy)."""
    ba = lambda k: pv[k]["cv_delta"]["balanced_accuracy"]["mean"]
    tie = [k for k in pv if pv[k]["t_test_holm_p"] >= 0.05]
    worse = [k for k in pv if pv[k]["t_test_holm_p"] < 0.05 and ba(k) < 0]
    better = [k for k in pv if pv[k]["t_test_holm_p"] < 0.05 and ba(k) > 0]
    u = pv["lgbm_under"]["cv_delta"]
    return (("No significant balanced-accuracy difference from v2 after Holm adjustment: "
             + ", ".join(f"{mods[k]['label']} ({ba(k):+.4f})" for k in tie) + ". ") if tie else "") \
        + (("Significantly lower than v2: " + ", ".join(f"{mods[k]['label']} ({ba(k):+.4f})" for k in worse) + ". ") if worse else "") \
        + (("Significantly higher than v2: " + ", ".join(f"{mods[k]['label']} ({ba(k):+.4f})" for k in better) + ". ") if better else
           "None of the re-implemented methods beats v2 on our data. ") \
        + (f"Undersampling trades overall quality for High recall (Δ model High recall {u['high_recall']['mean']:+.4f}, "
           f"Δ macro-F1 {u['macro_f1']['mean']:+.4f}); v2 gets its High coverage from the review flag instead. "
           + str(sum(abs(ba(k)) < 0.01 for k in pv)) + f" of {len(pv)} re-implemented setups land within one point of v2's "
           "balanced accuracy despite very different model families, which fits the data ceiling noted in CLAUDE.md "
           "(most errors sit at the Anxiety Level 3/4 and 6/7 borders).")


def lr_section() -> str:
    """'Why XGBoost if logistic regression ties?' from reports/lr_vs_v2.json (src/experiments/lr_vs_v2.py)."""
    path = ROOT / "reports" / "lr_vs_v2.json"
    if not path.exists():
        return ""
    d = json.loads(path.read_text(encoding="utf-8"))
    c, nz, rv, tm, cl = d["calibration_oof"], d["noise_balanced_accuracy"], d["review_flag_oof"], d["timing_per_row"], d["clean_balanced_accuracy"]
    cal = ["| Out-of-fold, 9,350 rows | v2 XGBoost | Logistic regression |", "|---|---|---|"]
    for n in ("Low", "Medium", "High"):
        cal.append(f"| ECE (10-bin), {n} | {c['v2'][f'ece_{n}']:.4f} | {c['logreg'][f'ece_{n}']:.4f} |")
    cal.append(f"| ECE, mean of 3 classes | {c['v2']['ece_mean']:.4f} | {c['logreg']['ece_mean']:.4f} |")
    for n in ("Low", "Medium", "High"):
        cal.append(f"| Brier (one-vs-rest), {n} | {c['v2'][f'brier_{n}']:.4f} | {c['logreg'][f'brier_{n}']:.4f} |")
    cal.append(f"| Brier, mean of 3 classes | {c['v2']['brier_mean']:.4f} | {c['logreg']['brier_mean']:.4f} |")
    noise = ["| Balanced accuracy (5 folds, 10 noise seeds each) | v2 XGBoost | Logistic regression | LR − v2 (paired) |", "|---|---|---|---|",
             f"| No noise | {cl['v2']['mean']:.4f} ± {cl['v2']['std']:.4f} | {cl['logreg']['mean']:.4f} ± {cl['logreg']['std']:.4f} | — |"]
    for k, v in nz.items():
        dd = v["delta_logreg_minus_v2"]
        noise.append(f"| {k}× std | {v['v2']['mean']:.4f} ± {v['v2']['std']:.4f} | {v['logreg']['mean']:.4f} ± {v['logreg']['std']:.4f} "
                     f"| {dd['mean']:+.4f} ± {dd['std']:.4f} (t-test p {dd['t_test_p']:.2g}) |")
    v, l = rv["v2"], rv["logreg"]
    flag = ["| Review flag, out-of-fold | v2 XGBoost | Logistic regression |", "|---|---|---|",
            f"| Threshold on P(High) | {v['threshold']} (served) | {l['threshold']} (re-derived) |",
            f"| True High flagged | {v['true_high_flagged']} / {rv['true_high']} ({v['catch_rate']:.1%}) | {l['true_high_flagged']} / {rv['true_high']} ({l['catch_rate']:.1%}) |",
            f"| Patients flagged | {v['flagged']:,} of {rv['rows']:,} ({v['flagged'] / rv['rows']:.1%}) | {l['flagged']:,} of {rv['rows']:,} ({l['flagged'] / rv['rows']:.1%}) |"]
    speed = ["| One-row predict_proba | v2 XGBoost | Logistic regression |", "|---|---|---|",
             f"| Model only (preprocessed row) | {tm['v2']['model_only_ms']:.2f} ms | {tm['logreg']['model_only_ms']:.2f} ms |",
             f"| Full pipeline (raw row) | {tm['v2']['pipeline_ms']:.2f} ms | {tm['logreg']['pipeline_ms']:.2f} ms |"]
    better_noise = all(x["delta_logreg_minus_v2"]["mean"] > 0 and x["delta_logreg_minus_v2"]["t_test_p"] < 0.05 for x in nz.values())
    fewer_flags = l["flagged"] < v["flagged"] and l["true_high_flagged"] >= v["true_high_flagged"]
    high_ece_worse = c["logreg"]["ece_High"] > c["v2"]["ece_High"]
    concl = [
        f"- **Accuracy:** tie (balanced accuracy {cl['v2']['mean']:.4f} vs {cl['logreg']['mean']:.4f}; Table B).",
        f"- **Calibration:** mean Brier is about equal ({c['v2']['brier_mean']:.4f} vs {c['logreg']['brier_mean']:.4f}). "
        + (f"v2 is better calibrated for High (ECE {c['v2']['ece_High']:.4f} vs {c['logreg']['ece_High']:.4f}; Brier "
           f"{c['v2']['brier_High']:.4f} vs {c['logreg']['brier_High']:.4f}), the class the review flag uses, and for Medium (ECE "
           f"{c['v2']['ece_Medium']:.4f} vs {c['logreg']['ece_Medium']:.4f}); LR is better for Low (ECE {c['logreg']['ece_Low']:.4f} vs "
           f"{c['v2']['ece_Low']:.4f}). Mean ECE {c['v2']['ece_mean']:.4f} vs {c['logreg']['ece_mean']:.4f}. All ECEs are small "
           f"(≤ {max(max(c[m][f'ece_{n}'] for n in ('Low', 'Medium', 'High')) for m in c):.3f})."
           if high_ece_worse else "LR is as well calibrated for High as v2."),
        ("- **Noise:** LR is clearly more robust: " + "; ".join(f"{k}× std {x['delta_logreg_minus_v2']['mean']:+.4f}" for k, x in nz.items())
         + " balanced accuracy vs v2." if better_noise else "- **Noise:** no consistent advantage for LR."),
        (f"- **Review flag:** at matched coverage ({l['true_high_flagged']} of {rv['true_high']} true High), LR flags "
         f"{v['flagged'] - l['flagged']:,} fewer patients ({l['flagged']:,} vs {v['flagged']:,}), so it puts less extra load on psychologists."
         if fewer_flags else f"- **Review flag:** LR flags {l['flagged']:,} patients vs {v['flagged']:,} for v2 at matched coverage."),
        f"- **Speed:** both are well under 10 ms per row through the full pipeline ({tm['v2']['pipeline_ms']:.1f} vs {tm['logreg']['pipeline_ms']:.1f} ms); "
        "most of that is preprocessing. Timings are from this machine only.",
        "- **What this supports:** logistic regression ties v2 on accuracy and Brier, is clearly more robust to noise, flags fewer "
        "patients for the same High coverage, and is simpler to explain (one coefficient per feature). **v2's only measured advantage "
        "is slightly better calibration for High and Medium**, so LR is not as good on everything, but the measured case for XGBoost "
        "over LR is weak. "
        "Not measured here: the shortcut checks that drove the 2026-09-28 switch from Random Forest (caffeine, age), SHAP and fairness. "
        "Those would need re-running for LR before any change. **The served model is unchanged**; this is evidence for a supervisor "
        "decision, not a decision.",
    ]
    return f"""
## Why XGBoost if logistic regression ties?

Script: `src/experiments/lr_vs_v2.py` (`reports/lr_vs_v2.json`). Same 5 folds; out-of-fold probabilities; v2 re-run reproduces
the ablation fold scores (guard). LR = scikit-learn defaults (`max_iter=1000`), same preprocessing as v2. Noise = Gaussian on all
9 numeric features of the held-out fold, scaled to that feature's training-fold std, identical for both models. LR's review
threshold is re-derived (the highest threshold catching at least v2's out-of-fold share at 0.025); v2 keeps the served 0.025.

{chr(10).join(cal)}

{chr(10).join(noise)}

{chr(10).join(flag)}

{chr(10).join(speed)}

{d['timing_note'].capitalize()}.

{chr(10).join(concl)}
"""


def write_markdown(r: dict) -> None:
    s, pv, mods = r["summary"], r["paired_vs_v2"], r["models"]
    fmt = lambda d: f"{d['mean']:.4f} ± {d['std']:.4f}"
    lit = ["| Study | Their data | Method and validation | Target | Their reported numbers |", "|---|---|---|---|---|"]
    lit += [f"| {' | '.join(row)} |" for row in LITERATURE]
    tb = ["| Model | Setup from | Balanced accuracy | Macro-F1 | Model High recall |", "|---|---|---|---|---|"]
    tb += [f"| {m['label']} | {m['source']} | " + " | ".join(fmt(s[k][x]) for x in METRICS) + " |" for k, m in mods.items()]
    pr = ["| Model − v2 | Δ balanced acc. | Δ macro-F1 | Δ model High recall | t-test p: raw / Holm | "
          "McNemar p (OOF): raw / Holm | Only v2 right / only model right |", "|---|---|---|---|---|---|---|"]
    for k, p in pv.items():
        d, mc = p["cv_delta"], p["mcnemar_oof_vs_v2"]
        pr.append(f"| {mods[k]['label']} | " + " | ".join(f"{d[x]['mean']:+.4f} ± {d[x]['std']:.4f}" for x in METRICS)
                  + f" | {p['t_test_balanced_accuracy_p']:.3f} / {p['t_test_holm_p']:.3f} | {mc['p_value']:.3g} / {p['mcnemar_holm_p']:.3g}"
                  f" | {mc['only_first_correct']} / {mc['only_second_correct']} |")
    under = mods["lgbm_under"]["train_rows_per_fold"]

    REPORT_MD.write_text(f"""# Comparison with published methods

Script: `src/experiments/sota_baselines.py` (results also in `reports/sota_baselines.json`). **The test set was not used; no
served file or threshold was changed.** Seed 42.

## How to read this

**Our dataset is very likely synthetic.** It appears to come from the Kaggle "Social Anxiety Dataset" [8]. That page calls it
a "synthetic dataset", although its disclaimer also says it was "compiled from real-world survey responses". Our own EDA found
near-uniform demographics, no missing values and templated recommendation text. The studies in Table A use other populations,
targets (mostly binary), instruments and validation schemes, and most use real survey or sensor data. **Their numbers are context,
not a ranking**, and nothing here should be read as MindCare beating or trailing any of them. Table B is the only like-for-like
comparison: the published *methods* re-run on *our* data, folds and target.

## Table A: the literature (their data, their numbers; not directly comparable)

Only facts read on each paper's own page. Where a page did not give a number, none is shown.

{chr(10).join(lit)}

Two patterns from these pages matter here. First, the near-perfect WESAD results [6, 7] put the same subjects in training and
test; under leave-one-subject-out, [7] reports per-subject accuracy as low as 0.31. Second, several papers' abstracts disagree
with their own tables [2, 3]. Neither pattern is a reason to doubt our own results; they are reasons not to rank against them.

## Has anyone published on this exact dataset?

- **One peer-reviewed paper found:** Nishwa, Abbas & Lee (2026) [1] analyse the Kaggle dataset by Zhang Chenyuan (2024) at
  kaggle.com/datasets/natezhang123/social-anxiety-dataset, with 11,000 participants. They bin Anxiety Level into the same
  1-3 / 4-6 / 7-10 groups for descriptive statistics, but model it as a 1-10 regression and **give no numeric model scores**.
  So no published number exists to compare with ours. The paper does not say whether the data are real or synthetic.
- **Kaggle page [8]:** "Zhang Chenyuan and 2 collaborators", CC0, file `enhanced_anxiety_dataset.csv`, 19 columns. The Data Card
  describes it as synthetic (see above). The Code tab lists 24 notebooks; we did not review them, and they are not peer-reviewed.
- **Link to our file:** the 10 column names and the first three rows shown in the Kaggle preview match the first 10 columns and
  first three rows of `data/raw/mindcare_dataset_final.csv`. Our file has 23 columns. Its first 19 are the features the Data
  Card lists plus Anxiety Level, which fits the 19-column Kaggle file; the other four are Severity, Exercises, Sleep_Schedule and
  Nutrition. We checked only the preview, not the full file.
- **The target is social anxiety:** the Data Card says `Anxiety Level (1-10)` "Quantifies the individual's social anxiety
  intensity". Of the Table A studies, none uses a social-anxiety target; they use GAD-7, PHQ-9 or stress measures.
- A search on the exact column names ("Anxiety Level (1-10)", "Therapy Sessions (per month)") found only [1].

## Table B: like-for-like results on our data

The same 5 folds as `src/experiments/ablation_study.py`: the {r['rows_cv']:,} train + validation rows, stratified on the 3-class
label, shuffled, seed 42, scaling and one-hot encoding fitted inside each fold, 11 v2 features. Mean ± std over the 5 folds.
"Model High recall" means the predicted class is High; the review flag is not applied to any model here. v2 re-run here
reproduces the per-fold scores in `reports/ablation_study.json` exactly (guard in the script).

{chr(10).join(tb)}

Settings are the ones each paper states; anything not stated is the library default. Vu et al. [5] tuned LightGBM by grid search
but do not list the chosen values on the page, so LightGBM uses defaults. Their random undersampling was applied inside each
training fold, cutting every class down to the High count ({', '.join(f'{n:,}' for n in under)} training rows per fold). Qasrawi
et al. [2] used Orange; anything Orange sets differently from scikit-learn's defaults is not reproduced.

**Paired comparison with v2** (per-fold difference, model − v2; same folds, so the differences are paired). The t-test is on the
5 fold balanced accuracies; McNemar is exact, on which of the {r['rows_cv']:,} out-of-fold predictions each model gets right. Folds
share training data, so p-values are approximate; with 5 folds the t-test has little power, so "not significant" is not proof
of no difference.

{chr(10).join(pr)}

**Reading.** {reading(pv, mods)}
{lr_section()}
Libraries: {', '.join(f'{k} {v}' for k, v in r['library_versions'].items())}.

## Sources (pages actually opened)

{chr(10).join(f'- {x}' for x in SOURCES)}

Searched but not used: Priya, Garg & Tiwari (2020, *Procedia Comput. Sci.*): the ScienceDirect page asked for a CAPTCHA, so
it was not read. Garg et al. (2021, WESAD with RF): the PDF could not be opened as a page. Their numbers appear only in other
papers' summaries, so they are left out.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    if "--report-only" in sys.argv:
        write_markdown(json.loads(REPORT_JSON.read_text(encoding="utf-8")))
    else:
        main()
