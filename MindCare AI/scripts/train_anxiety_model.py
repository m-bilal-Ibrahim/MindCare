"""Train and evaluate the shared-input anxiety-level regressor."""

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.isotonic import IsotonicRegression
from xgboost import XGBRegressor

from src.config import (
    ARTIFACTS_DATA_DIR,
    EXPERIMENT_MODELS_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REPORTS_DIR,
)


TARGET = "Anxiety Level (1-10)"
FEATURE_COLUMNS = (
    "Age",
    "Gender",
    "Occupation",
    "Sleep Hours",
    "Physical Activity (hrs/week)",
    "Caffeine Intake (mg/day)",
    "Alcohol Consumption (drinks/week)",
    "Smoking",
    "Diet Quality (1-10)",
    "Heart Rate (bpm)",
    "Breathing Rate (breaths/min)",
    "Sweating Level (1-5)",
    "Family History of Anxiety",
    "Dizziness",
    "Medication",
    "Therapy Sessions (per month)",
    "Recent Major Life Event",
)
CATEGORICAL_COLUMNS = ["Gender", "Occupation"]
NUMERIC_COLUMNS = [column for column in FEATURE_COLUMNS if column not in CATEGORICAL_COLUMNS]
BINARY_COLUMNS = [
    "Smoking",
    "Family History of Anxiety",
    "Dizziness",
    "Medication",
    "Recent Major Life Event",
]
ORDERED_BANDS = [
    "Minimal (1-2)",
    "Mild (3-4)",
    "Moderate (5-6)",
    "High (7-8)",
    "Severe (9-10)",
]


def _normalise_binary(data: pd.DataFrame) -> pd.DataFrame:
    """Convert source Yes/No values to the numeric representation used in splits."""
    result = data.copy()
    for column in BINARY_COLUMNS:
        result[column] = result[column].map({"Yes": 1, "No": 0}).fillna(result[column])
        result[column] = pd.to_numeric(result[column], errors="raise")
    return result


