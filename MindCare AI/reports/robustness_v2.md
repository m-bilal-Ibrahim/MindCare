# Phase 19 robustness for the served 11-feature v2 XGBoost (validation only)

Script: `src/evaluation/robustness_v2.py`. **The test set was not used; no served file or threshold changed.** The served
files on the 1,650 validation rows; imputation values and noise scales from the training split only. Comparison numbers
are parsed from `reports/robustness_3class.md`, which is the **17-feature Random Forest** (baseline balanced accuracy
0.8056), not a 12-feature model. "Model High recall" = predicted class
High; "flag catch rate" = true High with P(High) ≥ 0.025.

Guard: balanced accuracy 0.8055, 411 flagged, 158/165
true High flagged — reproduces v2. Baseline: balanced accuracy 0.8055, macro-F1 0.8148, model
High recall 0.8970, flag catch rate 0.9576.

## 1. Single-feature knockout (train median, then train mean; categorical = train mode)

| Feature | Median: balanced acc. (Δ) | Median: macro-F1 | Median: model High recall | Median: flag catch | Mean: balanced acc. (Δ) | Mean: model High recall | Mean: flag catch | 17-feature RF (mean/mode): balanced acc. / model High recall |
|---|---|---|---|---|---|---|---|---|
| Stress Level (1-10) | 0.3837 (-0.4218) | 0.3750 | 0.0485 | 0.8848 | 0.3743 (-0.4312) | 0.0000 | 0.8424 | 0.4291 / 0.2242 |
| Therapy Sessions (per month) | 0.5494 (-0.2561) | 0.5592 | 0.1273 | 0.9455 | 0.5494 (-0.2561) | 0.1273 | 0.9455 | 0.5590 / 0.1515 |
| Sleep Hours | 0.7040 (-0.1015) | 0.7428 | 0.5818 | 0.9697 | 0.7155 (-0.0900) | 0.6182 | 0.9758 | 0.7922 / 0.8545 |
| Caffeine Intake (mg/day) | 0.7858 (-0.0197) | 0.8022 | 0.8424 | 0.9515 | 0.7907 (-0.0148) | 0.8545 | 0.9576 | 0.7972 / 0.8727 |
| Physical Activity (hrs/week) | 0.7946 (-0.0109) | 0.8074 | 0.8667 | 0.9758 | 0.7946 (-0.0109) | 0.8667 | 0.9758 | 0.8065 / 0.8970 |
| Diet Quality (1-10) | 0.8014 (-0.0041) | 0.8152 | 0.8788 | 0.9576 | 0.8014 (-0.0041) | 0.8788 | 0.9576 | 0.7995 / 0.8788 |
| Heart Rate (bpm) | 0.8026 (-0.0029) | 0.8126 | 0.8909 | 0.9576 | 0.8026 (-0.0029) | 0.8909 | 0.9576 | 0.8055 / 0.8970 |
| Occupation | 0.8046 (-0.0009) | 0.8140 | 0.8970 | 0.9576 | 0.8046 (-0.0009) | 0.8970 | 0.9576 | 0.8070 / 0.8970 |
| Breathing Rate (breaths/min) | 0.8053 (-0.0003) | 0.8146 | 0.8970 | 0.9576 | 0.8048 (-0.0007) | 0.8970 | 0.9576 | 0.8068 / 0.8970 |
| Age | 0.8060 (+0.0005) | 0.8145 | 0.8970 | 0.9576 | 0.8060 (+0.0005) | 0.8970 | 0.9576 | 0.8057 / 0.8970 |
| Family History of Anxiety | 0.8096 (+0.0041) | 0.8187 | 0.8970 | 0.9576 | 0.8096 (+0.0041) | 0.8970 | 0.9576 | 0.8029 / 0.8970 |

## 2. Gaussian noise on all 9 numeric features (10 seeds, mean ± std)

| Noise (× train std) | Balanced accuracy | Macro-F1 | Model High recall | Flag catch rate | 17-feature RF, 1 seed: balanced acc. / model High recall |
|---|---|---|---|---|---|
| 0.25 | 0.7591 ± 0.0057 | 0.7821 ± 0.0049 | 0.7867 ± 0.0153 | 0.9461 ± 0.0053 | 0.7732 / 0.8000 |
| 0.5 | 0.7027 ± 0.0177 | 0.7357 ± 0.0149 | 0.6576 ± 0.0449 | 0.9376 ± 0.0134 | 0.6837 / 0.6121 |
| 0.75 | 0.6503 ± 0.0149 | 0.6862 ± 0.0143 | 0.5545 ± 0.0364 | 0.9018 ± 0.0153 | not tested |
| 1.0 | 0.6008 ± 0.0116 | 0.6365 ± 0.0112 | 0.4636 ± 0.0305 | 0.8594 ± 0.0252 | 0.5560 / 0.3273 |

