"""Read source datasets without modifying them."""

from pathlib import Path

import pandas as pd


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file into a dataframe."""
    return pd.read_csv(path)
