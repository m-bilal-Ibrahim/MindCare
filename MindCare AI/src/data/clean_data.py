"""Basic, reusable dataframe cleaning operations."""

import pandas as pd


def drop_empty_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy without rows that contain no values."""
    return dataframe.dropna(how="all").reset_index(drop=True)