## 3. Invalid inputs through `validate_patient()`

| Case | Rejected by validate_patient() | Detail |
|---|---|---|
| valid row (control) | no | 0 warning(s) |
| negative age (-5) | **yes** | Input validation failed with 1 error(s):
  - Age=-5 is outside the physically plausible range [0, 120] (0-120: outer bound of recorded human lifespan.) |
| under 18 (16) | **yes** | Input validation failed with 1 error(s):
  - Age=16 is under 18 - not eligible for MindCare (adults only; registration should have blocked this user). No predic |
| over 49 (55) | **yes** | Input validation failed with 1 error(s):
  - Age=55 is outside the supported range for AI pre-assessment [18, 49] - no prediction is made; refer this person dir |
| impossible stress (250) | **yes** | Input validation failed with 1 error(s):
  - Stress Level (1-10)=250 is outside the physically plausible range [0, 12] (0-12: 1-10 rating scale plus a small mar |
| impossible heart rate (9000) | **yes** | Input validation failed with 1 error(s):
  - Heart Rate (bpm)=9000 is outside the physically plausible range [30, 220] (30-220 bpm: standard clinical outer rang |
| negative sleep (-1) | **yes** | Input validation failed with 1 error(s):
  - Sleep Hours=-1 is outside the physically plausible range [0, 24] (0-24: a day has 24 hours.) |
| caffeine over 1200 mg (1500) | **yes** | Input validation failed with 1 error(s):
  - Caffeine Intake (mg/day)=1500 is outside the physically plausible range [0, 1200] (0-1200: commonly cited threshold |
| text instead of number | **yes** | Input validation failed with 1 error(s):
  - Heart Rate (bpm): expected a number, got 'fast' (str) |
| missing Stress Level | **yes** | Input validation failed with 1 error(s):
  - Missing required feature(s): ['Stress Level (1-10)'] |
| all numeric fields 999 | **yes** | Input validation failed with 8 error(s):
  - Age=999 is outside the physically plausible range [0, 120] (0-120: outer bound of recorded human lifespan.)
  - Sle |

## 4. Stress Level shift (clipped to 1–10)

| Shift | Rows changed | Predicted-High share | Flagged share | Balanced accuracy | Model High recall | 17-feature RF predicted-High share |
|---|---|---|---|---|---|---|
| -3 | 1495 | 0.0242 | 0.0964 | 0.5150 | 0.2424 | 0.0418 |
| -2 | 1495 | 0.0576 | 0.1303 | 0.6546 | 0.5576 | — |
| -1 | 1495 | 0.0855 | 0.1776 | 0.7726 | 0.8303 | 0.0879 |
| +0 | 0 | 0.0927 | 0.2491 | 0.8055 | 0.8970 | — |
| +1 | 1442 | 0.0927 | 0.3261 | 0.7999 | 0.8970 | 0.0903 |
| +2 | 1442 | 0.0927 | 0.4006 | 0.7833 | 0.8970 | — |
| +3 | 1442 | 0.0933 | 0.4745 | 0.7549 | 0.8970 | 0.0903 |

### Root cause of "shifting Stress up changes nothing"

**(a) Clipping.** 410 of 1,650 validation rows already have Stress 9–10 (208 at 10), by true class
Low 39, Medium 251, High 120. A +3 shift changes 1442 rows' values (the rest are
already at 10 or clip to it). True-High rows by Stress value: 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 1, 8: 44, 9: 60, 10: 60.

**(b) Split saturation.** The trees split on Stress 1263 times; thresholds in raw units (count):
2.0 (112), 3.0 (86), 4.0 (88), 5.0 (105), 6.0 (191), 7.0 (171), 8.0 (230), 9.0 (166), 10.0 (114). XGBoost sends values below a threshold left, so these splits separate every integer level
2–10 from the one below it: there is **no hard saturation** below 10.

| Stress set to | Mean P(High) | Predicted-High share |
|---|---|---|
| 1 | 0.0045 | 0.0000 |
| 2 | 0.0049 | 0.0000 |
| 3 | 0.0053 | 0.0000 |
| 4 | 0.0064 | 0.0000 |
| 5 | 0.0095 | 0.0000 |
| 6 | 0.0250 | 0.0048 |
| 7 | 0.0577 | 0.0661 |
| 8 | 0.1223 | 0.0933 |
| 9 | 0.1291 | 0.0958 |
| 10 | 0.1484 | 0.0976 |

**(c) Therapy Sessions interaction.**

| Therapy band (train quartiles) | Rows | True High | Predicted High: shift −3 / 0 / +3 | With Stress = 10: mean P(High) / predicted-High share |
|---|---|---|---|---|
| (-0.001, 1.0] | 696 | 5 | 0.0000 / 0.0000 / 0.0000 | 0.0450 / 0.0000 |
| (1.0, 2.0] | 312 | 3 | 0.0000 / 0.0000 / 0.0000 | 0.0518 / 0.0000 |
| (2.0, 4.0] | 368 | 25 | 0.0163 / 0.0598 / 0.0625 | 0.1279 / 0.0652 |
| (4.0, 12.0] | 274 | 132 | 0.1241 / 0.4781 / 0.4781 | 0.5484 / 0.5000 |

### Which explanation the evidence supports (computed)

- The asymmetry persists in v2: a +3 shift moves the predicted-High share by +0.0006, a −3 shift by -0.0685. It is
  about the predicted **class** only: the flagged share rises from 0.2491 to
  0.4745 with +3, so P(High) does respond.
- **(a) Clipping: not the explanation.** +3 changes 1442 of 1,650 rows' Stress values, yet the
  predicted-High share barely moves.
- **(b) Hard split saturation: not the explanation** (splits up to 10.000). There is a
  **soft plateau**: mean P(High) rises +0.0973 from Stress 6 to 8 but only +0.0261 from 8 to 10 (predicted-High
  share +0.0042).
- **(c) Therapy interaction: supported, and the main explanation.** With Stress forced to 10, patients in the Therapy band(s)
  (-0.001, 1.0], (1.0, 2.0] (1008 of 1,650 rows) are never predicted High; High predictions come
  almost only from the highest band ((4.0, 12.0]: 0.5000 predicted High at
  Stress 10). In this data every true-High patient already has Stress ≥ 7, so raising Stress cannot create new
  High predictions: High needs high Stress **and** other signals, mainly Therapy Sessions.
- **Conclusion:** the evidence supports (c), the Stress × Therapy interaction, together with the soft plateau above Stress 8;
  it does not support clipping (a) or hard saturation (b).

## 5. Therapy dependence: can patients with little therapy history be detected as High?

Out-of-fold over the 9,350 train + validation rows, rebuilt as `shap_v2.py` does (guarded: the review flag catches
931/968 true High and flags 2,361).

**How common is Therapy <= 2 sessions/month?**

| True class | Rows | Therapy <= 2 | Share |
|---|---|---|---|
| Low | 4,421 | 3,128 | 70.8% |
| Medium | 3,961 | 2,496 | 63.0% |
| High | 968 | 54 | 5.6% |

**Detection of true-High patients (out-of-fold)**

| True-High patients | Rows | Model High recall | Review-flag catch rate (P(High) >= 0.025) |
|---|---|---|---|
| Therapy <= 2 | 54 | 0 (0.0%) | 33 (61.1%) |
| Therapy > 2 | 914 | 849 (92.9%) | 898 (98.2%) |

**P(High) with Stress set to 8 / 9 / 10, by therapy band (validation rows, served files)**

| Therapy band | Rows | Mean P(High): Stress 8 / 9 / 10 | Predicted-High share: 8 / 9 / 10 | Flagged share: 8 / 9 / 10 |
|---|---|---|---|---|
| 0-2 | 1008 | 0.0240 / 0.0294 / 0.0471 | 0.0000 / 0.0000 / 0.0000 | 0.2520 / 0.3720 / 0.7510 |
| 3-5 | 486 | 0.1443 / 0.1521 / 0.1760 | 0.1008 / 0.1049 / 0.1111 | 0.6420 / 0.7325 / 0.9218 |
| 6+ | 156 | 0.6892 / 0.7011 / 0.7167 | 0.6731 / 0.6859 / 0.6859 | 0.9872 / 1.0000 / 1.0000 |

**Conclusion.** Few High patients in this data have little therapy history: 54 of 968 true-High rows (5.6%) have at most 2 sessions/month, against 70.8% of Low and 63.0% of Medium. For those 54 patients the model High recall is 0.0% (vs 92.9% with more therapy), and even with Stress forced to 10 the 0-2 band has a mean P(High) of 0.0471 and a predicted-High share of 0.0000. **Patients with little therapy history are rarely or never detected as High by the predicted class.** The review flag covers 33 of 54 of them (61.1%, vs 98.2% with more therapy); with Stress at 10, 75.1% of the 0-2 band would be flagged. Therapy count most likely acts as a proxy for severity in this dataset (people with more severe anxiety attend more sessions: reverse causality), so new help-seekers with high stress may be under-called. Small sample of true-High rows with little therapy; very likely synthetic data.

Libraries: python 3.13.13, xgboost 3.4.1, scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.5. Very likely synthetic data: prototype-level evidence only.
