# MindCare AI Context

## Project boundaries

- `notebooks/` is for exploration only and must not be imported by production code.
- `src/` contains reusable data, feature, model, feedback, and API code.
- `data/raw/` is read-only source data. Generated datasets belong in `data/interim/` or `data/processed/`.
- `models/production/` contains only the currently approved model artifact.
- Feedback from psychologist review is stored as structured records for future retraining.

## Safety

Model output is decision support for qualified professionals. It is not a diagnosis or a replacement for clinical judgment.
