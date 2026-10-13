# Re-tuning XGBoost on the 11 v2 features (CV only)

Script: `src/models/tune_models_11feature.py`. **The test set was not used.** 9,350 train + validation rows; 5-fold stratified CV on train+val; preprocessing fitted inside each fold; early stopping (50 rounds, mlogloss) on a 15% split of each fold's training part; 60 random-search trials scored by balanced accuracy. Every trial and fold: `reports/tuning_trials_11feature.csv`.

## Top 5 trials (search CV, early-stopped)

| Rank | Balanced accuracy (mean ± std) | High recall | Median rounds | Params |
|---|---|---|---|---|
| 1 | 0.8107 ± 0.0053 | 0.8760 | 49 | `{"subsample": 0.8, "sample_weighting": "none", "min_child_weight": 3, "max_depth": 3, "learning_rate": 0.2, "gamma": 0, "colsample_bytree": 0.8}` |
| 2 | 0.8098 ± 0.0055 | 0.8750 | 38 | `{"subsample": 0.8, "sample_weighting": "none", "min_child_weight": 5, "max_depth": 4, "learning_rate": 0.2, "gamma": 0.1, "colsample_bytree": 0.8}` |
| 3 | 0.8097 ± 0.0047 | 0.8760 | 281 | `{"subsample": 0.8, "sample_weighting": "none", "min_child_weight": 5, "max_depth": 4, "learning_rate": 0.03, "gamma": 0.1, "colsample_bytree": 0.8}` |
| 4 | 0.8092 ± 0.0054 | 0.8760 | 219 | `{"subsample": 0.8, "sample_weighting": "none", "min_child_weight": 1, "max_depth": 3, "learning_rate": 0.05, "gamma": 0.1, "colsample_bytree": 1.0}` |
| 5 | 0.8091 ± 0.0052 | 0.8750 | 271 | `{"subsample": 0.8, "sample_weighting": "none", "min_child_weight": 1, "max_depth": 4, "learning_rate": 0.03, "gamma": 0.1, "colsample_bytree": 0.8}` |

## Best trial vs served v2, same folds, both fitted in deployable form

Best trial refitted with `n_estimators = 49` (median early-stopped rounds) on each whole fold training part; v2 with its served params (`{"subsample": 0.8, "n_estimators": 300, "min_child_weight": 3, "max_depth": 3, "learning_rate": 0.03, "gamma": 0, "colsample_bytree": 1.0}`, sample weighting `none`).

| Metric | v2 served | Best trial | Paired difference (best − v2) |
|---|---|---|---|
| balanced_accuracy | 0.8113 ± 0.0070 | 0.8098 ± 0.0075 | -0.0014 ± 0.0019 |
| macro_f1 | 0.8239 ± 0.0082 | 0.8225 ± 0.0087 | -0.0015 ± 0.0022 |
| high_recall | 0.8771 ± 0.0124 | 0.8760 ± 0.0143 | -0.0010 ± 0.0023 |

**Decision: KEEP v2.** Mean paired balanced-accuracy difference -0.0014, std of the paired differences 0.0019. No served file was changed.

Libraries: python 3.13.13, xgboost 3.4.1, scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.5. Very likely synthetic dataset: prototype-level evidence only.
