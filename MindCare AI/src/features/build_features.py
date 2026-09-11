"""Build model-ready feature frames."""

import pandas as pd


def build_features(dataframe: pd.DataFrame, excluded_columns: list[str] | None = None) -> pd.DataFrame:
    """Select feature columns while preserving the input dataframe."""
    excluded = set(excluded_columns or [])
    return dataframe.drop(columns=[column for column in excluded if column in dataframe]).copy()
