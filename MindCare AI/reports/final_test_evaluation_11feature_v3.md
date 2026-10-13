# Final test evaluation: 11-feature v3 (untuned XGBoost, balanced weights)

**Third, disclosed use of the 3-class test set (2026-10-11)**, authorized by the project owner for this retrain. The saved model was scored once, as is; nothing was refitted or tuned afterwards. **Not the served model.**

- Artifacts: `data/processed/mindcare_preprocessor_11feature_v3.pkl`, `data/processed/mindcare_final_model_11feature_v3_xgb_balanced.pkl`
- Libraries: python 3.13.13, xgboost 3.4.1, scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.5
- Sanity check (balanced accuracy about 0.81): 0.8030, gap -0.0070 -> **PASSED** (tolerance 0.03)

## Test (1,650 rows)

- Balanced accuracy **0.8030**, macro F1 **0.8088**, accuracy 0.7703, High recall **0.8994** (n = 1650)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Low | 0.7755 | 0.7695 | 0.7725 | 781 |
| Medium | 0.7255 | 0.7400 | 0.7327 | 700 |
| High | 0.9441 | 0.8994 | 0.9212 | 169 |

Confusion matrix (rows = true, columns = predicted):

| true \ pred | Low | Medium | High |
|---|---|---|---|
| Low | 601 | 179 | 1 |
| Medium | 174 | 518 | 8 |
| High | 0 | 17 | 152 |

## Validation, same model (1,650 rows)

- Balanced accuracy **0.7960**, macro F1 **0.8060**, accuracy 0.7612, High recall **0.8970** (n = 1650)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Low | 0.7620 | 0.7571 | 0.7595 | 778 |
| Medium | 0.7159 | 0.7341 | 0.7249 | 707 |
| High | 0.9737 | 0.8970 | 0.9338 | 165 |

Confusion matrix (rows = true, columns = predicted):

| true \ pred | Low | Medium | High |
|---|---|---|---|
| Low | 589 | 189 | 0 |
| Medium | 184 | 519 | 4 |
| High | 0 | 17 | 148 |

## Test minus validation

- balanced_accuracy: +0.0069
- macro_f1: +0.0028
- accuracy: +0.0091
- high_recall: +0.0024

Synthetic-looking dataset: prototype-level numbers, not clinical validation.
