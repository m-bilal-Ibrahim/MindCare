# 11-feature v3: untuned XGBoost, balanced sample weights (validation)

Built by `src/models/train_11feature_v3_balanced.py`. **Not the served model** (that is the tuned, unweighted 11-feature v2). The test set was not touched by this script.

- Features (11): Sleep Hours, Physical Activity (hrs/week), Caffeine Intake (mg/day), Stress Level (1-10), Heart Rate (bpm), Breathing Rate (breaths/min), Therapy Sessions (per month), Diet Quality (1-10), Age, Occupation, Family History of Anxiety
- Split: 70/15/15 stratified on Severity, seed 42 (= mindcare_processed_splits.npz); train 7700, validation 1650
- Preprocessor: StandardScaler + OneHotEncoder fitted on the 7700 training rows only
- Sample weights (balanced): Low 0.705, Medium 0.789, High 3.196
- Libraries: python 3.13.13, xgboost 3.4.1, scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.5
- Artifacts: `data/processed/mindcare_preprocessor_11feature_v3.pkl`, `data/processed/mindcare_final_model_11feature_v3_xgb_balanced.pkl`

## Validation (1,650 rows)

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

Synthetic-looking dataset: prototype-level numbers, not clinical validation.
