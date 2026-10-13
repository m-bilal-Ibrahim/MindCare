# Fairness: 11-feature v2 by Gender and Occupation (validation and CV only)

Script: `src/fairness/fairness_11feature_v2.py`. **The test set was not used.** Model: the served v2 XGBoost, uncalibrated, review threshold 0.025. Validation split = the served files on the 1,650 validation rows; out-of-fold = 9,350 train + validation rows on the shared 5 folds (seed 42), preprocessing fitted inside each fold.

Rule: a group is flagged when its balanced accuracy or High recall is more than 5% points below the overall value of the same view; flags carry a bootstrap 95% interval (2000 resamples within the group). Gender is not a model input; Occupation is.

## Out-of-fold (9,350 rows): Gender

| Group | Rows | True High | Balanced accuracy | High recall | Flag catch (0.025) | Flag |
|---|---|---|---|---|---|---|
| **All** | 9350 | 968 | 0.8113 | 0.8771 | 0.9618 | |
| Female | 3163 | 334 | 0.8068 | 0.8653 | 0.9491 | — |
| Male | 3090 | 323 | 0.8165 | 0.9040 | 0.9721 | — |
| Other | 3097 | 311 | 0.8104 | 0.8617 | 0.9646 | — |

## Out-of-fold (9,350 rows): Occupation

| Group | Rows | True High | Balanced accuracy | High recall | Flag catch (0.025) | Flag |
|---|---|---|---|---|---|---|
| **All** | 9350 | 968 | 0.8113 | 0.8771 | 0.9618 | |
| Artist | 754 | 69 | 0.8429 | 0.9565 | 0.9710 | — |
| Athlete | 692 | 70 | 0.8299 | 0.9286 | 0.9714 | — |
| Chef | 714 | 71 | 0.8163 | 0.8592 | 0.9859 | — |
| Doctor | 712 | 78 | 0.8045 | 0.8718 | 0.9744 | — |
| Engineer | 718 | 77 | 0.7834 | 0.8182 | 0.9610 | **high_recall -0.059** (95% CI 0.726–0.903) |
| Freelancer | 725 | 79 | 0.8149 | 0.8608 | 0.9620 | — |
| Lawyer | 683 | 74 | 0.7911 | 0.8378 | 0.9730 | — |
| Musician | 758 | 79 | 0.8093 | 0.9114 | 0.9494 | — |
| Nurse | 733 | 71 | 0.8197 | 0.9296 | 0.9718 | — |
| Other | 727 | 75 | 0.8206 | 0.9200 | 0.9600 | — |
| Scientist | 711 | 75 | 0.7595 | 0.7467 | 0.9333 | **balanced_accuracy -0.052** (95% CI 0.719–0.797); **high_recall -0.130** (95% CI 0.645–0.847) |
| Student | 729 | 82 | 0.8358 | 0.9024 | 0.9390 | — |
| Teacher | 694 | 68 | 0.8043 | 0.8676 | 0.9559 | — |

## Validation split (1,650 rows): Gender

| Group | Rows | True High | Balanced accuracy | High recall | Flag catch (0.025) | Flag |
|---|---|---|---|---|---|---|
| **All** | 1650 | 165 | 0.8055 | 0.8970 | 0.9576 | |
| Female | 564 | 47 | 0.7934 | 0.8723 | 0.9574 | — |
| Male | 549 | 64 | 0.7992 | 0.9062 | 0.9688 | — |
| Other | 537 | 54 | 0.8234 | 0.9074 | 0.9444 | — |

## Validation split (1,650 rows): Occupation

| Group | Rows | True High | Balanced accuracy | High recall | Flag catch (0.025) | Flag |
|---|---|---|---|---|---|---|
| **All** | 1650 | 165 | 0.8055 | 0.8970 | 0.9576 | |
| Artist | 128 | 10 | 0.8335 | 1.0000 | 1.0000 | — |
| Athlete | 100 | 12 | 0.8706 | 1.0000 | 1.0000 | — |
| Chef | 131 | 16 | 0.7974 | 0.8750 | 1.0000 | — |
| Doctor | 140 | 12 | 0.8158 | 0.9167 | 1.0000 | — |
| Engineer | 117 | 14 | 0.7916 | 0.7857 | 0.8571 | **high_recall -0.111** (95% CI 0.542–1.000) |
| Freelancer | 132 | 9 | 0.7783 | 0.8889 | 1.0000 | — |
| Lawyer | 115 | 11 | 0.8032 | 1.0000 | 1.0000 | — |
| Musician | 122 | 10 | 0.7952 | 1.0000 | 1.0000 | — |
| Nurse | 145 | 13 | 0.7923 | 0.8462 | 0.9231 | **high_recall -0.051** (95% CI 0.611–1.000) |
| Other | 135 | 18 | 0.8380 | 0.9444 | 1.0000 | — |
| Scientist | 132 | 16 | 0.7450 | 0.7500 | 0.9375 | **balanced_accuracy -0.061** (95% CI 0.656–0.832); **high_recall -0.147** (95% CI 0.500–0.941) |
| Student | 118 | 14 | 0.8206 | 0.8571 | 0.8571 | — |
| Teacher | 135 | 10 | 0.8119 | 0.9000 | 0.9000 | — |

## Summary

Flagged: Engineer (Occupation, validation split); Nurse (Occupation, validation split); Scientist (Occupation, validation split); Engineer (Occupation, out-of-fold); Scientist (Occupation, out-of-fold). Occupations have 9–18 true-High validation rows and 68–82 out-of-fold, so read each flag with its interval. A flag whose interval still contains the overall value is consistent with noise. With 13 occupations, about one interval in 20 would exclude the overall value by chance alone, and the validation rows are part of the out-of-fold rows, so the two views are not independent confirmations.

Very likely synthetic dataset with near-uniform demographics: this checks the model, not real-world fairness.
