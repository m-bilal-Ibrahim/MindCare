# Occupation gaps for the served v2 XGBoost (out-of-fold)

Script: `src/experiments/occupation_gap_v2.py` (`reports/occupation_gap_v2.json`). **The test set was not used; no served file
or threshold changed.** Out-of-fold over the 9,350 train + validation rows (same 5 folds as the ablation study, v2's
tuned settings), 968 true-High patients. For each of the 13 occupations, its true-High patients
are compared with all other true-High patients. Gap = occupation − all others. Bootstrap: 2,000 resamples, seed
42, patients resampled within each group. Fisher exact is two-sided; Holm adjustment is across the 13
occupations, separately for each metric. Bold = Holm p < 0.05. Guard: Scientist's counts match
`reports/lr_candidate_evaluation.json`.

## Model High recall (predicted class = High)

| Occupation | True High | Model high recall | All others | Gap | Bootstrap 95% CI | Fisher p | Holm p (13) |
|---|---|---|---|---|---|---|---|
| **Scientist** | 75 | 56/75 (74.7%) | 88.8% | -0.141 | -0.250 to -0.048 | 0.00136 | **0.0177** |
| Engineer | 77 | 63/77 (81.8%) | 88.2% | -0.064 | -0.155 to +0.018 | 0.105 | 1 |
| Lawyer | 74 | 62/74 (83.8%) | 88.0% | -0.042 | -0.130 to +0.041 | 0.272 | 1 |
| Chef | 71 | 61/71 (85.9%) | 87.8% | -0.019 | -0.104 to +0.057 | 0.577 | 1 |
| Freelancer | 79 | 68/79 (86.1%) | 87.9% | -0.018 | -0.105 to +0.055 | 0.595 | 1 |
| Teacher | 68 | 59/68 (86.8%) | 87.8% | -0.010 | -0.095 to +0.067 | 0.848 | 1 |
| Doctor | 78 | 68/78 (87.2%) | 87.8% | -0.006 | -0.089 to +0.066 | 0.858 | 1 |
| Student | 82 | 74/82 (90.2%) | 87.5% | +0.028 | -0.044 to +0.091 | 0.598 | 1 |
| Musician | 79 | 72/79 (91.1%) | 87.4% | +0.037 | -0.034 to +0.100 | 0.473 | 1 |
| Other | 75 | 69/75 (92.0%) | 87.3% | +0.047 | -0.020 to +0.106 | 0.277 | 1 |
| Athlete | 70 | 65/70 (92.9%) | 87.3% | +0.056 | -0.012 to +0.115 | 0.254 | 1 |
| Nurse | 71 | 66/71 (93.0%) | 87.3% | +0.057 | -0.010 to +0.113 | 0.191 | 1 |
| Artist | 69 | 66/69 (95.7%) | 87.1% | +0.086 | +0.028 to +0.133 | 0.0355 | 0.426 |

## Review-flag catch rate (P(High) ≥ 0.025)

| Occupation | True High | Review-flag catch rate (0.025) | All others | Gap | Bootstrap 95% CI | Fisher p | Holm p (13) |
|---|---|---|---|---|---|---|---|
| Scientist | 75 | 70/75 (93.3%) | 96.4% | -0.031 | -0.097 to +0.021 | 0.199 | 1 |
| Student | 82 | 77/82 (93.9%) | 96.4% | -0.025 | -0.084 to +0.025 | 0.233 | 1 |
| Musician | 79 | 75/79 (94.9%) | 96.3% | -0.014 | -0.070 to +0.030 | 0.535 | 1 |
| Teacher | 68 | 65/68 (95.6%) | 96.2% | -0.006 | -0.064 to +0.037 | 0.74 | 1 |
| Other | 75 | 72/75 (96.0%) | 96.2% | -0.002 | -0.053 to +0.038 | 0.76 | 1 |
| Engineer | 77 | 74/77 (96.1%) | 96.2% | -0.001 | -0.051 to +0.039 | 1 | 1 |
| Freelancer | 79 | 76/79 (96.2%) | 96.2% | +0.000 | -0.047 to +0.037 | 1 | 1 |
| Artist | 69 | 67/69 (97.1%) | 96.1% | +0.010 | -0.036 to +0.044 | 1 | 1 |
| Athlete | 70 | 68/70 (97.1%) | 96.1% | +0.010 | -0.037 to +0.045 | 1 | 1 |
| Nurse | 71 | 69/71 (97.2%) | 96.1% | +0.011 | -0.037 to +0.045 | 1 | 1 |
| Lawyer | 74 | 72/74 (97.3%) | 96.1% | +0.012 | -0.034 to +0.045 | 1 | 1 |
| Doctor | 78 | 76/78 (97.4%) | 96.1% | +0.014 | -0.026 to +0.044 | 0.762 | 1 |
| Chef | 71 | 70/71 (98.6%) | 96.0% | +0.026 | -0.009 to +0.050 | 0.513 | 1 |

## Reading

- **Model High recall:** significant after Holm: Scientist. Raw p < 0.05: Artist, Scientist.
- **Review-flag catch rate:** significant after Holm: none. Raw p < 0.05: none.
- **Scientist:** model High recall 56/75 (74.7%) vs 88.8%,
  gap -0.141 (95% CI -0.250 to -0.048), Holm p 0.0177. The review flag
  catches 70/75 (93.3%) vs 96.4% (Holm p 1).
- Occupation has no relationship with Stress Level in this dataset (ANOVA p = 0.93, CLAUDE.md), and the data are very likely
  synthetic. These tests show whether a gap is larger than sampling noise; they do not explain it. Out-of-fold predictions come
  from five models.
