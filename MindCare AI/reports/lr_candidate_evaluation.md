# Logistic regression as a candidate to replace v2

Script: `src/experiments/lr_candidate_evaluation.py` (`reports/lr_candidate_evaluation.json`). **The test set was not used; no
served file or threshold changed.** Seed 42. 9,350 train + validation rows; the same 5 outer folds as the v2 nested CV
and the ablation study. Very likely synthetic data, and the target is a self-rated social anxiety level, so none of this is
clinical validation.

**Guards (all passed):** v2 retrained on the training split reproduces the served validation numbers
(0.8055, 411 flagged, 158/165 true High);
v2's caffeine counterfactual matches `reports/shap_v2.json`; v2's low-caffeine (23 / 0 / 12) and low-therapy (54 / 0 / 33)
out-of-fold numbers match `reports/shap_v2.md` and `reports/robustness_v2.md`.

**Thresholds.** v2 uses the served 0.025 throughout. LR has no served threshold, so it gets the rule that produced 0.025: the
highest threshold flagging at least 158/165 true High on the validation split (**0.0148**), and out-of-fold
the highest threshold catching at least v2's out-of-fold share at 0.025 (96.2%): **0.0171**.
In nested CV each fold derives its own threshold for both models.

**LR settings for sections 2-3:** tuned on the 7,700 training rows (GridSearchCV, cv=5, balanced accuracy; C in
['0.001', '0.01', '0.1', '1', '10', '100'], class_weight none/balanced): **C = 10, class_weight = none** (inner CV 0.8117).

## Side by side

| Check | v2 XGBoost | Logistic regression |
|---|---|---|
| Nested CV balanced accuracy (all ages) | 0.8121 ± 0.0060 | 0.8122 ± 0.0041 |
| Nested CV model High recall | 0.8812 ± 0.0092 | 0.8791 ± 0.0202 |
| Nested CV flag catch rate / flag volume | 0.9546 / 0.2425 | 0.9608 / 0.2327 |
| Caffeine ≤ 200, true High, out-of-fold (n=23) | 0/23 predicted High, 12/23 flagged | 1/23 predicted High, 9/23 flagged |
| Caffeine set to 0, validation true High (of 165) | 128 predicted High, 154 flagged | 101 predicted High, 150 flagged |
| Mean P(High), true High under 50 set to age 49 → 50 → 55 (n=161) | 0.884 → 0.881 → 0.862 | 0.863 → 0.862 → 0.855 |
| Scientist − other: model High recall gap, out-of-fold (Scientist n=75) | -0.141 | -0.116 |
| Scientist − other: flag catch gap, out-of-fold | -0.031 | -0.017 |
| Therapy ≤ 2, true High, out-of-fold (n=54) | 0/54 predicted High, 33/54 flagged | 1/54 predicted High, 31/54 flagged |
| Direction check (Sleep, Caffeine, Activity, Diet) matches clinical expectation | 4/4 | 4/4 |

## 1. Nested 5-fold CV (same procedure and metrics as `reports/nested_cv_11feature_v2_xgb.md`)

LR: inside each outer training fold, GridSearchCV over C and class_weight (inner cv=5, balanced accuracy), then the review
threshold from the chosen configuration's inner out-of-fold P(High) (highest flagging ≥ 158/165). v2's numbers are read from
`reports/nested_cv_11feature_v2_xgb.json` (its own tuning: 40 XGBoost configurations per fold). Mean ± std over 5 folds
(population std, as in that report). Flag rows use each fold's own threshold.

**All ages**

| Metric | v2 XGBoost | Logistic regression | LR − v2 |
|---|---|---|---|
| Accuracy | 0.7891 ± 0.0081 | 0.7903 ± 0.0083 | +0.0012 |
| Balanced accuracy | 0.8121 ± 0.0060 | 0.8122 ± 0.0041 | +0.0001 |
| Macro-F1 | 0.8225 ± 0.0052 | 0.8226 ± 0.0060 | +0.0001 |
| Recall Low | 0.7946 ± 0.0133 | 0.8012 ± 0.0149 | +0.0066 |
| Recall Medium | 0.7604 ± 0.0101 | 0.7564 ± 0.0124 | -0.0040 |
| Model High recall | 0.8812 ± 0.0092 | 0.8791 ± 0.0202 | -0.0021 |
| Precision High | 0.9632 ± 0.0231 | 0.9607 ± 0.0139 | -0.0025 |
| Review-flag catch rate | 0.9546 ± 0.0143 | 0.9608 ± 0.0095 | +0.0062 |
| Flag volume | 0.2425 ± 0.0219 | 0.2327 ± 0.0111 | -0.0097 |
| Brier Low | 0.1369 ± 0.0050 | 0.1356 ± 0.0051 | -0.0013 |
| Brier Medium | 0.1496 ± 0.0031 | 0.1485 ± 0.0037 | -0.0010 |
| Brier High | 0.0148 ± 0.0020 | 0.0156 ± 0.0014 | +0.0008 |

