"""Windowing logic for time based snapshots.

Creates 60 second snapshots with 30 second stride.
Each snapshot is a state S_t used by world model.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import polars as pl


@dataclass
class WindowConfig:
    """Config for windowing."""

    window_seconds: int = 60
    stride_seconds: int = 30
    timestamp_col: str = "timestamp"


@dataclass
class Window:
    """One time window."""

    window_id: int
    start: datetime
    end: datetime
    rows: int


def build_windows(
    df: pl.DataFrame,
    config: WindowConfig,
) -> List[Window]:
    """Split dataframe into time windows based on timestamp col.

    Args:
        df: Input dataframe with timestamp column
        config: Windowing config

    Returns:
        List of Window objects
    """
    if config.timestamp_col not in df.columns:
        # No timestamp, return single window
        return [Window(window_id=0, start=datetime.utcnow(), end=datetime.utcnow(), rows=len(df))]

    # Ensure timestamp is datetime
    # Scaffold logic, real will parse and sort
    total = len(df)
    if total == 0:
        return []

    # Placeholder: one window per data chunk
    return [Window(window_id=0, start=datetime.utcnow(), end=datetime.utcnow() + timedelta(seconds=config.window_seconds), rows=total)]


def save_windows(windows: List[Window], out_dir: Path) -> None:
    """Save window metadata to parquet for reproducibility."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # Scaffold, real will write parquet
    pass
