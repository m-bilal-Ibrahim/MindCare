"""Schema and sanity checks used before training."""

import pandas as pd


def require_columns(dataframe: pd.DataFrame, columns: list[str]) -> None:
    """Raise a clear error when required columns are absent."""
    missing = sorted(set(columns) - set(dataframe.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
