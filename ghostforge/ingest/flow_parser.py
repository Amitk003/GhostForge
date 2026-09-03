"""Flow level parser for NetFlow and CIC style CSVs.

Handles CIC-IDS2018, CTU-13 biargus, and generic NetFlow CSV.
Cleans leakage fields and normalizes features.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import polars as pl


# Leakage fields that must be removed before training
LEAKAGE_FIELDS = {
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "timestamp",
    "flow_id",
}


@dataclass
class FlowRecord:
    """Single flow record after cleaning."""

    src_role: str
    dst_role: str
    protocol: int
    duration: float
    bytes_total: int
    packets_total: int
    flags: int
    iat_mean: float
    iat_var: float
    iat_max: float
    bytes_per_packet: float


def infer_role(port: int) -> str:
    """Infer host role from port usage. Simple heuristic."""
    if port in {22, 3389, 5985, 445}:
        return "server"
    if port in {502, 102, 20000}:
        return "ot"
    if port in {80, 443, 53}:
        return "infra"
    return "workstation"


def load_cic_csv(path: Path) -> pl.DataFrame:
    """Load CIC style CSV with polars for speed."""
    df = pl.read_csv(path, infer_schema_length=10000)
    # Normalize column names to lower snake
    df = df.rename({c: c.strip().lower().replace(" ", "_") for c in df.columns})
    return df


def clean_dataframe(df: pl.DataFrame, drop_leakage: bool = True) -> pl.DataFrame:
    """Clean dataframe: remove leakage, handle inf and missing."""
    if drop_leakage:
        cols_to_drop = [c for c in df.columns if c.lower() in LEAKAGE_FIELDS]
        if cols_to_drop:
            df = df.drop(cols_to_drop)

    # Replace inf with null then fill
    df = df.with_columns([pl.col(c).replace(float("inf"), None) for c in df.columns if df[c].dtype.is_numeric()])

    # Fill nulls with median for numeric cols
    for col in df.columns:
        if df[col].dtype.is_numeric():
            median = df[col].median()
            if median is not None:
                df = df.with_columns(pl.col(col).fill_null(median))

    return df


def parse_flows(path: Path) -> List[FlowRecord]:
    """Parse flow file into list of records. Supports csv."""
    df = load_cic_csv(path)
    df = clean_dataframe(df)
    # Minimal conversion to dataclass for now
    records: List[FlowRecord] = []
    # Placeholder: real mapping depends on dataset columns
    # Keep function signature stable for future work
    return records
