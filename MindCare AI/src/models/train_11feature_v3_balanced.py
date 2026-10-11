"""Retrain the 11-feature v2 feature set as "v3": UNTUNED XGBoost with balanced sample weights and a
freshly fitted preprocessor (requested 2026-10-11). Development and validation only - this script
never transforms, predicts on or scores the test rows. The single, disclosed test evaluation is
src/evaluation/final_test_evaluation_11feature_v3.py.

- Data: data/raw/mindcare_dataset_final.csv (11,000 rows). Target: Anxiety Level 1-3 Low, 4-6 Medium,
  7-10 High (src/build_3class_target.py).
- Split 70/15/15, seed 42, stratified on Severity, exactly as src/rebuild_preprocessor.py. The split is
  re-derived and asserted identical to the row indices saved in mindcare_processed_splits.npz.
- StandardScaler + OneHotEncoder fitted on the 7,700 training rows only.
- XGBoost library defaults (objective multi:softprob, seed 42), sample_weight = balanced.
- New files only, never the served v2 ones:
    data/processed/mindcare_preprocessor_11feature_v3.pkl
    data/processed/mindcare_final_model_11feature_v3_xgb_balanced.pkl
    reports/train_11feature_v3_balanced.json / .md   (validation metrics + library versions)

Run from MindCare AI/: python -m src.models.train_11feature_v3_balanced
"""

from __future__ import annotations

import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from src.build_3class_target import bin_anxiety_level

SEED = 42
ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raw" / "mindcare_dataset_final.csv"
SAVED_SPLITS_PATH = ROOT / "data" / "processed" / "mindcare_processed_splits.npz"
SERVED_FILES = [
    ROOT / "data" / "processed" / "mindcare_preprocessor_11feature_v2.pkl",
    ROOT / "data" / "processed" / "mindcare_final_model_11feature_v2_xgb.pkl",
]
PREPROCESSOR_PATH = ROOT / "data" / "processed" / "mindcare_preprocessor_11feature_v3.pkl"
MODEL_PATH = ROOT / "data" / "processed" / "mindcare_final_model_11feature_v3_xgb_balanced.pkl"
REPORT_JSON = ROOT / "reports" / "train_11feature_v3_balanced.json"
REPORT_MD = ROOT / "reports" / "train_11feature_v3_balanced.md"

NUMERIC_FEATURES = [
    "Sleep Hours", "Physical Activity (hrs/week)", "Caffeine Intake (mg/day)", "Stress Level (1-10)",
    "Heart Rate (bpm)", "Breathing Rate (breaths/min)", "Therapy Sessions (per month)",
    "Diet Quality (1-10)", "Age",
]
CATEGORICAL_FEATURES = ["Occupation", "Family History of Anxiety"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
CLASSES = ["Low", "Medium", "High"]
HIGH = 2


def split_indices(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """70/15/15 stratified on Severity, seed 42 - the project's one split. Asserted against the saved
    indices so every model in this project is compared on the same rows."""
    severity = LabelEncoder().fit_transform(df["Severity"])
    idx = np.arange(len(df))
    train_idx, temp_idx = train_test_split(idx, test_size=0.30, random_state=SEED, stratify=severity)
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.50, random_state=SEED, stratify=severity[temp_idx])
    with np.load(SAVED_SPLITS_PATH) as saved:
        for name, ours in (("train", train_idx), ("val", val_idx), ("test", test_idx)):
            assert np.array_equal(saved[f"{name}_original_idx"], ours), f"{name} split differs from the saved one"
    assert (len(train_idx), len(val_idx), len(test_idx)) == (7700, 1650, 1650)
    return train_idx, val_idx, test_idx


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])


def build_model() -> XGBClassifier:
    # Library defaults on purpose (untuned); only the objective, metric and seed are fixed.
    return XGBClassifier(objective="multi:softprob", eval_metric="mlogloss", random_state=SEED, n_jobs=-1)


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=[0, 1, 2], zero_division=0)
    return {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "per_class": {
            c: {"precision": float(precision[i]), "recall": float(recall[i]), "f1": float(f1[i]), "support": int(support[i])}
            for i, c in enumerate(CLASSES)
        },
        "high_recall": float(recall[HIGH]),
        "confusion_matrix": {"labels": CLASSES, "rows_true_cols_pred": confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist()},
    }


def library_versions() -> dict[str, str]:
    return {"python": platform.python_version(), "xgboost": xgboost.__version__, "scikit-learn": sklearn.__version__,
            "numpy": np.__version__, "pandas": pd.__version__}


