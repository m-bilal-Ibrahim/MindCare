"""Per-occupation gaps for the served v2 XGBoost, out-of-fold: is Scientist the only occupation affected?

Train + validation rows only (the test set is never loaded); same 5 folds as src/experiments/ablation_study.py; v2's
tuned settings; served 0.025 review threshold (read-only copy). For the true-High patients of each of the 13
occupations vs all other true-High patients:
- model High recall (predicted class High) and review-flag catch rate (P(High) >= 0.025);
- gap = occupation - all others; bootstrap 95% CI (2,000 resamples, seed 42, patients resampled within each group);
- two-sided Fisher exact test, Holm-adjusted across the 13 occupations (separately for recall and for catch rate).
Guard: Scientist's counts must match reports/lr_candidate_evaluation.json (56/75 predicted High, 70/75 flagged).

Run from MindCare AI/: python -m src.experiments.occupation_gap_v2
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from sklearn.model_selection import StratifiedKFold

from src.build_3class_target import bin_anxiety_level
from src.experiments.ablation_study import (DATA_PATH, FOLDS, HIGH, REVIEW_THRESHOLD, ROOT, SEED, SPLITS_PATH,
                                            TUNING_12, V2_CATEGORICAL, V2_NUMERIC, holm)
from src.experiments.lr_candidate_evaluation import v2_model
from src.experiments.sota_baselines import pipeline

REPORT_JSON = ROOT / "reports" / "occupation_gap_v2.json"
REPORT_MD = ROOT / "reports" / "occupation_gap_v2.md"
LR_JSON = ROOT / "reports" / "lr_candidate_evaluation.json"
RESAMPLES = 2000
METRIC_LABEL = {"recall": "model High recall", "catch": "review-flag catch rate (0.025)"}


def gap_stats(hit: np.ndarray, in_group: np.ndarray, rng: np.random.Generator) -> dict:
    a, b = hit[in_group].astype(float), hit[~in_group].astype(float)
    boots = np.array([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(RESAMPLES)])
    _, p = fisher_exact([[int(a.sum()), int(len(a) - a.sum())], [int(b.sum()), int(len(b) - b.sum())]])
    return {"hits": int(a.sum()), "n": int(len(a)), "rate": float(a.mean()), "others_hits": int(b.sum()),
            "others_n": int(len(b)), "others_rate": float(b.mean()), "gap": float(a.mean() - b.mean()),
            "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))], "fisher_p": float(p)}


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    with np.load(SPLITS_PATH) as s:
        df = raw.iloc[np.concatenate([s["train_original_idx"], s["val_original_idx"]])].reset_index(drop=True)  # no test rows
    y = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    x = df[V2_NUMERIC + V2_CATEGORICAL]
    params = json.loads(TUNING_12.read_text(encoding="utf-8"))["models"]["xgboost"]["best_params"]
    proba = np.zeros((len(df), 3))
    for tr, te in StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(df, y):
        proba[te] = pipeline(v2_model(params)).fit(x.iloc[tr], y[tr]).predict_proba(x.iloc[te])

    is_h = y == HIGH
    occ = df.loc[is_h, "Occupation"].to_numpy()
    hits = {"recall": proba[is_h].argmax(1) == HIGH, "catch": proba[is_h, HIGH] >= REVIEW_THRESHOLD}
    rng = np.random.default_rng(SEED)
    rows = {o: {m: gap_stats(h, occ == o, rng) for m, h in hits.items()} for o in sorted(set(occ))}
    for m in hits:
        adj = holm({o: rows[o][m]["fisher_p"] for o in rows})
        for o in rows:
            rows[o][m]["holm_p"] = adj[o]

    ref = json.loads(LR_JSON.read_text(encoding="utf-8"))["fairness_scientist"]["oof"]["v2"]["scientist"]
    sci = rows["Scientist"]
    got = {"rows": sci["recall"]["n"], "predicted_high": sci["recall"]["hits"], "flagged": sci["catch"]["hits"]}
    if got != ref:
        raise SystemExit(f"STOP: Scientist counts {got} differ from reports/lr_candidate_evaluation.json {ref}")
    print("guard: Scientist counts match reports/lr_candidate_evaluation.json")

    result = {"rows_cv": len(df), "true_high": int(is_h.sum()), "occupations": len(rows), "seed": SEED,
              "resamples": RESAMPLES, "threshold": REVIEW_THRESHOLD, "test_set_used": False, "by_occupation": rows}
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_markdown(result)
    for o, r in rows.items():
        print(f"{o:12s} recall {r['recall']['hits']}/{r['recall']['n']} gap {r['recall']['gap']:+.3f} holm {r['recall']['holm_p']:.3g} | "
              f"catch {r['catch']['hits']}/{r['catch']['n']} gap {r['catch']['gap']:+.3f} holm {r['catch']['holm_p']:.3g}")
    print("wrote", REPORT_MD.relative_to(ROOT))


def write_markdown(r: dict) -> None:
    occ = r["by_occupation"]
    tables = {}
    for m in ("recall", "catch"):
        t = [f"| Occupation | True High | {METRIC_LABEL[m].capitalize()} | All others | Gap | Bootstrap 95% CI | Fisher p | Holm p (13) |",
             "|---|---|---|---|---|---|---|---|"]
        for o, v in sorted(occ.items(), key=lambda kv: kv[1][m]["gap"]):
            s = v[m]
            bold = "**" if s["holm_p"] < 0.05 else ""
            t.append(f"| {bold}{o}{bold} | {s['n']} | {s['hits']}/{s['n']} ({s['rate']:.1%}) | {s['others_rate']:.1%} | {s['gap']:+.3f} | "
                     f"{s['ci95'][0]:+.3f} to {s['ci95'][1]:+.3f} | {s['fisher_p']:.3g} | {bold}{s['holm_p']:.3g}{bold} |")
        tables[m] = "\n".join(t)
    sig = {m: [o for o, v in occ.items() if v[m]["holm_p"] < 0.05] for m in ("recall", "catch")}
    raw_sig = {m: [o for o, v in occ.items() if v[m]["fisher_p"] < 0.05] for m in ("recall", "catch")}
    sci = occ["Scientist"]
    fmt = lambda xs: ", ".join(xs) if xs else "none"
    REPORT_MD.write_text(f"""# Occupation gaps for the served v2 XGBoost (out-of-fold)

