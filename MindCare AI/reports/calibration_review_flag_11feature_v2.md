# Calibration and the review-flag threshold: 11-feature v2 (out-of-fold, CV only)

Script: `src/experiments/calibration_review_flag_11feature_v2.py`. **The test set was not used.** Out-of-fold
probabilities for all 9,350 train + validation rows (968 true High), 5-fold stratified on the 3-class label,
shuffled, seed 42 (the folds of the re-tuning and derived-feature reports). Per-row probabilities:
`reports/calibration_review_flag_11feature_v2_oof.csv`.

## Threshold target (fixed before the tables were built)

flag catch rate >= 0.95 of true-High, flagging as few patients as possible (largest threshold meeting it); fixed before the tables were built.

## Deployed object this mirrors

CalibratedClassifierCV(XGBClassifier(v2 params), method, cv=StratifiedKFold(5, shuffle, 42), ensemble=False) fitted on the training rows; same preprocessor; one pickle. Inside every outer fold the exact object was fitted on the fold's training part only (its
own inner 5-fold CV for the calibrator), and the plain v2 XGBoost on the same part is the uncalibrated arm.

## 1. Calibration (Brier score and ECE per class, one-vs-rest, 10 bins; lower is better)

| Class | Brier: uncalibrated | Brier: isotonic | Brier: sigmoid | ECE: uncalibrated | ECE: isotonic | ECE: sigmoid |
|---|---|---|---|---|---|---|
| Low | 0.1368 | 0.1373 | 0.1381 | 0.0102 | 0.0053 | 0.0313 |
| Medium | 0.1485 | 0.1487 | 0.1495 | 0.0104 | 0.0071 | 0.0364 |
| High | 0.0140 | 0.0138 | 0.0150 | 0.0048 | 0.0019 | 0.0110 |
| **Sum / mean** | **0.2994** | **0.2997** | **0.3026** | **0.0085** | **0.0048** | **0.0262** |

Better method by out-of-fold Brier, then ECE: **isotonic**. Sigmoid makes calibration worse. The uncalibrated v2 model is
already well calibrated (ECE at most 0.010 per class); isotonic lowers ECE but does not improve the Brier score.

## 2. Does calibration change the predictions?

Same predicted class on 98.5% of rows; 137 rows change
(Low->Medium: 131, High->Medium: 6).

| Metric (out-of-fold, 9,350 rows) | Uncalibrated | Isotonic | Difference |
|---|---|---|---|
| balanced_accuracy | 0.8113 | 0.8119 | +0.0006 |
| macro_f1 | 0.8239 | 0.8251 | +0.0011 |
| high_recall | 0.8771 | 0.8750 | -0.0021 |

**MODEL CHANGE: calibration changes predicted classes and costs High recall**
(-2 true-High patients labelled High), for a
negligible gain elsewhere.

## 3. Review threshold trade-off (out-of-fold)

"Missed High caught" = true-High patients the model labels Low/Medium that the flag still points at; "wrong
caught" = all wrong predictions among flagged patients.

### Uncalibrated (as served)

| Threshold | Patients flagged | True High caught | Missed High caught | Wrong caught |
|---|---|---|---|---|
| 0.005 | 4,438 (47.5%) | 964/968 (99.59%) | 115 | 852 |
| 0.01 | 3,553 (38.0%) | 955/968 (98.66%) | 106 | 535 |
| 0.015 | 3,060 (32.7%) | 946/968 (97.73%) | 97 | 397 |
| 0.02 | 2,671 (28.6%) | 935/968 (96.59%) | 86 | 298 |
| 0.025 (current) | 2,361 (25.3%) | 931/968 (96.18%) | 82 | 238 |
| 0.0302 | 2,111 (22.6%) | 923/968 (95.35%) | 74 | 190 |
| 0.0349 (proposed) | 1,939 (20.7%) | 921/968 (95.14%) | 72 | 172 |
| 0.035 | 1,936 (20.7%) | 919/968 (94.94%) | 70 | 170 |
| 0.04 | 1,761 (18.8%) | 913/968 (94.32%) | 64 | 143 |
| 0.05 | 1,554 (16.6%) | 904/968 (93.39%) | 55 | 116 |
| 0.06 | 1,393 (14.9%) | 893/968 (92.25%) | 44 | 97 |
| 0.075 | 1,257 (13.4%) | 882/968 (91.12%) | 33 | 69 |
| 0.1 | 1,128 (12.1%) | 874/968 (90.29%) | 25 | 53 |
| 0.125 | 1,053 (11.3%) | 871/968 (89.98%) | 22 | 46 |
| 0.15 | 1,009 (10.8%) | 864/968 (89.26%) | 15 | 38 |
| 0.2 | 951 (10.2%) | 858/968 (88.64%) | 9 | 31 |
| 0.25 | 918 (9.8%) | 857/968 (88.53%) | 8 | 29 |
| 0.3 | 898 (9.6%) | 854/968 (88.22%) | 5 | 25 |
| 0.4 | 883 (9.4%) | 852/968 (88.02%) | 3 | 23 |
| 0.5 | 869 (9.3%) | 849/968 (87.71%) | 0 | 20 |

