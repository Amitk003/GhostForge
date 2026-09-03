"""Argus biargus parser for CTU-13.

CTU-13 provides detailed bidirectional flow labels with Argus fields.
This parser normalizes them to the unified schema for training.

Fields in CTU-13 biargus: StartTime, Dur, Proto, SrcAddr, Sport, Dir, DstAddr, Dport,
State, sTos, dTos, TotPkts, TotBytes, SrcBytes, Label.
"""

from pathlib import Path

import polars as pl

from ghostforge.ingest.utils import normalize_columns


ARGUS_LABEL_COL = "label"


def load_argus_csv(path: Path) -> pl.DataFrame:
    """Load Argus biargus CSV with polars.

    Handles both comma and tab separated files.
    """
    if not path.exists():
        raise FileNotFoundError(f"Argus file not found: {path}")

    # Try comma first, fallback to tab
    try:
        df = pl.read_csv(path, infer_schema_length=10000, ignore_errors=True)
    except Exception:
        df = pl.read_csv(path, separator="\t", infer_schema_length=10000, ignore_errors=True)

    df = normalize_columns(df)
    return df


def clean_argus(df: pl.DataFrame) -> pl.DataFrame:
    """Clean Argus dataframe and map labels to benign or attack.

    Labels in CTU-13 look like: flow=From-Botnet-V50-4-TCP-WEB-EstablishedPick-up etc.
    We map Background -> benign, Botnet -> attack, Normal -> benign for training.
    """
    if df.is_empty():
        return df

    # Normalize label col
    label_col = None
    for c in df.columns:
        if "label" in c.lower():
            label_col = c
            break

    if label_col:
        df = df.with_columns(
            pl.col(label_col)
            .str.to_lowercase()
            .str.contains("botnet")
            .alias("is_attack")
        )
        df = df.with_columns(
            pl.when(pl.col("is_attack"))
            .then(pl.lit("attack"))
            .otherwise(pl.lit("benign"))
            .alias("unified_label")
        )

    # Coerce numeric
    for col in ["dur", "totpkts", "totbytes", "srcbytes"]:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.Float64, strict=False).fill_null(0))

    # Proto mapping
    if "proto" in df.columns:
        proto_map = {"tcp": 6, "udp": 17, "icmp": 1}
        df = df.with_columns(pl.col("proto").str.to_lowercase().replace(proto_map, default=0).alias("proto_num"))

    return df


def load_argus(path: Path) -> pl.DataFrame:
    """Load and clean Argus file in one call."""
    df = load_argus_csv(path)
    return clean_argus(df)
