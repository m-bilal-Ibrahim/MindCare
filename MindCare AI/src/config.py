"""Central project paths and default settings."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DATA_DIR = DATA_DIR / "artifacts"
REFERENCE_DATA_DIR = DATA_DIR / "reference"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
MODELS_DIR = PROJECT_ROOT / "models"
EXPERIMENT_MODELS_DIR = MODELS_DIR / "experiments"
PRODUCTION_MODELS_DIR = MODELS_DIR / "production"
REPORTS_DIR = PROJECT_ROOT / "reports"

RANDOM_STATE = 42
TARGET_COLUMN = "Severity"
PREDICTION_EXCLUDED_COLUMNS = {TARGET_COLUMN, "Anxiety Level (1-10)"}
WEARABLE_FEATURE_COLUMNS = (
	"Sleep Hours",
	"Physical Activity (hrs/week)",
	"Heart Rate (bpm)",
	"Breathing Rate (breaths/min)",
	"Sweating Level (1-5)",
	"Dizziness",
)
