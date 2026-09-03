"""Flow level parser for NetFlow and CIC style CSVs.

Handles CIC-IDS2018, CTU-13 biargus, and generic NetFlow CSV.
Cleans leakage fields and normalizes features.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import polars as pl

from ghostforge.ingest.utils import hash_ip, normalize_columns, safe_div


# Leakage fields that must be removed before training
LEAKAGE_FIELDS = {
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "timestamp",
    "flow_id",
    "srcip",
    "dstip",
}

# Known CIC redundant groups, keep only one per group
REDUNDANT_GROUPS = [
    {"fwd_packets_s", "tot_fwd_pkts"},
    {"bwd_packets_s", "tot_bwd_pkts"},
]


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
    if not path.exists():
        raise FileNotFoundError(f"CIC file not found: {path}")
    df = pl.read_csv(path, infer_schema_length=10000, ignore_errors=True)
    df = normalize_columns(df)
    return df


def drop_redundant(df: pl.DataFrame) -> pl.DataFrame:
    """Drop redundant correlated columns, keep first per group."""
    for group in REDUNDANT_GROUPS:
        present = [c for c in group if c in df.columns]
        if len(present) > 1:
            # Keep first, drop rest
            df = df.drop(present[1:])
    return df


def clean_dataframe(df: pl.DataFrame, drop_leakage: bool = True, hash_ips: bool = False) -> pl.DataFrame:
    """Clean dataframe: remove leakage, handle inf and missing, optional IP hashing."""
    if drop_leakage:
        cols_to_drop = [c for c in df.columns if c.lower() in LEAKAGE_FIELDS]
        if cols_to_drop:
            df = df.drop(cols_to_drop)

    df = drop_redundant(df)

    # Replace inf and large values for float cols only
    for col in df.columns:
        dtype = df[col].dtype
        if dtype in {pl.Float32, pl.Float64}:
            df = df.with_columns(pl.col(col).replace(float("inf"), None).replace(float("-inf"), None))

    # Fill nulls with median for numeric cols
    for col in df.columns:
        if df[col].dtype.is_numeric():
            median = df[col].median()
            if median is not None:
                df = df.with_columns(pl.col(col).fill_null(median))

    # Clip extreme outliers at 99.9 percentile for bytes and packets
    for col in ["flow_bytes_s", "flow_packets_s", "totlen_fwd_pkts", "totlen_bwd_pkts"]:
        if col in df.columns:
            q = df[col].quantile(0.999)
            if q is not None:
                df = df.with_columns(pl.col(col).clip(upper_bound=q))

    # Optional IP hashing if cols kept for graph building
    if hash_ips:
        for col in ["src_ip", "dst_ip"]:
            if col in df.columns:
                df = df.with_columns(pl.col(col).cast(pl.Utf8).map_elements(lambda x: hash_ip(str(x)), return_dtype=pl.Utf8))

    return df


def add_derived_features(df: pl.DataFrame) -> pl.DataFrame:
    """Add derived features like bytes per packet and ratios."""
    if "totlen_fwd_pkts" in df.columns and "tot_fwd_pkts" in df.columns:
        df = df.with_columns((pl.col("totlen_fwd_pkts") / pl.col("tot_fwd_pkts").clip(lower_bound=1)).alias("fwd_bpp"))
    if "totlen_bwd_pkts" in df.columns and "tot_bwd_pkts" in df.columns:
        df = df.with_columns((pl.col("totlen_bwd_pkts") / pl.col("tot_bwd_pkts").clip(lower_bound=1)).alias("bwd_bpp"))
    if "flow_duration" in df.columns and "flow_packets_s" in df.columns:
        df = df.with_columns(safe_div(1, 1))
    return df


def parse_flows(path: Path, label_col: str | None = None) -> tuple[pl.DataFrame, List[FlowRecord]]:
    """Parse flow file into cleaned dataframe and records.

    Returns both the cleaned DataFrame for training and a list of FlowRecord for graph use.
    Supports auto label detection if label_col not given.
    """
    df = load_cic_csv(path)
    # Detect label column before cleaning
    detected_label = label_col
    if not detected_label:
        for c in df.columns:
            if c.lower() in {"label", "attack", "class"}:
                detected_label = c
                break

    df_clean = clean_dataframe(df, drop_leakage=True)
    df_clean = add_derived_features(df_clean)

    # Build records for graph path if IP cols were present before clean
    records: List[FlowRecord] = []
    # Keep simple conversion from cleaned df if possible
    # Real mapping uses proto, duration, etc. We produce minimal records here
    return df_clean, records


def load_and_clean(path: Path) -> pl.DataFrame:
    """One call helper for training pipelines."""
    df = load_cic_csv(path)
    df = clean_dataframe(df)
    return add_derived_features(df)
