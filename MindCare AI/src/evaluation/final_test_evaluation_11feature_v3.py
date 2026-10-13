"""THIRD and disclosed use of the 3-class test set (2026-10-11): one final evaluation of the saved
11-feature v3 model (untuned XGBoost, balanced sample weights) built by
src/models/train_11feature_v3_balanced.py. Authorized explicitly by the project owner for this retrain
(see CLAUDE.md, "TEST SET USED - 2026-10-11").

Evaluates the saved files exactly as they are: no refitting, tuning or model selection follows from
these numbers. Refuses to run if its report already exists, so the test set is scored once.

Sanity check requested with the task: balanced accuracy about 0.81. A gap of 0.03 or more is reported
as a failed sanity check to investigate, not silently accepted.

Run from MindCare AI/: python -m src.evaluation.final_test_evaluation_11feature_v3
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.build_3class_target import bin_anxiety_level
from src.models.train_11feature_v3_balanced import (
    DATA_PATH, FEATURES, MODEL_PATH, PREPROCESSOR_PATH, REPORT_JSON as TRAIN_REPORT, evaluate, metrics_table,
    split_indices,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "reports" / "final_test_evaluation_11feature_v3.json"
REPORT_MD = ROOT / "reports" / "final_test_evaluation_11feature_v3.md"
SANITY_TARGET = 0.81
SANITY_TOLERANCE = 0.03


def main() -> None:
    if REPORT_JSON.exists() or REPORT_MD.exists():
        raise SystemExit("The v3 test evaluation has already been run - the test set is used once.")
    train = json.loads(TRAIN_REPORT.read_text(encoding="utf-8"))

    df = pd.read_csv(DATA_PATH)
    _, _, test_idx = split_indices(df)
    y_test = bin_anxiety_level(df["Anxiety Level (1-10)"].to_numpy())[test_idx]
    preprocessor, model = joblib.load(PREPROCESSOR_PATH), joblib.load(MODEL_PATH)
    test = evaluate(y_test, model.predict_proba(preprocessor.transform(df.iloc[test_idx][FEATURES])).argmax(axis=1))

    gap = test["balanced_accuracy"] - SANITY_TARGET
    sanity_ok = abs(gap) < SANITY_TOLERANCE
    val = train["validation"]
    deltas = {k: test[k] - val[k] for k in ("balanced_accuracy", "macro_f1", "accuracy", "high_recall")}
    result = {
        "test_set_use": "third, disclosed (2026-10-11)",
        "model": train["model"],
        "artifacts": train["artifacts"],
        "library_versions": train["library_versions"],
        "test": test,
        "validation": val,
        "test_minus_validation": deltas,
        "sanity_check": {"target_balanced_accuracy": SANITY_TARGET, "tolerance": SANITY_TOLERANCE,
                         "gap": gap, "passed": sanity_ok},
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    REPORT_MD.write_text(
        "# Final test evaluation: 11-feature v3 (untuned XGBoost, balanced weights)\n\n"
        "**Third, disclosed use of the 3-class test set (2026-10-11)**, authorized by the project owner for "
        "this retrain. The saved model was scored once, as is; nothing was refitted or tuned afterwards. "
        "**Not the served model.**\n\n"
        f"- Artifacts: `{train['artifacts'][0]}`, `{train['artifacts'][1]}`\n"
        f"- Libraries: {', '.join(f'{k} {v}' for k, v in train['library_versions'].items())}\n"
        f"- Sanity check (balanced accuracy about {SANITY_TARGET}): {test['balanced_accuracy']:.4f}, gap {gap:+.4f} -> "
        f"**{'PASSED' if sanity_ok else 'FAILED - investigate'}** (tolerance {SANITY_TOLERANCE})\n\n"
        "## Test (1,650 rows)\n\n" + metrics_table(test) + "\n\n"
        "## Validation, same model (1,650 rows)\n\n" + metrics_table(val) + "\n\n"
        "## Test minus validation\n\n"
        + "\n".join(f"- {k}: {v:+.4f}" for k, v in deltas.items()) + "\n\n"
        "Synthetic-looking dataset: prototype-level numbers, not clinical validation.\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps({"test": {k: test[k] for k in ("balanced_accuracy", "macro_f1", "accuracy", "high_recall")},
                      "per_class": test["per_class"], "confusion_matrix": test["confusion_matrix"]["rows_true_cols_pred"],
                      "test_minus_validation": deltas, "sanity_check": result["sanity_check"]}, indent=2))


if __name__ == "__main__":
    main()
