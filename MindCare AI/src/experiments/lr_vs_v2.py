"""Logistic regression vs the served v2 XGBoost beyond accuracy: calibration, noise, review flag, speed.

Logistic regression tied v2 on balanced accuracy in reports/sota_comparison.md, so this checks the other properties
the 2026-09-28 model choice relied on. CV only, on the same 5 folds as src/experiments/ablation_study.py (the 9,350
train + validation rows; the test set is never loaded). No served file or threshold is read or changed.

- Calibration: out-of-fold probabilities; per-class 10-bin ECE (same ece() as compare_models_12feature.py) and
  per-class one-vs-rest Brier, plus their mean over the 3 classes.
- Noise: Gaussian noise on all 9 numeric features of the held-out fold, k x that feature's training-fold std,
  k = 0.25 and 1.0, 10 seeds per fold; the same noise for both models. Paired difference per fold (mean over seeds).
- Review flag: v2 at P(High) >= 0.025 (the served threshold); LR gets its own threshold, the highest one whose
  out-of-fold catch share of true High is >= v2's (same rule as the ablation study's Therapy check).
- Speed: one-row predict_proba, mean of 500 calls after 50 warm-up calls, model fitted on fold 1's training rows;
  model only (preprocessed row, as in compare_models_12feature.py) and full pipeline (raw row).

Run from MindCare AI/: python -m src.experiments.lr_vs_v2
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, brier_score_loss
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level
from src.evaluation.compare_models_12feature import ece
from src.experiments.ablation_study import (DATA_PATH, FOLDS, HIGH, REVIEW_THRESHOLD, ROOT, SEED, SPLITS_PATH,
                                            TUNING_12, V2_CATEGORICAL, V2_NUMERIC)
from src.experiments.sota_baselines import pipeline

REPORT_JSON = ROOT / "reports" / "lr_vs_v2.json"
CLASSES = ["Low", "Medium", "High"]
NOISE_LEVELS = (0.25, 1.0)
NOISE_SEEDS = range(10)
TIMING_CALLS, WARMUP = 500, 50


def own_threshold(p_high: np.ndarray, is_high: np.ndarray, target_share: float) -> float:
    hp = np.sort(p_high[is_high])
    t = float(hp[int(np.floor((1 - target_share) * len(hp) + 1e-9))])
    t = float(np.floor(t * 1e4) / 1e4)
    assert (p_high[is_high] >= t).mean() >= target_share
    return t


def per_row_ms(fn, row) -> float:
    for _ in range(WARMUP):
        fn(row)
    start = time.perf_counter()
    for _ in range(TIMING_CALLS):
        fn(row)
    return (time.perf_counter() - start) / TIMING_CALLS * 1000


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as s:
        idx = np.concatenate([s["train_original_idx"], s["val_original_idx"]])  # no test rows
    df = raw.iloc[idx].reset_index(drop=True)
    y = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    x = df[V2_NUMERIC + V2_CATEGORICAL]
    folds = list(StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y))
    xgb_params = json.loads(TUNING_12.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]
    makers = {
        "v2": lambda: XGBClassifier(**xgb_params, objective="multi:softprob", eval_metric="mlogloss",
                                    random_state=SEED, n_jobs=-1),
        "logreg": lambda: LogisticRegression(max_iter=1000),
    }

    oof = {k: np.zeros((len(df), 3)) for k in makers}
    clean = {k: [] for k in makers}
    noisy = {k: {str(n): [] for n in NOISE_LEVELS} for k in makers}  # per fold: mean over seeds
    timing = {}
    for f, (tr, te) in enumerate(folds):
        fitted = {k: pipeline(make()).fit(x.iloc[tr], y[tr]) for k, make in makers.items()}
        x_te = x.iloc[te]
        std = x.iloc[tr][V2_NUMERIC].std().to_numpy()
        for k, m in fitted.items():
            oof[k][te] = m.predict_proba(x_te)
            clean[k].append(float(balanced_accuracy_score(y[te], oof[k][te].argmax(1))))
        for n in NOISE_LEVELS:
            per_seed = {k: [] for k in makers}
            for s in NOISE_SEEDS:
                delta = np.random.default_rng(1000 * f + s).normal(size=(len(te), len(V2_NUMERIC))) * std * n
                frame = x_te.copy()
                frame[V2_NUMERIC] = frame[V2_NUMERIC].to_numpy() + delta
                for k, m in fitted.items():
                    per_seed[k].append(float(balanced_accuracy_score(y[te], m.predict(frame))))
            for k in makers:
                noisy[k][str(n)].append(float(np.mean(per_seed[k])))
        if f == 0:
            raw_row = x_te.iloc[:1]
            for k, m in fitted.items():
                pre_row = m.named_steps["pre"].transform(raw_row)
                timing[k] = {"model_only_ms": per_row_ms(m.named_steps["model"].predict_proba, pre_row),
                             "pipeline_ms": per_row_ms(m.predict_proba, raw_row)}
        print(f"fold {f + 1}/{FOLDS} done", flush=True)

    ref = [f["balanced_accuracy"] for f in json.loads((ROOT / "reports" / "ablation_study.json").read_text(encoding="utf-8"))["cv_scores"]["v2"]]
    if any(abs(a - b) > 1e-9 for a, b in zip(clean["v2"], ref)):
        raise SystemExit(f"STOP: v2 does not reproduce reports/ablation_study.json fold balanced accuracy: {clean['v2']}")
    print("guard: v2 reproduces reports/ablation_study.json fold balanced accuracy")

    calibration = {}
    for k, p in oof.items():
        c = {f"ece_{n}": ece((y == i).astype(int), p[:, i]) for i, n in enumerate(CLASSES)}
        c.update({f"brier_{n}": float(brier_score_loss((y == i).astype(int), p[:, i])) for i, n in enumerate(CLASSES)})
        c["ece_mean"] = float(np.mean([c[f"ece_{n}"] for n in CLASSES]))
        c["brier_mean"] = float(np.mean([c[f"brier_{n}"] for n in CLASSES]))
        calibration[k] = c

    is_high = y == HIGH
    v2_flag = oof["v2"][:, HIGH] >= REVIEW_THRESHOLD
    share = float(v2_flag[is_high].mean())
    t_lr = own_threshold(oof["logreg"][:, HIGH], is_high, share)
    lr_flag = oof["logreg"][:, HIGH] >= t_lr
    review = {
        "v2": {"threshold": REVIEW_THRESHOLD, "flagged": int(v2_flag.sum()), "true_high_flagged": int(v2_flag[is_high].sum()),
               "catch_rate": share, "true_high_unflagged": int((is_high & ~v2_flag).sum())},
        "logreg": {"threshold": t_lr, "flagged": int(lr_flag.sum()), "true_high_flagged": int(lr_flag[is_high].sum()),
                   "catch_rate": float(lr_flag[is_high].mean()), "true_high_unflagged": int((is_high & ~lr_flag).sum())},
        "true_high": int(is_high.sum()), "rows": len(df),
    }
    noise = {}
    for n in map(str, NOISE_LEVELS):
        d = np.array(noisy["logreg"][n]) - np.array(noisy["v2"][n])
        noise[n] = {k: {"mean": float(np.mean(noisy[k][n])), "std": float(np.std(noisy[k][n], ddof=1))} for k in makers}
        noise[n]["delta_logreg_minus_v2"] = {"mean": float(d.mean()), "std": float(d.std(ddof=1)),
                                             "t_test_p": float(ttest_rel(noisy["logreg"][n], noisy["v2"][n]).pvalue)}
    result = {
        "rows_cv": len(df), "folds": FOLDS, "seed": SEED, "test_set_used": False,
        "clean_balanced_accuracy": {k: {"mean": float(np.mean(v)), "std": float(np.std(v, ddof=1))} for k, v in clean.items()},
        "calibration_oof": calibration, "noise_balanced_accuracy": noise, "noise_per_fold": noisy,
        "review_flag_oof": review, "timing_per_row": timing,
        "timing_note": f"mean of {TIMING_CALLS} one-row calls after {WARMUP} warm-up calls, this machine, fold-1 models",
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: result[k] for k in ("clean_balanced_accuracy", "calibration_oof", "noise_balanced_accuracy",
                                             "review_flag_oof", "timing_per_row")}, indent=1))
    print(f"wrote {REPORT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