**Ages 18-49**

| Metric | v2 XGBoost | Logistic regression | LR − v2 |
|---|---|---|---|
| Accuracy | 0.7978 ± 0.0084 | 0.7978 ± 0.0076 | -0.0000 |
| Balanced accuracy | 0.8226 ± 0.0053 | 0.8206 ± 0.0037 | -0.0020 |
| Macro-F1 | 0.8297 ± 0.0043 | 0.8285 ± 0.0050 | -0.0012 |
| Recall Low | 0.8042 ± 0.0179 | 0.8090 ± 0.0192 | +0.0048 |
| Recall Medium | 0.7506 ± 0.0152 | 0.7474 ± 0.0168 | -0.0032 |
| Model High recall | 0.9130 ± 0.0089 | 0.9055 ± 0.0170 | -0.0076 |
| Precision High | 0.9729 ± 0.0230 | 0.9713 ± 0.0128 | -0.0016 |
| Review-flag catch rate | 0.9658 ± 0.0166 | 0.9744 ± 0.0161 | +0.0086 |
| Flag volume | 0.2769 ± 0.0254 | 0.2657 ± 0.0154 | -0.0112 |
| Brier Low | 0.1308 ± 0.0060 | 0.1303 ± 0.0057 | -0.0005 |
| Brier Medium | 0.1436 ± 0.0036 | 0.1437 ± 0.0039 | +0.0001 |
| Brier High | 0.0150 ± 0.0021 | 0.0163 ± 0.0019 | +0.0013 |

| Fold | LR C | LR class_weight | LR threshold | v2 threshold |
|---|---|---|---|---|
| 1 | 0.1 | none | 0.0226 | 0.0234 |
| 2 | 100 | none | 0.0177 | 0.0814 |
| 3 | 0.1 | none | 0.0215 | 0.0263 |
| 4 | 10 | none | 0.0208 | 0.0288 |
| 5 | 1 | none | 0.0208 | 0.0311 |

## 2. The checks behind the XGBoost choice

**Caffeine shortcut, observed** (true-High patients with caffeine ≤ 200 mg/day):

| View | Model | True High with caffeine ≤ 200 | Predicted High | Flagged |
|---|---|---|---|---|
| Validation | v2 | 4 | 0 | 2 |
| Validation | LR | 4 | 0 | 1 |
| Out-of-fold | v2 | 23 | 0 | 12 |
| Out-of-fold | LR | 23 | 1 | 9 |

**Caffeine shortcut, counterfactual** (every true-High validation patient with caffeine set to a fixed value; models fitted on
the training split):

| Caffeine set to | v2: predicted High / flagged | LR: predicted High / flagged |
|---|---|---|
| 0 mg/day | 128 / 154 of 165 | 101 / 150 of 165 |
| 100 mg/day | 129 / 155 of 165 | 117 / 152 of 165 |
| 200 mg/day | 129 / 155 of 165 | 135 / 154 of 165 |

**Age artifact** (161 true-High validation patients under 50, only Age changed; models fitted on the training split):

| Age set to | v2: mean P(High) | v2: predicted High | LR: mean P(High) | LR: predicted High |
|---|---|---|---|---|
| 49 | 0.884 | 148 | 0.863 | 147 |
| 50 | 0.881 | 148 | 0.862 | 147 |
| 55 | 0.862 | 144 | 0.855 | 147 |

**Occupation fairness: Scientist vs all other occupations** (true High only):

| View | Model | Scientist: High recall / catch | Other: High recall / catch | Gap: recall / catch |
|---|---|---|---|---|
| Validation | v2 | 12/16 (75.0%) / 15/16 (93.8%) | 136/149 (91.3%) / 143/149 (96.0%) | -0.163 / -0.022 |
| Validation | LR | 12/16 (75.0%) / 16/16 (100.0%) | 136/149 (91.3%) / 142/149 (95.3%) | -0.163 / +0.047 |
| Out-of-fold | v2 | 56/75 (74.7%) / 70/75 (93.3%) | 793/893 (88.8%) / 861/893 (96.4%) | -0.141 / -0.031 |
| Out-of-fold | LR | 58/75 (77.3%) / 71/75 (94.7%) | 794/893 (88.9%) / 861/893 (96.4%) | -0.116 / -0.017 |

Scientist true-High counts are small, so a gap of a few points is one or two patients.

**Is the out-of-fold model High recall gap real?** Bootstrap 95% CI (2,000 resamples, seed 42,
patients resampled within each group) and a two-sided Fisher exact test on predicted-High vs not, Scientist vs other:

| Model | Scientist High recall | Other High recall | Gap | Bootstrap 95% CI | Fisher exact p | Odds ratio |
|---|---|---|---|---|---|---|
| v2 | 56/75 | 793/893 | -0.141 | -0.247 to -0.045 | 0.00136 | 0.37 |
| LR | 58/75 | 794/893 | -0.116 | -0.218 to -0.023 | 0.0082 | 0.43 |

