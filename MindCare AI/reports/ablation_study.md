# Ablation study, PCA check and significance tests: served 11-feature v2 XGBoost

Script: `src/experiments/ablation_study.py`. **The test set was not used; no served file or threshold changed.** Every variant
was re-run here. Validation split = fitted on the 7,700 training rows, scored on the 1,650 validation rows. Paired CV = the
9,350 train + validation rows, 5-fold stratified on the 3-class label, shuffled, seed 42, the same folds for every
variant, preprocessing fitted inside each fold. Δ = variant − v2. "Model High recall" = predicted class High.

Guard: the served files reproduce balanced accuracy 0.8055, 411 flagged,
158/165 true High flagged; v2 retrained here reproduces validation balanced
accuracy 0.8055 (macro-F1 0.8148, model High recall 0.8970).

## 1. Ablation table

| Decision (variant − v2) | Val Δ macro-F1 | Val Δ balanced acc. | Val Δ model High recall | CV Δ macro-F1 | CV Δ balanced acc. | CV Δ model High recall | Earlier report |
|---|---|---|---|---|---|---|---|
| 17 features instead of 11 | +0.0004 | +0.0004 | +0.0000 | -0.0010 ± 0.0027 | -0.0006 ± 0.0024 | +0.0000 ± 0.0000 | different model/config: balanced_accuracy -0.0028, macro_f1 -0.0027, high_recall -0.0000 (reports/feature_reduction_3class.md (tuned Random Forest, validation split)) |
| Age removed (10 features) | +0.0014 | +0.0023 | +0.0000 | -0.0000 ± 0.0010 | +0.0003 ± 0.0008 | +0.0000 ± 0.0000 | different model/config: balanced_accuracy +0.0022, macro_f1 +0.0022, high_recall +0.0000 (reports/feature_addition_age_3class.md (tuned Random Forest, validation split)) |
| Sweating Level kept (12 features) | +0.0023 | +0.0023 | +0.0000 | -0.0001 ± 0.0008 | -0.0000 ± 0.0008 | +0.0000 ± 0.0000 | matches: balanced_accuracy +0.0023, macro_f1 +0.0023, high_recall +0.0000 (reports/feature_reduction_sweatlevel_3class.json (same XGBoost, validation split)) |
| Caffeine dropped (10 features) | -0.0002 | -0.0002 | +0.0000 | -0.0040 ± 0.0028 | -0.0033 ± 0.0023 | -0.0031 ± 0.0046 | different model/config: balanced_accuracy -0.0052, macro_f1 -0.0074, high_recall -0.0000 (reports/feature_reduction_caffeine_3class.md (tuned Random Forest, validation split)) |
| Derived features added (16 features) | +0.0040 | +0.0017 | -0.0061 | -0.0032 ± 0.0013 | -0.0026 ± 0.0022 | -0.0010 ± 0.0043 | matches: CV balanced_accuracy -0.0026, macro_f1 -0.0032, high_recall -0.0010 (reports/derived_features_11feature.json (branch of PR #57; same XGBoost, same folds)) |
| Balanced class weights | -0.0131 | -0.0022 | +0.0061 | -0.0144 ± 0.0041 | -0.0034 ± 0.0032 | +0.0103 ± 0.0052 | — |
| Isotonic calibration | -0.0007 | -0.0029 | -0.0061 | +0.0011 ± 0.0034 | +0.0006 ± 0.0029 | -0.0021 ± 0.0046 | pooled out-of-fold: balanced_accuracy +0.0006, macro_f1 +0.0011, high_recall -0.0021 (reports/calibration_review_flag_11feature_v2.json (branch of PR #57; pooled out-of-fold, not a fold mean)) |
| Random Forest instead of XGBoost | +0.0052 | +0.0024 | +0.0000 | +0.0003 ± 0.0034 | -0.0014 ± 0.0034 | -0.0010 ± 0.0057 | different model/config: balanced_accuracy -0.0004, macro_f1 +0.0024 (reports/model_comparison_12feature.json (12 features, validation split)) |
| MLP instead of XGBoost | +0.0044 | +0.0020 | -0.0061 | -0.0025 ± 0.0051 | -0.0007 ± 0.0051 | +0.0021 ± 0.0119 | not comparable (reports/advanced_models_3class.md (17 features): MLP 0.8041 vs XGBoost 0.8074 balanced accuracy) |
| Therapy Sessions removed (10 features) | -0.0074 | -0.0087 | -0.0242 | -0.0090 ± 0.0040 | -0.0081 ± 0.0060 | -0.0114 ± 0.0134 | — |

**No re-run differs from an earlier report that used the same configuration.** Rows marked "different model/config" compare against earlier Random Forest or 12/17-feature runs and are shown for reference only.

## 2. Significance

Paired t-test on the 5 fold balanced accuracies, and an exact McNemar test on which validation patients each model gets right.
**The CV folds share training data, so they are not independent and these p-values are approximate** (they tend to be too small).
With 5 folds the t-test has little power, so "no clear evidence" is not proof of no difference.

| Variant vs v2 | Paired CV t-test p: raw / Holm | McNemar p (validation): raw / Holm | Only v2 right / only variant right | Reading (Holm-adjusted) |
|---|---|---|---|---|
| 17 features instead of 11 | 0.612 / 1.000 | 1.000 / 1.000 | 8 / 9 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Age removed (10 features) | 0.443 / 1.000 | 0.383 / 1.000 | 8 / 13 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Sweating Level kept (12 features) | 0.981 / 1.000 | 0.227 / 1.000 | 3 / 8 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Caffeine dropped (10 features) | 0.033 / 0.328 | 1.000 / 1.000 | 29 / 29 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Derived features added (16 features) | 0.061 / 0.491 | 0.382 / 1.000 | 20 / 27 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Balanced class weights | 0.076 / 0.529 | 0.243 / 1.000 | 28 / 19 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Isotonic calibration | 0.661 / 1.000 | 0.541 / 1.000 | 14 / 10 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Random Forest instead of XGBoost | 0.409 / 1.000 | 0.828 / 1.000 | 41 / 44 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| MLP instead of XGBoost | 0.787 / 1.000 | 0.322 / 1.000 | 21 / 29 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Therapy Sessions removed (10 features) | 0.039 / 0.352 | 0.630 / 1.000 | 37 / 32 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |

**Multiple comparisons.** 10 variants are each tested against v2, so the p-values are adjusted with Holm-Bonferroni (each test family separately). Raw t-test p < 0.05: Caffeine dropped (10 features) (raw 0.033, Holm 0.328), Therapy Sessions removed (10 features) (raw 0.039, Holm 0.352). These do not survive adjustment, so they are best described as **small, borderline-significant costs**: Caffeine dropped (10 features) (CV Δ balanced acc. -0.0033), Therapy Sessions removed (10 features) (CV Δ balanced acc. -0.0081). No McNemar comparison is significant after adjustment (smallest Holm p 1.000).

**Model family (all on the same 11 features):**

| Pair | CV mean Δ balanced acc. (first − second) | Paired CV t-test p: raw / Holm | McNemar p: raw / Holm | Only first / only second right | Reading (Holm-adjusted) |
|---|---|---|---|---|---|
| XGBoost (v2) vs Random Forest | +0.0014 | 0.409 / 1.000 | 0.828 / 1.000 | 41 / 44 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| XGBoost (v2) vs MLP | +0.0007 | 0.787 / 1.000 | 0.322 / 0.967 | 21 / 29 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |
| Random Forest vs MLP | -0.0007 | 0.750 / 1.000 | 0.679 / 1.000 | 44 / 49 | CV: no clear evidence of a difference in balanced accuracy (p ≥ 0.05); validation: no clear evidence of a difference in errors (p ≥ 0.05) |

## 3. Therapy Sessions removed (11 → 10 features): detail

Out-of-fold over 9,350 rows. The variant gets **its own review threshold**, re-derived to match v2's coverage target
(the highest threshold still catching ≥ 96.2% of true High, v2's out-of-fold catch share at 0.025): **0.027**.
It flags **2,359** of 9,350 patients (25.2%), against 2,361
(25.3%) for v2 at 0.025.

| True-High patients | Rows | v2: predicted High | v2: flagged (0.025) | Therapy removed: predicted High | Therapy removed: flagged (own threshold) |
|---|---|---|---|---|---|
| Therapy ≤ 2 | 54 | 0 | 33 | 1 | 35 |
| Therapy > 2 | 914 | 849 | 898 | 837 | 896 |

**SHAP for the Therapy-removed model** (High class, exact `pred_contribs`, validation rows; Occupation and Family History summed back):

| Rank | Feature | Mean \|SHAP\| (High) | Share |
|---|---|---|---|
| 1 | Stress Level (1-10) | 1.6457 | 42.5% |
| 2 | Sleep Hours | 0.6852 | 17.7% |
| 3 | Caffeine Intake (mg/day) | 0.5145 | 13.3% |
| 4 | Physical Activity (hrs/week) | 0.3218 | 8.3% |
| 5 | Family History of Anxiety | 0.1741 | 4.5% |
| 6 | Diet Quality (1-10) | 0.1620 | 4.2% |
| 7 | Heart Rate (bpm) | 0.1527 | 3.9% |
| 8 | Age | 0.1407 | 3.6% |
| 9 | Breathing Rate (breaths/min) | 0.0494 | 1.3% |
| 10 | Occupation | 0.0229 | 0.6% |

**Stress forced to 8 / 9 / 10, by the patient's former therapy band** (validation rows; models fitted on the training split):

| Former therapy band | Rows | Predicted-High share, Stress 8 / 9 / 10: Therapy removed | Same: v2 |
|---|---|---|---|
| 0-2 | 1008 | 0.0129 / 0.0129 / 0.0149 | 0.0000 / 0.0000 / 0.0000 |
| 3-5 | 486 | 0.0988 / 0.0988 / 0.1049 | 0.1008 / 0.1049 / 0.1111 |
| 6+ | 156 | 0.6410 / 0.6474 / 0.6538 | 0.6731 / 0.6859 / 0.6859 |

## 4. PCA check (evidence for the report only)

v2's XGBoost settings trained on PCA components of the preprocessed features, PCA fitted inside each fold on training rows only.

| Variant | Components per fold | Val Δ macro-F1 | Val Δ balanced acc. | Val Δ model High recall | CV Δ macro-F1 | CV Δ balanced acc. | CV Δ model High recall |
|---|---|---|---|---|---|---|---|
| PCA, 95% of variance | 15, 15, 15, 15, 15 | +0.0076 | +0.0043 | +0.0000 | -0.0035 ± 0.0053 | -0.0039 ± 0.0056 | -0.0062 ± 0.0134 |
| PCA, 99% of variance | 21, 21, 21, 21, 21 | +0.0068 | +0.0034 | +0.0000 | -0.0043 ± 0.0066 | -0.0048 ± 0.0072 | -0.0073 ± 0.0154 |

**What PCA loses:** each component mixes all 24 preprocessed columns, so SHAP can only rank components, not real features.
There is no per-feature explanation for the psychologist, no direction check for Sleep, Caffeine, Activity or Diet, and no
feature-level driver for the recommendation engine. The input-validation and alert rules would still work on raw inputs, but
the model's reasons could no longer be tied to them.

## 5. Therapy Sessions decision (for the supervisor; no decision is made here)

- **Overall accuracy cost of removing it:** CV Δ balanced accuracy -0.0081 ± 0.0060,
  Δ macro-F1 -0.0090, Δ model High recall -0.0114 (validation: -0.0087 /
  -0.0074 / -0.0242); paired t-test p = 0.039 raw, 0.352 Holm-adjusted.
- **Detection of low-therapy High patients:** true-High patients with ≤ 2 sessions are predicted High 0 of
  54 times by v2 and 1 of 54 without Therapy; the review flag catches
  33 of 54 (v2, 0.025) vs 35 of 54 (own threshold 0.027),
  with 2,361 (v2) vs 2,359 (Therapy removed) patients flagged overall. Without Therapy, the top High drivers are Stress Level (1-10), Sleep Hours, Caffeine Intake (mg/day).
- **Reverse-causality risk of keeping it:** in this dataset therapy count most likely reflects severity (more severe patients
  attend more sessions), so a new help-seeker with high stress but no therapy history is under-called by v2.
- **Trade-off:** Removing it costs overall accuracy and **does not** fix the low-therapy gap: +1 predicted High and +2 flagged among the 54 low-therapy High patients. Dropping the proxy alone does not make the model see them. Keeping it keeps the higher accuracy but leaves the reverse-causality gap to the review flag and the psychologist.
- **What this means:** removing Therapy does not fix the low-therapy gap (1/54 predicted High,
  35/54 flagged), so the gap reflects the data, not the model's use of the feature; mitigation is
  psychologist review and the documented limitation (model card Known Limitations item 16).
- Very likely synthetic data; small low-therapy High sample (54 patients).

Libraries: python 3.13.13, xgboost 3.4.1, scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.5.