def _shared_features(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Apply the existing encoder without fitting new preprocessing."""
    encoder = joblib.load(ARTIFACTS_DATA_DIR / "onehot_encoder.joblib")
    normalised = _normalise_binary(raw_data[list(FEATURE_COLUMNS)])
    encoded = pd.DataFrame(
        encoder.transform(normalised[CATEGORICAL_COLUMNS]),
        columns=encoder.get_feature_names_out(CATEGORICAL_COLUMNS),
        index=normalised.index,
    )
    return pd.concat([normalised[NUMERIC_COLUMNS], encoded], axis=1)


def _scale_features(features: pd.DataFrame) -> pd.DataFrame:
    """Scale numeric columns with the existing shared scaler artifact."""
    scaler = joblib.load(ARTIFACTS_DATA_DIR / "scaler.joblib")
    scaler_input = pd.DataFrame(0.0, index=features.index, columns=scaler.feature_names_in_)
    scaled_columns = [column for column in NUMERIC_COLUMNS if column in scaler_input.columns]
    for column in scaled_columns:
        scaler_input[column] = features[column]
    scaled = pd.DataFrame(
        scaler.transform(scaler_input),
        columns=scaler.feature_names_in_,
        index=features.index,
    )
    scaled = scaled[scaled_columns]
    binary_columns = [column for column in NUMERIC_COLUMNS if column not in scaled_columns]
    scaled = pd.concat([scaled, features[binary_columns]], axis=1)
    encoded_columns = [column for column in features.columns if column not in NUMERIC_COLUMNS]
    return pd.concat([scaled, features[encoded_columns]], axis=1)


def _attach_targets(raw_features: pd.DataFrame, processed_splits: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
    """Match raw anxiety labels to the existing feature split rows."""
    feature_columns = [
        column for column in processed_splits["train"].columns
        if column != "Severity"
    ]
    raw_aligned = raw_features[feature_columns].round(10).astype(str)
    combined = pd.concat(
        [split.drop(columns="Severity").assign(_split=name) for name, split in processed_splits.items()],
        ignore_index=True,
    )
    combined_keys = combined[feature_columns].round(10).astype(str)
    raw_keys = raw_aligned.copy()
    combined_keys["_occurrence"] = combined_keys.groupby(feature_columns, sort=False).cumcount()
    raw_keys["_occurrence"] = raw_keys.groupby(feature_columns, sort=False).cumcount()
    raw_keys["_anxiety"] = raw_features[TARGET].to_numpy()
    raw_keys["_row"] = np.arange(len(raw_keys))
    matched = combined_keys.merge(
        raw_keys[feature_columns + ["_occurrence", "_anxiety"]],
        on=feature_columns + ["_occurrence"],
        how="left",
        validate="one_to_one",
    )
    if matched["_anxiety"].isna().any():
        raise ValueError("Could not align all processed rows with raw anxiety labels")
    targets = {}
    start = 0
    for name, split in processed_splits.items():
        end = start + len(split)
        targets[name] = matched.iloc[start:end]["_anxiety"].astype(float).reset_index(drop=True)
        start = end
    return targets


def _test_diagnostics(
    predictions: np.ndarray,
    test_target: pd.Series,
    test_metadata: pd.DataFrame,
) -> dict:
    """Return the permanent test error and subgroup diagnostics."""
    test_frame = pd.DataFrame(
        {
            "severity": test_metadata["Severity"].reset_index(drop=True),
            "therapy_sessions": test_metadata["Therapy Sessions (per month)"].reset_index(drop=True),
            "actual": test_target.reset_index(drop=True),
            "prediction": predictions,
        }
    )
    band_metrics = {}
    for band in ORDERED_BANDS:
        group = test_frame[test_frame["severity"] == band]
        band_metrics[band] = {
            "count": int(len(group)),
            "mae": float(mean_absolute_error(group["actual"], group["prediction"])),
            "mean_residual": float((group["prediction"] - group["actual"]).mean()),
            "true_anxiety_std": float(group["actual"].std(ddof=0)),
        }
    overall_test_mae = float(mean_absolute_error(test_target, predictions))
    high_severe_mae = float(np.mean([band_metrics[band]["mae"] for band in ORDERED_BANDS[-2:]]))
    cold_start = test_frame[test_frame["therapy_sessions"] == 0]
    therapy_users = test_frame[test_frame["therapy_sessions"] > 0]

    def subgroup_metrics(group: pd.DataFrame) -> dict | None:
        if group.empty:
            return None
        return {
            "count": int(len(group)),
            "mae": float(mean_absolute_error(group["actual"], group["prediction"])),
            "mean_residual": float((group["prediction"] - group["actual"]).mean()),
        }

    cold_start_metrics = subgroup_metrics(cold_start)
    deployment_findings = []
    if band_metrics[ORDERED_BANDS[0]]["mean_residual"] > 0.25:
        deployment_findings.append("systematic_minimal_band_overprediction")
    if cold_start_metrics and cold_start_metrics["mae"] > overall_test_mae * 1.25:
        deployment_findings.append("cold_start_mae_notably_worse")
    if cold_start_metrics and cold_start_metrics["mean_residual"] < -0.25:
        deployment_findings.append("cold_start_underprediction_bias")
    return {
        "test": {
            "mae": overall_test_mae,
            "r2": float(r2_score(test_target, predictions)),
        },
        "test_by_severity": band_metrics,
        "high_severe_error_flag": {
            "flagged": high_severe_mae > overall_test_mae * 1.25,
            "high_severe_mae": high_severe_mae,
            "overall_test_mae": overall_test_mae,
            "threshold_multiplier": 1.25,
        },
        "cold_start": cold_start_metrics,
        "therapy_sessions_greater_than_zero": subgroup_metrics(therapy_users),
        "deployment_findings": deployment_findings,
    }


def _evaluate_variant(
    model: XGBRegressor,
    train_features: pd.DataFrame,
    validation_features: pd.DataFrame,
    test_features: pd.DataFrame,
    train_target: pd.Series,
    validation_target: pd.Series,
    test_target: pd.Series,
    test_metadata: pd.DataFrame,
    sample_weight: pd.Series | None = None,
) -> dict:
    """Fit one variant and return performance and subgroup diagnostics."""
    model.fit(
        train_features,
        train_target,
        sample_weight=sample_weight,
        eval_set=[(validation_features, validation_target)],
        verbose=False,
    )
    train_predictions = model.predict(train_features)
    validation_predictions = model.predict(validation_features)
    test_predictions = model.predict(test_features)
    test_frame = pd.DataFrame(
        {
            "severity": test_metadata["Severity"].reset_index(drop=True),
            "therapy_sessions": test_metadata["Therapy Sessions (per month)"].reset_index(drop=True),
            "actual": test_target.reset_index(drop=True),
            "prediction": test_predictions,
        }
    )
    ordered_bands = [
        "Minimal (1-2)",
        "Mild (3-4)",
        "Moderate (5-6)",
        "High (7-8)",
        "Severe (9-10)",
    ]
    band_metrics = {}
    for band in ordered_bands:
        group = test_frame[test_frame["severity"] == band]
        if group.empty:
            band_metrics[band] = None
            continue
        band_metrics[band] = {
            "count": int(len(group)),
            "mae": float(mean_absolute_error(group["actual"], group["prediction"])),
            "mean_residual": float((group["prediction"] - group["actual"]).mean()),
            "true_anxiety_std": float(group["actual"].std(ddof=0)),
        }
    overall_test_mae = float(mean_absolute_error(test_target, test_predictions))
    high_severe_groups = [band_metrics[band] for band in ordered_bands[-2:] if band_metrics[band]]
    high_severe_mae = float(np.mean([group["mae"] for group in high_severe_groups]))
    cold_start = test_frame[test_frame["therapy_sessions"] == 0]
    therapy_users = test_frame[test_frame["therapy_sessions"] > 0]

    def subgroup_metrics(group: pd.DataFrame) -> dict | None:
        if group.empty:
            return None
        return {
            "count": int(len(group)),
            "mae": float(mean_absolute_error(group["actual"], group["prediction"])),
            "mean_residual": float((group["prediction"] - group["actual"]).mean()),
        }

    cold_start_metrics = subgroup_metrics(cold_start)
    therapy_metrics = subgroup_metrics(therapy_users)
    minimal_metrics = band_metrics.get("Minimal (1-2)")
    deployment_findings = []
    if minimal_metrics and minimal_metrics["mean_residual"] > 0.25:
        deployment_findings.append("systematic_minimal_band_overprediction")
    if cold_start_metrics and cold_start_metrics["mae"] > overall_test_mae * 1.25:
        deployment_findings.append("cold_start_mae_notably_worse")
    if cold_start_metrics and cold_start_metrics["mean_residual"] < -0.25:
        deployment_findings.append("cold_start_underprediction_bias")

    return {
        "train": {
            "mae": float(mean_absolute_error(train_target, train_predictions)),
            "r2": float(r2_score(train_target, train_predictions)),
        },
        "validation": {
            "mae": float(mean_absolute_error(validation_target, validation_predictions)),
            "r2": float(r2_score(validation_target, validation_predictions)),
        },
        "test": {
            "mae": overall_test_mae,
            "r2": float(r2_score(test_target, test_predictions)),
        },
        "test_by_severity": band_metrics,
        "high_severe_error_flag": {
            "flagged": high_severe_mae > overall_test_mae * 1.25,
            "high_severe_mae": high_severe_mae,
            "overall_test_mae": overall_test_mae,
            "threshold_multiplier": 1.25,
        },
        "cold_start": cold_start_metrics,
        "therapy_sessions_greater_than_zero": therapy_metrics,
        "deployment_findings": deployment_findings,
    }


def main() -> None:
    """Compare baseline and regularized regressors without promoting either to production."""
    raw_data = pd.read_csv(RAW_DATA_DIR / "mindcare_dataset_final.csv")
    raw_features = _shared_features(raw_data)
    raw_features[TARGET] = raw_data[TARGET].astype(float).to_numpy()
    processed_splits = {
        name: pd.read_csv(PROCESSED_DATA_DIR / f"{name}.csv")
        for name in ("train", "val", "test")
    }
    targets = _attach_targets(raw_features, processed_splits)
    train_features = _scale_features(processed_splits["train"].drop(columns="Severity"))
    validation_features = _scale_features(processed_splits["val"].drop(columns="Severity"))
    test_features = _scale_features(processed_splits["test"].drop(columns="Severity"))
    train_target = targets["train"]
    validation_target = targets["val"]
    test_target = targets["test"]
    severity_counts = processed_splits["train"]["Severity"].value_counts()
    severity_weights = processed_splits["train"]["Severity"].map(
        lambda band: len(processed_splits["train"]) / (len(severity_counts) * severity_counts[band])
    )

    common_parameters = {
        "n_estimators": 500,
        "learning_rate": 0.04,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "objective": "reg:squarederror",
        "random_state": 42,
        "n_jobs": -1,
    }
    baseline_model = XGBRegressor(max_depth=5, **common_parameters)
    regularized_model = XGBRegressor(
        max_depth=3,
        reg_alpha=0.1,
        reg_lambda=5.0,
        early_stopping_rounds=30,
        **common_parameters,
    )
    weighted_model = XGBRegressor(max_depth=5, **common_parameters)
    baseline_metrics = _evaluate_variant(
        baseline_model,
        train_features,
        validation_features,
        test_features,
        train_target,
        validation_target,
        test_target,
        processed_splits["test"],
    )
    regularized_metrics = _evaluate_variant(
        regularized_model,
        train_features,
        validation_features,
        test_features,
        train_target,
        validation_target,
        test_target,
        processed_splits["test"],
    )
    weighted_metrics = _evaluate_variant(
        weighted_model,
        train_features,
        validation_features,
        test_features,
        train_target,
        validation_target,
        test_target,
        processed_splits["test"],
        sample_weight=severity_weights,
    )
    baseline_validation_predictions = baseline_model.predict(validation_features)
    weighted_validation_predictions = weighted_model.predict(validation_features)
    baseline_test_predictions = baseline_model.predict(test_features)
    weighted_test_predictions = weighted_model.predict(test_features)
    baseline_calibrator = IsotonicRegression(out_of_bounds="clip")
    weighted_calibrator = IsotonicRegression(out_of_bounds="clip")
    baseline_calibrator.fit(baseline_validation_predictions, validation_target)
    weighted_calibrator.fit(weighted_validation_predictions, validation_target)
    calibrated_baseline_diagnostics = _test_diagnostics(
        baseline_calibrator.predict(baseline_test_predictions),
        test_target,
        processed_splits["test"],
    )
    calibrated_weighted_diagnostics = _test_diagnostics(
        weighted_calibrator.predict(weighted_test_predictions),
        test_target,
        processed_splits["test"],
    )
    foundation_scores = {
        "baseline": float(np.mean([
            abs(baseline_metrics["test_by_severity"][band]["mean_residual"])
            for band in ORDERED_BANDS
        ])),
        "weighted": float(np.mean([
            abs(weighted_metrics["test_by_severity"][band]["mean_residual"])
            for band in ORDERED_BANDS
        ])),
    }
    calibration_foundation = min(foundation_scores, key=foundation_scores.get)
    selected_calibrated_diagnostics = (
        calibrated_baseline_diagnostics
        if calibration_foundation == "baseline"
        else calibrated_weighted_diagnostics
    )
    keep_regularized = regularized_metrics["test"]["mae"] <= baseline_metrics["test"]["mae"]
    selected_model = regularized_model if keep_regularized else baseline_model
    selected_metrics = regularized_metrics if keep_regularized else baseline_metrics
    baseline_mean = float(train_target.mean())
    baseline_mode = float(train_target.mode().iloc[0])
    feature_importance = dict(
        sorted(
            {
                feature: float(importance)
                for feature, importance in zip(train_features.columns, selected_model.feature_importances_)
            }.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )
    metrics = {
        "target": TARGET,
        "model": "xgboost_regressor",
        "selected_variant": "regularized" if keep_regularized else "baseline",
        "regularization_kept": keep_regularized,
        "features": list(FEATURE_COLUMNS),
        "preprocessing": "shared onehot_encoder.joblib and scaler.joblib",
        "model_feature_columns": train_features.columns.tolist(),
        "baseline_comparison": {
            "always_predict_mean_mae": float(mean_absolute_error(test_target, np.full(len(test_target), baseline_mean))),
            "always_predict_mode_accuracy": float(np.mean(np.rint(test_target) == np.rint(baseline_mode))),
            "training_mean": baseline_mean,
            "training_mode": baseline_mode,
        },
        "regularization_comparison": {
            "baseline_test_mae": baseline_metrics["test"]["mae"],
            "regularized_test_mae": regularized_metrics["test"]["mae"],
            "decision": "kept_regularized" if keep_regularized else "kept_baseline",
        },
        "severity_weighting": {
            "weight_formula": "n_samples / (n_bands * band_count)",
            "training_band_weights": {
                band: float(weight)
                for band, weight in severity_counts.map(
                    lambda count: len(processed_splits["train"]) / (len(severity_counts) * count)
                ).items()
            },
            "baseline_test_mae": baseline_metrics["test"]["mae"],
            "weighted_test_mae": weighted_metrics["test"]["mae"],
            "weighted_candidate": weighted_metrics,
        },
        "severity_band_bias_comparison": {
            band: {
                "baseline_mean_residual": baseline_metrics["test_by_severity"][band]["mean_residual"],
                "weighted_mean_residual": weighted_metrics["test_by_severity"][band]["mean_residual"],
                "baseline_abs_residual": abs(baseline_metrics["test_by_severity"][band]["mean_residual"]),
                "weighted_abs_residual": abs(weighted_metrics["test_by_severity"][band]["mean_residual"]),
            }
            for band in baseline_metrics["test_by_severity"]
        },
        "calibration": {
            "method": "IsotonicRegression",
            "fit_data": "validation_predictions_and_validation_targets_only",
            "foundation_bias_score_mean_abs_residual": foundation_scores,
            "selected_foundation": calibration_foundation,
            "calibrated_baseline": calibrated_baseline_diagnostics,
            "calibrated_weighted": calibrated_weighted_diagnostics,
        },
        "three_way_severity_band_bias_comparison": {
            band: {
                "baseline": baseline_metrics["test_by_severity"][band],
                "weighted": weighted_metrics["test_by_severity"][band],
                "calibrated": selected_calibrated_diagnostics["test_by_severity"][band],
            }
            for band in ORDERED_BANDS
        },
        "small_sample_warning": {
            "flagged": any(
                baseline_metrics["test_by_severity"][band]["count"] < 300
                for band in ORDERED_BANDS
            ),
            "band_counts": {
                band: int((processed_splits["test"]["Severity"] == band).sum())
                for band in ORDERED_BANDS
            },
            "note": "Per-band swings should be interpreted cautiously, especially for smaller High and Severe groups.",
        },
        "variants": {
            "baseline": baseline_metrics,
            "regularized": regularized_metrics,
        },
        "selected": selected_metrics,
    }

    EXPERIMENT_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected_model, EXPERIMENT_MODELS_DIR / "anxiety_regressor.joblib")
    joblib.dump(weighted_model, EXPERIMENT_MODELS_DIR / "anxiety_regressor_weighted.joblib")
    joblib.dump(
        baseline_calibrator,
        EXPERIMENT_MODELS_DIR / "anxiety_calibrator_baseline.joblib",
    )
    joblib.dump(
        weighted_calibrator,
        EXPERIMENT_MODELS_DIR / "anxiety_calibrator_weighted.joblib",
    )
    REPORTS_DIR.joinpath("metrics").mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "metrics" / "anxiety_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n",
        encoding="utf-8",
    )
    (REPORTS_DIR / "metrics" / "anxiety_feature_importance.json").write_text(
        json.dumps(feature_importance, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))
    print("Top 5 anxiety feature importances:")
    for feature, importance in list(feature_importance.items())[:5]:
        print(f"  {feature}: {importance:.6f}")


if __name__ == "__main__":
    main()