### Isotonic-calibrated

| Threshold | Patients flagged | True High caught | Missed High caught | Wrong caught |
|---|---|---|---|---|
| 0.005 | 3,818 (40.8%) | 960/968 (99.17%) | 113 | 631 |
| 0.01 | 3,622 (38.7%) | 955/968 (98.66%) | 108 | 551 |
| 0.015 | 3,247 (34.7%) | 952/968 (98.35%) | 105 | 446 |
| 0.02 | 3,042 (32.5%) | 946/968 (97.73%) | 99 | 393 |
| 0.025 (current) | 2,706 (28.9%) | 937/968 (96.80%) | 90 | 308 |
| 0.0302 | 2,500 (26.7%) | 931/968 (96.18%) | 84 | 271 |
| 0.035 | 2,302 (24.6%) | 924/968 (95.45%) | 77 | 222 |
| 0.0374 (proposed) | 2,167 (23.2%) | 922/968 (95.25%) | 75 | 194 |
| 0.04 | 1,911 (20.4%) | 915/968 (94.52%) | 68 | 152 |
| 0.05 | 1,668 (17.8%) | 906/968 (93.60%) | 59 | 125 |
| 0.06 | 1,452 (15.5%) | 900/968 (92.98%) | 53 | 102 |
| 0.075 | 1,137 (12.2%) | 870/968 (89.88%) | 23 | 47 |
| 0.1 | 999 (10.7%) | 864/968 (89.26%) | 17 | 39 |
| 0.125 | 913 (9.8%) | 855/968 (88.33%) | 8 | 24 |
| 0.15 | 898 (9.6%) | 854/968 (88.22%) | 7 | 23 |
| 0.2 | 889 (9.5%) | 851/968 (87.91%) | 4 | 20 |
| 0.25 | 886 (9.5%) | 851/968 (87.91%) | 4 | 20 |
| 0.3 | 877 (9.4%) | 849/968 (87.71%) | 2 | 18 |
| 0.4 | 868 (9.3%) | 849/968 (87.71%) | 2 | 18 |
| 0.5 | 863 (9.2%) | 847/968 (87.50%) | 0 | 16 |

### Bootstrap 95% intervals (2000 resamples of the 9,350 rows, seed 42)

| Threshold | Flag catch rate of true High | Share flagged |
|---|---|---|
| uncalibrated 0.025 | 96.18% [94.86%, 97.29%] | 25.3% [24.4%, 26.1%] |
| uncalibrated 0.0302 | 95.35% [93.97%, 96.67%] | 22.6% [21.8%, 23.4%] |
| uncalibrated 0.0349 | 95.14% [93.79%, 96.47%] | 20.7% [19.9%, 21.6%] |
| isotonic 0.0374 | 95.25% [93.94%, 96.53%] | 23.2% [22.4%, 24.0%] |

The intervals hold the threshold fixed, so they do not include the uncertainty of choosing it.

### Validation split only (1,650 rows, for continuity with earlier reports)

