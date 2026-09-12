# MindCare AI

MindCare AI is an ML project scaffold for clinician-facing mental-health decision support. The system is organized so that exploratory work stays in notebooks and reusable production logic stays in `src/`.

## Repository layout

- `data/raw/`: original, read-only source data
- `data/interim/`: partially cleaned datasets
- `data/processed/`: combined train, validation, test, and scaled datasets only
- `data/artifacts/`: fitted encoders, scalers, and class-weight metadata
- `data/reference/`: business-logic lookup data, separate from training data
- `data/external/`: reference data and lookup tables
- `notebooks/`: numbered exploratory analysis and experiments
- `src/`: reusable data, feature, model, feedback, and API code
- `models/`: experiment artifacts and the approved production model
- `reports/`: generated figures and metrics
- `tests/`: automated checks for the production code

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the API locally with:

```powershell
uvicorn src.api.app:app --reload
```

The API is decision support for qualified professionals. It does not provide a diagnosis or replace clinical judgment.

Prepare or refresh the dataset layout with:

```powershell
python -m src.data.prepare_dataset
```

Train baseline models and select the production model with:

```powershell
python -m scripts.train_models
```

The production severity model uses wearable-compatible inputs: sleep hours,
physical activity, heart rate, breathing rate, sweating level, and dizziness.
It does not require oxygen level or use `Anxiety Level (1-10)` as an input.

Train the separate anxiety-level model with:

```powershell
python -m scripts.train_anxiety_model
```

The anxiety model is evaluated independently because anxiety level is a target,
not an input to severity prediction. Its current held-out results are recorded
in `reports/metrics/anxiety_metrics.json`.
