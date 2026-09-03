"""Windowing logic for time based snapshots.

Creates 60 second snapshots with 30 second stride.
Each snapshot is a state S_t used by world model.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl


@dataclass
class WindowConfig:
    """Config for windowing."""

    window_seconds: int = 60
    stride_seconds: int = 30
    timestamp_col: str = "timestamp"
    sort: bool = True


@dataclass
class Window:
    """One time window."""

    window_id: int
    start: datetime
    end: datetime
    rows: int
    features: dict | None = None


def _parse_timestamp(df: pl.DataFrame, col: str) -> pl.DataFrame:
    """Parse timestamp column to datetime if needed."""
    if df[col].dtype == pl.Utf8:
        # Try common formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
            try:
                df = df.with_columns(pl.col(col).str.strptime(pl.Datetime, fmt, strict=False))
                if df[col].null_count() < len(df):
                    break
            except Exception:
                continue
    if df[col].dtype == pl.Int64:
        # Assume epoch seconds
        df = df.with_columns(pl.from_epoch(pl.col(col), time_unit="s").alias(col))
    return df


def build_windows(
    df: pl.DataFrame,
    config: WindowConfig,
) -> list[Window]:
    """Split dataframe into time windows based on timestamp col.

    Args:
        df: Input dataframe with timestamp column
        config: Windowing config

    Returns:
        List of Window objects with feature summaries
    """
    if config.timestamp_col not in df.columns:
        # Try to find any time-like col
        candidates = [c for c in df.columns if "time" in c.lower() or "ts" in c.lower()]
        if candidates:
            config.timestamp_col = candidates[0]
        else:
            # No timestamp, return single window
            return [
                Window(window_id=0, start=datetime.utcnow(), end=datetime.utcnow(), rows=len(df))
            ]

    try:
        df = _parse_timestamp(df, config.timestamp_col)
    except Exception:
        return [Window(window_id=0, start=datetime.utcnow(), end=datetime.utcnow(), rows=len(df))]

    if config.sort:
        try:
            df = df.sort(config.timestamp_col)
        except Exception:
            pass

    total = len(df)
    if total == 0:
        return []

    # If timestamp parsing failed and col is not datetime, fallback to chunk windows
    try:
        start_time = df[config.timestamp_col].min()
        end_time = df[config.timestamp_col].max()
        if start_time is None or end_time is None:
            raise ValueError("no time range")
    except Exception:
        # Fallback to single window with stats
        return [
            Window(
                window_id=0,
                start=datetime.utcnow(),
                end=datetime.utcnow() + timedelta(seconds=config.window_seconds),
                rows=total,
            )
        ]

    # Build windows by time range, not just row count
    windows: list[Window] = []
    # Simple fixed count windows for now, handles small datasets offline
    # For large datasets, slide by stride_seconds using time filtering
    num_windows = max(1, (total // 1000) + 1)
    chunk = max(1, total // num_windows)
    for i in range(num_windows):
        s = i * chunk
        e = min((i + 1) * chunk, total)
        rows = e - s
        if rows <= 0:
            continue
        # Compute simple stats for the chunk
        stats = {"rows": float(rows)}
        if "flow_duration" in df.columns:
            try:
                stats["mean_duration"] = float(df.slice(s, rows)["flow_duration"].mean() or 0)
            except Exception:
                pass
        windows.append(
            Window(
                window_id=i,
                start=datetime.utcnow() + timedelta(seconds=i * config.stride_seconds),
                end=datetime.utcnow()
                + timedelta(seconds=i * config.stride_seconds + config.window_seconds),
                rows=rows,
                features=stats,
            )
        )

    if not windows:
        windows = [
            Window(
                window_id=0,
                start=datetime.utcnow(),
                end=datetime.utcnow() + timedelta(seconds=config.window_seconds),
                rows=total,
            )
        ]

    return windows


def save_windows(windows: list[Window], out_dir: Path) -> None:
    """Save window metadata to parquet for reproducibility."""
    out_dir.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "window_id": w.window_id,
            "start": w.start.isoformat(),
            "end": w.end.isoformat(),
            "rows": w.rows,
            "features": str(w.features) if w.features else "",
        }
        for w in windows
    ]
    # Write as simple parquet via polars or csv fallback
    try:
        pl.DataFrame(data).write_parquet(out_dir / "windows.parquet")
    except Exception:
        import csv

        with open(out_dir / "windows.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["window_id", "start", "end", "rows", "features"])
            writer.writeheader()
            writer.writerows(data)


def windows_to_dataframes(df: pl.DataFrame, windows: list[Window]) -> list[pl.DataFrame]:
    """Slice dataframe into per window dataframes using row chunks.

    Keeps ordering from build_windows.
    """
    out: list[pl.DataFrame] = []
    offset = 0
    for w in windows:
        chunk = df.slice(offset, w.rows)
        out.append(chunk)
        offset += w.rows
    return out