**Reading.** v2: the CI excludes zero and Fisher p is 0.00136 (below 0.05); LR: the CI excludes zero and Fisher p is 0.0082 (below 0.05). Scientist was singled out because it was flagged earlier; if any of the 13 occupations could have been, a Bonferroni-adjusted p (× 13) is: v2 0.0177; LR 0.107. The two models' tests share patients. Out-of-fold predictions come from five models, not one. The data are very likely synthetic, and occupation shows no link to Stress Level in this dataset (CLAUDE.md). So this result bears on whether the gap is sampling noise; it does not explain the gap.

**Under-detected subgroups** (out-of-fold):

| Out-of-fold true High | Rows | v2: model High recall | v2: flag catch (0.025) | LR: model High recall | LR: flag catch |
|---|---|---|---|---|---|
| Therapy ≤ 2 sessions | 54 | 0/54 (0.0%) | 33/54 (61.1%) | 1/54 (1.9%) | 31/54 (57.4%) |
| Caffeine ≤ 200 mg/day | 23 | 0/23 (0.0%) | 12/23 (52.2%) | 1/23 (4.3%) | 9/23 (39.1%) |

## 3. Feature effects

LR coefficients are for the High class on the model's own inputs: numeric features standardised (per training std), so a
coefficient is the change in the High logit per one std. For Occupation and Family History the figure is the spread between
their one-hot levels' coefficients, which is not on the same scale. LR fitted on all 9,350 rows with the
training-split settings. v2's ranking is mean |SHAP| for High, out-of-fold (`reports/shap_v2.json`). Spearman correlation
of the two rankings: **0.66** over all 11 features, **0.98** over the 9 numeric features only.
The overall figure is pulled down by Occupation, whose spread over 13 levels is not comparable to a per-std coefficient.

| Feature | LR coefficient for High (per train std; categorical = spread of levels) | LR rank | v2 SHAP rank (High, out-of-fold) |
|---|---|---|---|
| Stress Level (1-10) | +2.016 | 1 | 1 |
| Occupation | range 1.041 | 2 | 10 |
| Sleep Hours | -1.014 | 3 | 3 |
| Therapy Sessions (per month) | +0.908 | 4 | 2 |
| Caffeine Intake (mg/day) | +0.829 | 5 | 4 |
| Physical Activity (hrs/week) | -0.450 | 6 | 5 |
| Diet Quality (1-10) | -0.324 | 7 | 6 |
| Age | -0.242 | 8 | 7 |
| Heart Rate (bpm) | +0.199 | 9 | 8 |
| Breathing Rate (breaths/min) | +0.099 | 10 | 9 |
| Family History of Anxiety | range 0.001 | 11 | 11 |

**Direction check** (LR: sign of the coefficient; v2: sign of the Spearman correlation between the feature and its SHAP
value for High, from `reports/shap_v2.json`):

| Feature | Clinical expectation | LR coefficient | LR matches | v2 (SHAP Spearman, out-of-fold) | v2 matches |
|---|---|---|---|---|---|
| Sleep Hours | higher -> less risk | -1.014 | yes | -0.927 | yes |
| Caffeine Intake (mg/day) | higher -> more risk | +0.829 | yes | +0.866 | yes |
| Physical Activity (hrs/week) | higher -> less risk | -0.450 | yes | -0.902 | yes |
| Diet Quality (1-10) | higher -> less risk | -0.324 | yes | -0.772 | yes |

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
  predicted-High count by +1 for v2 and +34 for LR. The 2026-09-28 switch away from Random
  Forest was partly about this sensitivity, because the API only estimates caffeine from drink counts.
- **Scientist gap, recorded but not resolved here.** Out-of-fold, with 75 Scientist true-High
  patients, both models show a model High recall gap (-0.141 for v2, -0.116 for LR). CLAUDE.md
  treats the Scientist flag as likely noise, based on 16 validation patients. This larger sample is the cross-validated check
  that note asked for. The flag catch gap is smaller (-0.031 / -0.017). No significance test was run.
- **Explainability.** LR's effects are one fixed coefficient per feature. v2's depend on the patient and need SHAP. Section 3
  shows whether the two models rank the same features as important.
- **Robustness and workload** (from `reports/sota_comparison.md`, "Why XGBoost if logistic regression ties?"): LR lost less
  balanced accuracy under noise and flagged fewer patients at matched coverage. v2 was better calibrated for High and Medium.
- **Cost of switching.** A switch would need a new served model, preprocessor and threshold, re-running the deployment
  manifest step (`docs/deployment.md`), and updating the model card, API docs and tests. The 0.025 threshold would not carry
  over. Calibration, SHAP-based explanations and fairness for the served model would need redoing.
- **Not covered:** the same caveats as v2's nested CV (feature set, label bins, age range and coverage target were decided
  on these rows), very likely synthetic data, and a self-rated social-anxiety target.

Libraries: scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.5.
