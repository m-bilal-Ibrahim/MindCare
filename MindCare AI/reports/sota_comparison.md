# Comparison with published methods

Script: `src/experiments/sota_baselines.py` (results also in `reports/sota_baselines.json`). **The test set was not used; no
served file or threshold was changed.** Seed 42.

## How to read this

**Our dataset is very likely synthetic.** It appears to come from the Kaggle "Social Anxiety Dataset" [8]. That page calls it
a "synthetic dataset", although its disclaimer also says it was "compiled from real-world survey responses". Our own EDA found
near-uniform demographics, no missing values and templated recommendation text. The studies in Table A use other populations,
targets (mostly binary), instruments and validation schemes, and most use real survey or sensor data. **Their numbers are context,
not a ranking**, and nothing here should be read as MindCare beating or trailing any of them. Table B is the only like-for-like
comparison: the published *methods* re-run on *our* data, folds and target.

## Table A: the literature (their data, their numbers; not directly comparable)

Only facts read on each paper's own page. Where a page did not give a number, none is shown.

| Study | Their data | Method and validation | Target | Their reported numbers |
|---|---|---|---|---|
| Nishwa, Abbas & Lee (2026), *Front. Psychiatry* 17:1727014 [1] | Kaggle "Social Anxiety Dataset" (the source of **our** data), 11,000 adults aged 18-64 | 7 regressors (gradient boosting, RF, lasso, linear, elastic net, SVR, MLP); 80/20 split, 5-fold CV tuning | Anxiety Level 1-10 (regression) | MAE, MAPE, RMSE, R² named but **no numeric values given** (normalised radar chart only); GB and RF ranked best |
| Qasrawi et al. (2022), *JMIR Form. Res.* 6(8):e32736 [2] | Real survey, 3,984 schoolchildren aged 10-15, West Bank, 2013-14 | RF, ANN, DT, SVM, NB; 70:20:10 split, CV grid search | Anxiety normal vs abnormal (GAD-7 ≥ 5), binary | Anxiety accuracy SVM 76.4%, RF 78.6% (Table 7; text gives 76.5% / 78.4%; abstract gives different figures) |
| Rois et al. (2021), *J. Health Popul. Nutr.* 40:50 [3] | Real online survey, 355 Bangladeshi university students | DT, RF, SVM (poly-2, linear), LR; 70/30 split × 11 runs, plus 3/5/10-fold CV | Perceived stress in last 12 months, yes/no (30.7% yes) | RF hold-out accuracy 0.8929, sensitivity 0.8953, specificity 0.8853; RF AUC 0.8715 (one split); LR accuracy 0.7723 (abstract differs) |
| Moon & Woo (2025), *Front. Public Health* 12:1504739 [4] | Real national survey (KYRBS 2020-23), 213,820 Korean adolescents aged 12-18 | RF and ANN after LASSO / SelectKBest / XGBoost feature selection, SMOTE; validation scheme not stated | GAD-7 ≥ 10, binary (17.9% positive) | Best accuracy ANN+SelectKBest 82%, AUC 81%, sensitivity 44%; RF+XGBoost features AUC 82%, sensitivity 64% |
| Vu et al. (2025), *BMC Med. Inform. Decis. Mak.* 25:83 [5] | Real national survey (NHANES 2013-14), 5,372 US adults (9.5% depressed) | LR, RF, NB, SVM, XGBoost, LightGBM; random undersampling; 80/20 split, 5-fold CV grid search | Depression, PHQ-9 ≥ 10, binary | XGBoost accuracy 0.69, AUC 0.69, F1 0.69, sensitivity 0.68; SVM 0.68 / 0.68 / 0.67; LR 0.66 / 0.66 / 0.65; LightGBM 0.62 / 0.62 / 0.63 |
| Almadhor et al. (2023), *Sensors* 23(15):6664 [6] | WESAD lab recordings (chest sensor), 14 subjects as described | SelectKBest + SMOTE + stacking ensemble; k-fold CV (k not given), no subject-independent split described | Stress vs calm, binary | Stacking accuracy 0.997, F1 0.998; LR alone accuracy 0.978 |
| Dahal, Bogue-Jimenez & Doblas (2023), *Sensors* 23(11):5220 [7] | WESAD (15 subjects) and SWELL (22-25 subjects) HRV features | mRMR (8 features) + RF; each subject's rows split 70/30, so subjects appear in train and test | Stress vs no stress, binary | ≥ 99% per-subject accuracy; leave-one-subject-out on WESAD: accuracy 0.3143 to 0.949 by subject |