Script: `src/experiments/occupation_gap_v2.py` (`reports/occupation_gap_v2.json`). **The test set was not used; no served file
or threshold changed.** Out-of-fold over the {r['rows_cv']:,} train + validation rows (same 5 folds as the ablation study, v2's
tuned settings), {r['true_high']} true-High patients. For each of the {r['occupations']} occupations, its true-High patients
are compared with all other true-High patients. Gap = occupation − all others. Bootstrap: {r['resamples']:,} resamples, seed
{r['seed']}, patients resampled within each group. Fisher exact is two-sided; Holm adjustment is across the {r['occupations']}
occupations, separately for each metric. Bold = Holm p < 0.05. Guard: Scientist's counts match
`reports/lr_candidate_evaluation.json`.

## Model High recall (predicted class = High)

{tables['recall']}

## Review-flag catch rate (P(High) ≥ {r['threshold']})

{tables['catch']}

## Reading

- **Model High recall:** significant after Holm: {fmt(sig['recall'])}. Raw p < 0.05: {fmt(raw_sig['recall'])}.
- **Review-flag catch rate:** significant after Holm: {fmt(sig['catch'])}. Raw p < 0.05: {fmt(raw_sig['catch'])}.
- **Scientist:** model High recall {sci['recall']['hits']}/{sci['recall']['n']} ({sci['recall']['rate']:.1%}) vs {sci['recall']['others_rate']:.1%},
  gap {sci['recall']['gap']:+.3f} (95% CI {sci['recall']['ci95'][0]:+.3f} to {sci['recall']['ci95'][1]:+.3f}), Holm p {sci['recall']['holm_p']:.3g}. The review flag
  catches {sci['catch']['hits']}/{sci['catch']['n']} ({sci['catch']['rate']:.1%}) vs {sci['catch']['others_rate']:.1%} (Holm p {sci['catch']['holm_p']:.3g}).
- Occupation has no relationship with Stress Level in this dataset (ANOVA p = 0.93, CLAUDE.md), and the data are very likely
  synthetic. These tests show whether a gap is larger than sampling noise; they do not explain it. Out-of-fold predictions come
  from five models.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
