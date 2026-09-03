"""Feedback store for contestable learning.

Analyst marks prediction as correct or wrong, we store for later fine tune.
Simple parquet or csv append, offline.
"""

from dataclasses import asdict, dataclass
from pathlib import Path

import polars as pl


@dataclass
class Feedback:
    """One feedback item."""

    window_id: int
    label: str  # correct, wrong, missing
    risk: float | None = None
    stage: str | None = None
    note: str = ""


def save_feedback(feedback: Feedback, path: Path = Path("feedback.parquet")) -> None:
    """Append feedback to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df_new = pl.DataFrame([asdict(feedback)])

    if path.exists():
        try:
            df_old = pl.read_parquet(path)
            df = pl.concat([df_old, df_new])
        except Exception:
            df = df_new
    else:
        df = df_new

    # Try parquet, fallback csv
    try:
        df.write_parquet(path)
    except Exception:
        df.write_csv(path.with_suffix(".csv"))


def load_feedback(path: Path = Path("feedback.parquet")) -> list[Feedback]:
    """Load all feedback."""
    if not path.exists():
        # Try csv fallback
        csv_path = path.with_suffix(".csv")
        if not csv_path.exists():
            return []
        path = csv_path

    try:
        if path.suffix == ".parquet":
            df = pl.read_parquet(path)
        else:
            df = pl.read_csv(path)
    except Exception:
        return []

    out: list[Feedback] = []
    for row in df.to_dicts():
        out.append(
            Feedback(
                window_id=int(row.get("window_id", 0)),
                label=str(row.get("label", "")),
                risk=row.get("risk"),
                stage=row.get("stage"),
                note=str(row.get("note", "")),
            )
        )
    return out


def needs_retrain(path: Path = Path("feedback.parquet"), threshold: int = 10) -> bool:
    """Check if enough contested cases to trigger retrain."""
    return len(load_feedback(path)) >= threshold
