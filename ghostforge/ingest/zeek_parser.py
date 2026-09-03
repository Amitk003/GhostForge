"""Zeek conn.log parser.

Reads Zeek conn.log (tab separated with header) and converts to
flow records with same schema as CIC flows. Runs offline.

Zeek logs are the production path for live tailing.
"""

import gzip
from pathlib import Path
from typing import List

import polars as pl

from ghostforge.ingest.utils import normalize_columns


ZEEK_FIELDS = [
    "ts",
    "uid",
    "id.orig_h",
    "id.orig_p",
    "id.resp_h",
    "id.resp_p",
    "proto",
    "service",
    "duration",
    "orig_bytes",
    "resp_bytes",
    "conn_state",
    "missed_bytes",
    "history",
    "orig_pkts",
    "resp_pkts",
    "orig_ip_bytes",
    "resp_ip_bytes",
    "tunnel_parents",
]


def read_zeek_log(path: Path) -> pl.DataFrame:
    """Read Zeek conn.log, supports plain and gzipped.

    Skips comment lines starting with #.
    Returns polars DataFrame with normalized columns.
    """
    if not path.exists():
        raise FileNotFoundError(f"Zeek log not found: {path}")

    # Read with polars, handle gz
    open_func = gzip.open if path.suffix == ".gz" else open

    rows: List[dict] = []
    with open_func(path, "rt", encoding="utf-8", errors="ignore") as f:
        header: List[str] | None = None
        for line in f:
            if line.startswith("#fields"):
                header = line.strip().split("\t")[1:]
                continue
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            if header is None:
                continue
            parts = line.strip().split("\t")
            # Pad if short
            if len(parts) < len(header):
                parts += ["-"] * (len(header) - len(parts))
            row = dict(zip(header, parts))
            rows.append(row)

    if not rows:
        return pl.DataFrame()

    df = pl.DataFrame(rows)
    df = normalize_columns(df)
    return df


def zeek_to_flow_features(df: pl.DataFrame) -> pl.DataFrame:
    """Map Zeek fields to unified flow features.

    Produces columns: duration, proto, orig_bytes, resp_bytes, total_bytes,
    orig_pkts, resp_pkts, bytes_per_packet, duration ratio.
    """
    if df.is_empty():
        return df

    # Coerce numeric cols
    for col in ["duration", "orig_bytes", "resp_bytes", "orig_pkts", "resp_pkts", "orig_ip_bytes", "resp_ip_bytes"]:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.Utf8).str.replace("-", "0").cast(pl.Float64, strict=False).fill_null(0))

    # Proto to int
    proto_map = {"tcp": 6, "udp": 17, "icmp": 1}
    if "proto" in df.columns:
        df = df.with_columns(pl.col("proto").str.to_lowercase().replace_strict(proto_map, default=0).alias("proto_num"))

    # Derived
    if "orig_bytes" in df.columns and "resp_bytes" in df.columns:
        df = df.with_columns((pl.col("orig_bytes") + pl.col("resp_bytes")).alias("total_bytes"))
    if "orig_pkts" in df.columns and "resp_pkts" in df.columns:
        df = df.with_columns((pl.col("orig_pkts") + pl.col("resp_pkts")).alias("total_pkts"))

    return df


def load_zeek(path: Path) -> pl.DataFrame:
    """One call to load and convert Zeek log."""
    df = read_zeek_log(path)
    return zeek_to_flow_features(df)
