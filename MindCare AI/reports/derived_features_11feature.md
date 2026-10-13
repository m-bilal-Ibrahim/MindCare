# Derived-feature stage vs the 11-feature v2 model (5-fold CV, train + validation)

Script: `src/experiments/derived_features_11feature.py`. **Validation/CV only; the test set was not loaded.** 9,350 rows, 5-fold stratified on the 3-class label (shuffled, seed 42); scaler and encoder fitted inside each fold; both arms use the served v2 XGBoost hyperparameters, unweighted.

Derived features (fixed constants, nothing learned): `sleep_deficit = max(0, 8 - sleep)`, `stress_x_sleepdef = stress * sleep_deficit`, `arousal_index = (HR-70)/70 + (BR-16)/16`, `lifestyle_score = (min(sleep/8,1) + min(activity/5,1) + diet/10)/3`, `caffeine_per_sleep = caffeine / sleep`.

| Metric | 11 features (mean ± std) | 11 + 5 derived | Paired gain (mean ± std) | Gain per fold |
|---|---|---|---|---|
| balanced_accuracy | 0.8113 ± 0.0070 | 0.8087 ± 0.0067 | -0.0026 ± 0.0022 | -0.0014, -0.0045, -0.0054, -0.0007, -0.0008 |
| macro_f1 | 0.8239 ± 0.0082 | 0.8207 ± 0.0083 | -0.0032 ± 0.0013 | -0.0029, -0.0039, -0.0049, -0.0028, -0.0015 |
| high_recall | 0.8771 ± 0.0124 | 0.8760 ± 0.0164 | -0.0010 ± 0.0043 | +0.0000, -0.0052, -0.0052, +0.0000, +0.0052 |

**Decision:** DO NOT KEEP the derived features. Rule: keep only if the mean paired balanced-accuracy gain (-0.0026) is larger than one standard deviation of the paired gains (0.0022).

Libraries: python 3.13.13, xgboost 3.4.1, scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.5. Very likely synthetic dataset: prototype-level evidence only.