| Threshold | Flagged | True High caught |
|---|---|---|
| uncalibrated 0.025 | 408 (24.7%) | 158/165 |
| uncalibrated 0.0302 | 366 (22.2%) | 157/165 |
| uncalibrated 0.0349 | 341 (20.7%) | 157/165 |
| isotonic 0.0374 | 374 (22.7%) | 158/165 |

## 4. Knock-on effect on the confident/borderline label (0.70 cut-off, out-of-fold)

| Probabilities and flag threshold | Confident | Accuracy if confident | Accuracy if borderline | True High shown as a confident Low/Medium |
|---|---|---|---|---|
| uncalibrated_at_0.025 | 56.2% | 0.8582 | 0.7015 | 33 |
| uncalibrated_at_0.0349 | 60.4% | 0.8581 | 0.6847 | 43 |
| isotonic_at_0.0374 | 60.1% | 0.8503 | 0.6997 | 42 |

## Proposal

- **Calibration: do not deploy.** v2 is already well calibrated; isotonic changes 137 predicted classes and
  loses High recall, and at the same ~95% catch it flags more patients than the uncalibrated model.
- **Threshold, by the pre-set target: 0.0349** on the uncalibrated probabilities. It is the largest threshold that still
  catches ≥ 95% of true High out-of-fold, and flags about 21% of patients instead of
  25% at 0.025.
- **Caveats for that choice:** it sits exactly on the target (0.035 already falls below 95%); its catch-rate interval
  goes down to 93.8% (0.025: 94.9%); it catches 10 fewer of 968 true-High patients than 0.025;
  and more true-High patients are shown as a confident Low/Medium (43 vs 33). 0.0302 is the in-between
  option. Choosing between catching more High patients and flagging fewer is a clinical decision.

## Known optimism

v2 hyperparameters were tuned on rows inside these 9,350, and the threshold is proposed on the rows it is reported on; estimates are slightly optimistic.

## What would change (nothing was changed)

If the threshold changes:
- `MindCare AI/src/api/main.py`: `HIGH_PROBA_THRESHOLD = 0.025` and its comment
- `MindCare AI/src/inference/predict_single.py`: its own copy of `HIGH_PROBA_THRESHOLD = 0.025`
- `MindCare AI/src/api/static/manual_test_form.html`: the text "P(High) ≥ 0.025"
- `MindCare AI/tests/test_api.py`: `assert HIGH_PROBA_THRESHOLD == 0.025`, and `test_confidence_label_matches_report_on_validation` (pins 54.8% / 0.8530 / 0.6792 / 7 at the current threshold)
- `MindCare AI/src/inference/confidence.py` docstring and `reports/confidence_label_11feature_v2.md`: the confident/borderline evidence is computed at 0.025 and would need re-deriving
- `MindCare Backend/apps/ai/api/serializers.py`: help text "P(High) >= 0.025"
- Docs: `MindCare AI/docs/api_usage.md`, `docs/model_card.md`, `CLAUDE.md` (all quote 0.025 and 158/165)

If calibration were deployed, additionally:
- `data/processed/mindcare_final_model_11feature_v2_xgb.pkl` replaced by a new calibrated pickle (`CalibratedClassifierCV`, same scikit-learn 1.9.1 / xgboost 3.4.1; no new library or format beyond a different pickled class) and `MODEL_PATH` in `src/api/main.py` / `src/inference/predict_single.py`
- `scripts/deploy_artifacts.py` `ARTIFACTS` and `data/processed/deploy_artifacts.json` (hashes and the expected example probabilities)
- `tests/test_api.py` `test_serves_xgboost_with_its_review_threshold` (asserts the model is an `XGBClassifier`) and every test pinned to the current probabilities
- `src/inference/confidence.py` `CONFIDENCE_THRESHOLD = 0.70`: its evidence (share confident, accuracy) is for uncalibrated probabilities and would need re-deriving
- the `/patient-summary` severity-tier lookup uses the predicted class, which calibration changes for 1.5% of rows

The alert layer (`src/inference/alerts.py`, `src/config/alert_thresholds.toml`, open PR) does not use this flag and is
not affected.

Libraries: python 3.13.13, xgboost 3.4.1, scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.5. Very likely synthetic dataset:
prototype-level evidence only.