Two patterns from these pages matter here. First, the near-perfect WESAD results [6, 7] put the same subjects in training and
test; under leave-one-subject-out, [7] reports per-subject accuracy as low as 0.31. Second, several papers' abstracts disagree
with their own tables [2, 3]. Neither pattern is a reason to doubt our own results; they are reasons not to rank against them.

## Has anyone published on this exact dataset?

- **One peer-reviewed paper found:** Nishwa, Abbas & Lee (2026) [1] analyse the Kaggle dataset by Zhang Chenyuan (2024) at
  kaggle.com/datasets/natezhang123/social-anxiety-dataset, with 11,000 participants. They bin Anxiety Level into the same
  1-3 / 4-6 / 7-10 groups for descriptive statistics, but model it as a 1-10 regression and **give no numeric model scores**.
  So no published number exists to compare with ours. The paper does not say whether the data are real or synthetic.
- **Kaggle page [8]:** "Zhang Chenyuan and 2 collaborators", CC0, file `enhanced_anxiety_dataset.csv`, 19 columns. The Data Card
  describes it as synthetic (see above). The Code tab lists 24 notebooks; we did not review them, and they are not peer-reviewed.
- **Link to our file:** the 10 column names and the first three rows shown in the Kaggle preview match the first 10 columns and
  first three rows of `data/raw/mindcare_dataset_final.csv`. Our file has 23 columns. Its first 19 are the features the Data
  Card lists plus Anxiety Level, which fits the 19-column Kaggle file; the other four are Severity, Exercises, Sleep_Schedule and
  Nutrition. We checked only the preview, not the full file.
- A search on the exact column names ("Anxiety Level (1-10)", "Therapy Sessions (per month)") found only [1].

## Table B: like-for-like results on our data

The same 5 folds as `src/experiments/ablation_study.py`: the 9,350 train + validation rows, stratified on the 3-class
label, shuffled, seed 42, scaling and one-hot encoding fitted inside each fold, 11 v2 features. Mean ± std over the 5 folds.
"Model High recall" means the predicted class is High; the review flag is not applied to any model here. v2 re-run here
reproduces the per-fold scores in `reports/ablation_study.json` exactly (guard in the script).

| Model | Setup from | Balanced accuracy | Macro-F1 | Model High recall |
|---|---|---|---|---|
| Served v2: XGBoost (tuned) | this project | 0.8113 ± 0.0070 | 0.8239 ± 0.0082 | 0.8771 ± 0.0124 |
| RBF SVM (C=20, γ=0.001) | Qasrawi et al. 2022 | 0.8113 ± 0.0045 | 0.8236 ± 0.0054 | 0.8739 ± 0.0226 |
| MLP (1×500 logistic, max_iter 500) | Qasrawi et al. 2022 | 0.8074 ± 0.0049 | 0.8157 ± 0.0080 | 0.8822 ± 0.0202 |
| LightGBM (defaults) | Vu et al. 2025 | 0.8025 ± 0.0056 | 0.8158 ± 0.0081 | 0.8760 ± 0.0161 |
| LightGBM + random undersampling | Vu et al. 2025 | 0.7898 ± 0.0083 | 0.7840 ± 0.0106 | 0.8957 ± 0.0122 |
| Logistic regression (defaults) | Rois et al. 2021; Vu et al. 2025 | 0.8119 ± 0.0049 | 0.8218 ± 0.0068 | 0.8791 ± 0.0228 |

Settings are the ones each paper states; anything not stated is the library default. Vu et al. [5] tuned LightGBM by grid search
but do not list the chosen values on the page, so LightGBM uses defaults. Their random undersampling was applied inside each
training fold, cutting every class down to the High count (2,325, 2,325, 2,322, 2,322, 2,322 training rows per fold). Qasrawi
et al. [2] used Orange; anything Orange sets differently from scikit-learn's defaults is not reproduced.

