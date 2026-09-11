# MindCare AI

MindCare AI is an ML project scaffold for clinician-facing mental-health decision support. The system is organized so that exploratory work stays in notebooks and reusable production logic stays in `src/`.

## Repository layout

- `data/raw/`: original, read-only source data
- `data/interim/`: partially cleaned datasets
- `data/processed/`: train, validation, and test-ready datasets
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
