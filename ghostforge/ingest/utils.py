"""Shared helpers for ingestion.

Small, fast, and tested utils used by flow and pcap parsers.
"""

import hashlib
import ipaddress
import re
from typing import Any

import polars as pl


def hash_ip(ip: str, salt: str = "ghostforge") -> str:
    """Hash IP to avoid storing raw values and to reduce leakage.

    Returns first 8 chars of sha256, stable per IP.
    """
    h = hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()
    return h[:8]


def normalize_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Lower case and snake case all column names."""
    mapping = {}
    for c in df.columns:
        new_c = c.strip().lower()
        new_c = re.sub(r"[^a-z0-9]+", "_", new_c)
        new_c = re.sub(r"_+", "_", new_c).strip("_")
        mapping[c] = new_c
    return df.rename(mapping)


def is_private_ip(ip: str) -> bool:
    """Check if IP is private range."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    """Division that never crashes on zero."""
    if b == 0:
        return default
    return a / b


def col_exists(df: pl.DataFrame, name: str) -> bool:
    """Case insensitive column check."""
    lower_cols = {c.lower() for c in df.columns}
    return name.lower() in lower_cols


def get_col(df: pl.DataFrame, name: str, default: Any = None) -> pl.Series | None:
    """Get column case insensitive, or None."""
    for c in df.columns:
        if c.lower() == name.lower():
            return df[c]
    return None