def metrics_table(m: dict) -> str:
    lines = [f"- Balanced accuracy **{m['balanced_accuracy']:.4f}**, macro F1 **{m['macro_f1']:.4f}**, "
             f"accuracy {m['accuracy']:.4f}, High recall **{m['high_recall']:.4f}** (n = {m['n']})", "",
             "| Class | Precision | Recall | F1 | Support |", "|---|---|---|---|---|"]
    for c in CLASSES:
        p = m["per_class"][c]
        lines.append(f"| {c} | {p['precision']:.4f} | {p['recall']:.4f} | {p['f1']:.4f} | {p['support']} |")
    lines += ["", "Confusion matrix (rows = true, columns = predicted):", "",
              "| true \\ pred | Low | Medium | High |", "|---|---|---|---|"]
    for c, row in zip(CLASSES, m["confusion_matrix"]["rows_true_cols_pred"]):
        lines.append(f"| {c} | " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def main() -> None:
    for path in (PREPROCESSOR_PATH, MODEL_PATH):
        assert path not in SERVED_FILES
        if path.exists():
            raise SystemExit(f"{path.relative_to(ROOT)} already exists - refusing to overwrite.")
    served_before = {p: p.read_bytes() for p in SERVED_FILES}

    df = pd.read_csv(DATA_PATH)
    assert len(df) == 11000
    y_all = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())
    train_idx, val_idx, _ = split_indices(df)  # test indices deliberately discarded here
    train_rows, val_rows = df.iloc[train_idx][FEATURES], df.iloc[val_idx][FEATURES]
    y_train, y_val = y_all[train_idx], y_all[val_idx]

    preprocessor = build_preprocessor()
    x_train = preprocessor.fit_transform(train_rows)  # fitted on training rows only
    weights = compute_sample_weight("balanced", y_train)
    model = build_model()
    model.fit(x_train, y_train, sample_weight=weights)

    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    joblib.dump(model, MODEL_PATH)
    # Score the reloaded copies, exactly as a service would load them.
    val_pred = joblib.load(MODEL_PATH).predict_proba(joblib.load(PREPROCESSOR_PATH).transform(val_rows)).argmax(axis=1)
    val = evaluate(y_val, val_pred)
    assert all(p.read_bytes() == b for p, b in served_before.items()), "served files changed"

    result = {
        "model": "XGBClassifier, library defaults (untuned), balanced sample weights",
        "xgb_params": {k: v for k, v in model.get_params().items() if v is not None},
        "features": FEATURES,
        "seed": SEED,
        "split": {"method": "70/15/15 stratified on Severity, seed 42 (= mindcare_processed_splits.npz)",
                  "train": len(train_idx), "val": len(val_idx), "test": 1650},
        "train_class_counts": {c: int((y_train == i).sum()) for i, c in enumerate(CLASSES)},
        "sample_weight_per_class": {c: float(weights[y_train == i][0]) for i, c in enumerate(CLASSES)},
        "library_versions": library_versions(),
        "artifacts": [str(PREPROCESSOR_PATH.relative_to(ROOT)).replace("\\", "/"),
                      str(MODEL_PATH.relative_to(ROOT)).replace("\\", "/")],
        "validation": val,
        "test_set_used": False,
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    REPORT_MD.write_text(
        "# 11-feature v3: untuned XGBoost, balanced sample weights (validation)\n\n"
        "Built by `src/models/train_11feature_v3_balanced.py`. **Not the served model** (that is the tuned, "
        "unweighted 11-feature v2). The test set was not touched by this script.\n\n"
        f"- Features (11): {', '.join(FEATURES)}\n"
        f"- Split: {result['split']['method']}; train {len(train_idx)}, validation {len(val_idx)}\n"
        f"- Preprocessor: StandardScaler + OneHotEncoder fitted on the {len(train_idx)} training rows only\n"
        f"- Sample weights (balanced): {', '.join(f'{c} {w:.3f}' for c, w in result['sample_weight_per_class'].items())}\n"
        f"- Libraries: {', '.join(f'{k} {v}' for k, v in result['library_versions'].items())}\n"
        f"- Artifacts: `{result['artifacts'][0]}`, `{result['artifacts'][1]}`\n\n"
        "## Validation (1,650 rows)\n\n" + metrics_table(val) + "\n\n"
        "Synthetic-looking dataset: prototype-level numbers, not clinical validation.\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps({"validation": {k: val[k] for k in ("balanced_accuracy", "macro_f1", "accuracy", "high_recall")},
                      "confusion_matrix": val["confusion_matrix"]["rows_true_cols_pred"],
                      "versions": result["library_versions"]}, indent=2))


if __name__ == "__main__":
    main()