**Paired comparison with v2** (per-fold difference, model − v2; same folds, so the differences are paired). The t-test is on the
5 fold balanced accuracies; McNemar is exact, on which of the 9,350 out-of-fold predictions each model gets right. Folds
share training data, so p-values are approximate; with 5 folds the t-test has little power, so "not significant" is not proof
of no difference.

| Model − v2 | Δ balanced acc. | Δ macro-F1 | Δ model High recall | t-test p: raw / Holm | McNemar p (OOF): raw / Holm | Only v2 right / only model right |
|---|---|---|---|---|---|---|
| RBF SVM (C=20, γ=0.001) | +0.0000 ± 0.0051 | -0.0004 ± 0.0050 | -0.0031 ± 0.0107 | 0.996 / 1.000 | 0.587 / 1 | 132 / 142 |
| MLP (1×500 logistic, max_iter 500) | -0.0038 ± 0.0031 | -0.0082 ± 0.0034 | +0.0052 ± 0.0097 | 0.051 / 0.152 | 0.00906 / 0.0272 | 268 / 210 |
| LightGBM (defaults) | -0.0087 ± 0.0043 | -0.0082 ± 0.0040 | -0.0010 ± 0.0057 | 0.011 / 0.043 | 6e-07 / 2.4e-06 | 281 / 174 |
| LightGBM + random undersampling | -0.0215 ± 0.0073 | -0.0399 ± 0.0096 | +0.0186 ± 0.0108 | 0.003 / 0.014 | 4.42e-23 / 2.21e-22 | 726 / 396 |
| Logistic regression (defaults) | +0.0006 ± 0.0053 | -0.0022 ± 0.0045 | +0.0021 ± 0.0119 | 0.803 / 1.000 | 0.908 / 1 | 148 / 151 |

**Reading.** No significant balanced-accuracy difference from v2 after Holm adjustment: RBF SVM (C=20, γ=0.001) (+0.0000), MLP (1×500 logistic, max_iter 500) (-0.0038), Logistic regression (defaults) (+0.0006). Significantly lower than v2: LightGBM (defaults) (-0.0087), LightGBM + random undersampling (-0.0215). None of the re-implemented methods beats v2 on our data. Undersampling trades overall quality for High recall (Δ model High recall +0.0186, Δ macro-F1 -0.0399); v2 gets its High coverage from the review flag instead. 4 of 5 re-implemented setups land within one point of v2's balanced accuracy despite very different model families, which fits the data ceiling noted in CLAUDE.md (most errors sit at the Anxiety Level 3/4 and 6/7 borders).

Libraries: python 3.13.13, scikit-learn 1.9.1, xgboost 3.4.1, lightgbm 4.7.0, numpy 2.5.3, pandas 3.0.5.

## Sources (pages actually opened)

- [1] https://pmc.ncbi.nlm.nih.gov/articles/PMC13230050 — doi:10.3389/fpsyt.2026.1727014
- [2] https://formative.jmir.org/2022/8/e32736 — doi:10.2196/32736
- [3] https://pmc.ncbi.nlm.nih.gov/articles/PMC8627029/ — doi:10.1186/s41043-021-00276-5
- [4] https://www.frontiersin.org/articles/10.3389/fpubh.2024.1504739/full — doi:10.3389/fpubh.2024.1504739
- [5] https://link.springer.com/article/10.1186/s12911-025-02903-1 (and its /tables/2) — doi:10.1186/s12911-025-02903-1
- [6] https://pmc.ncbi.nlm.nih.gov/articles/PMC10422546/ — doi:10.3390/s23156664
- [7] https://pmc.ncbi.nlm.nih.gov/articles/PMC10255919/ — doi:10.3390/s23115220
- [8] https://www.kaggle.com/datasets/natezhang123/social-anxiety-dataset (Data Card and Code tab)

Searched but not used: Priya, Garg & Tiwari (2020, *Procedia Comput. Sci.*): the ScienceDirect page asked for a CAPTCHA, so
it was not read. Garg et al. (2021, WESAD with RF): the PDF could not be opened as a page. Their numbers appear only in other
papers' summaries, so they are left out.
