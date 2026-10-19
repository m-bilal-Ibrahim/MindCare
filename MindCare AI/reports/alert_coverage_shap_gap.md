# Alert layer vs the low-caffeine true-High gap: coverage and cost

Script: `src/experiments/alert_coverage_shap_gap.py`. **The test set was not used.** Out-of-fold over the 9,350
train + validation rows, rebuilt exactly as `src/explainability/shap_v2.py` does (5-fold stratified on the 3-class
label, shuffled, seed 42, served v2 hyperparameters, preprocessing fitted inside each fold); guarded to reproduce
the same 23 low-caffeine true-High rows (0 predicted High, 12 review-flagged) and the review flag's overall
931/968 catch with 2,361 flagged. Alert layer and **draft thresholds unchanged** (`src/config/alert_thresholds.toml`:
sleep ≤ 3, stress ≥ 8, HR ≥ 115, BR ≥ 27,
caffeine ≥ 520, diet < 4); attention level uses the out-of-fold model class.
Stress here is the dataset's raw 1-10 column; in the live API it comes from the four PSS-4 answers.

## 1. Coverage: the 23 true-High patients with caffeine ≤ 200 mg/day

| Row | Stress | Sleep (h) | Caffeine (mg) | Model class | P(High) | Review flag | Attention | Alerts |
|---|---|---|---|---|---|---|---|---|
| 3095 | 10 | 6.3 | 169 | Medium | 0.0493 | yes | notice | high_stress |
| 1505 | 9 | 7.2 | 98 | Medium | 0.0133 | no | notice | high_stress |
| 617 | 9 | 6.9 | 164 | Medium | 0.0292 | yes | elevated | high_stress, low_diet_quality |
| 1506 | 10 | 6.9 | 19 | Medium | 0.0266 | yes | elevated | high_stress, low_diet_quality |
| 3814 | 9 | 6.1 | 157 | Medium | 0.0081 | no | notice | high_stress |
| 7001 | 10 | 7.3 | 190 | Medium | 0.0383 | yes | notice | high_stress |
| 10698 | 10 | 7.1 | 197 | Medium | 0.0462 | yes | elevated | high_stress, high_heart_rate |
| 1095 | 8 | 3.9 | 183 | Medium | 0.0181 | no | notice | high_stress |
| 5040 | 8 | 4.9 | 51 | Medium | 0.0175 | no | notice | high_stress |
| 9483 | 10 | 6.6 | 192 | Medium | 0.0326 | yes | elevated | high_stress, low_diet_quality |
| 1781 | 10 | 6.7 | 110 | Medium | 0.0491 | yes | notice | high_stress |
| 3057 | 8 | 6.5 | 77 | Medium | 0.0089 | no | notice | high_stress |
| 2584 | 9 | 7.8 | 116 | Medium | 0.0109 | no | notice | high_stress |
| 6272 | 10 | 6.9 | 49 | Medium | 0.0268 | yes | notice | high_stress |
| 4443 | 9 | 7.9 | 143 | Medium | 0.0138 | no | elevated | high_stress, low_diet_quality |
| 1284 | 9 | 7.4 | 176 | Medium | 0.0094 | no | notice | high_stress |
| 8797 | 10 | 7.7 | 161 | Medium | 0.0770 | yes | elevated | high_stress, low_diet_quality |
| 4061 | 8 | 6.5 | 89 | Medium | 0.0182 | no | elevated | high_stress, high_heart_rate |
| 1406 | 9 | 3.9 | 179 | Medium | 0.0394 | yes | notice | high_stress |
| 6420 | 10 | 8.2 | 103 | Medium | 0.0183 | no | notice | high_stress |
| 7929 | 10 | 7.6 | 101 | Medium | 0.0556 | yes | notice | high_stress |
| 10199 | 9 | 6.4 | 60 | Medium | 0.0146 | no | elevated | high_stress, high_breathing_rate |
| 2318 | 10 | 6.3 | 165 | Medium | 0.0802 | yes | elevated | high_stress, low_diet_quality |

- Stress ≥ 8 alert: **23 of 23**; any alert: 23 of 23.
- Attention level: urgent 0, elevated 9, notice 14, clear 0. Final risk class High: 0 of 23.
- Review flag: 12 of 23; **review flag OR any alert: 23 of 23**
  (11 only through an alert, 0 caught by neither).

## 2. Cost: all 9,350 patients by true class (out-of-fold)

| True class | Rows | Stress ≥ 8 alert | Any alert | Review flag (P(High) ≥ 0.025) | Review flag OR any alert | Stress alert AND review flag |
|---|---|---|---|---|---|---|
| Low | 4,421 | 400 (9.0%) | 2,451 (55.4%) | 135 (3.1%) | 2,452 (55.5%) | 123 (2.8%) |
| Medium | 3,961 | 2,089 (52.7%) | 3,069 (77.5%) | 1,295 (32.7%) | 3,088 (78.0%) | 1,223 (30.9%) |
| High | 968 | 954 (98.6%) | 962 (99.4%) | 931 (96.2%) | 963 (99.5%) | 930 (96.1%) |
| **All** | 9,350 | 3,443 (36.8%) | 6,482 (69.3%) | 2,361 (25.3%) | 6,503 (69.6%) | 2,276 (24.3%) |

Attention level by true class:

| True class | Rows | urgent | elevated | notice | clear |
|---|---|---|---|---|---|
| Low | 4,421 | 0 (0.0%) | 624 (14.1%) | 1,827 (41.3%) | 1,970 (44.6%) |
| Medium | 3,961 | 21 (0.5%) | 1,309 (33.0%) | 1,739 (43.9%) | 892 (22.5%) |
| High | 968 | 849 (87.7%) | 65 (6.7%) | 48 (5.0%) | 6 (0.6%) |
| **All** | 9,350 | 870 (9.3%) | 1,998 (21.4%) | 3,614 (38.7%) | 2,868 (30.7%) |

Catch rate of true-High patients (n = 968): review flag alone 931 (96.2%); any alert alone
962 (99.4%); **review flag OR any alert 963 (99.5%)**. Patients flagged by that
combination: **6,503 (69.6%)** of all 9,350, against 2,361 (25.3%) for the
review flag alone.

## 3. Conclusion

The alert layer closes the coverage gap: every one of the 23 low-caffeine true-High patients gets a stress ≥ 8
alert, so "review flag OR any alert" catches 23 of 23 where the review flag alone catches 12.
But it does so only at a low priority — 14 get "notice" and 9 "elevated",
none "urgent", and all stay Medium — and the cost is volume: the stress alert fires for
400 (9.0%) of Low and 2,089 (52.7%) of Medium patients, and "review
flag OR any alert" marks 6,503 (69.6%) of all patients (review flag alone:
2,361 (25.3%)). In practice the combination raises the true-High catch rate from
96.2% to 99.5% by putting most patients on the reviewer's list, so it is not a
targeted fix for this gap. Very likely synthetic data; draft thresholds pending psychologist review.

## 4. Open question for the psychologist (not implemented)

**Should a stress alert together with P(High) ≥ 0.025 raise the attention level** (for example to "elevated" or
"urgent")? For reference only, out-of-fold: 2,276 (24.3%) of all patients have both,
by true class Low 123 (2.8%), Medium 1,223 (30.9%), High
930 (96.1%). Of the 23 low-caffeine true-High patients,
12 have both, so such a rule would raise only
those; the other 11 have the stress alert without
the review flag and would stay where they are. No rule was changed.
