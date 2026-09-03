"""Extended tests for new ingest parsers."""

import tempfile
from pathlib import Path

import polars as pl

from ghostforge.ingest.argus_parser import clean_argus
from ghostforge.ingest.graph_builder import build_graph_from_dataframe
from ghostforge.ingest.utils import hash_ip, normalize_columns
from ghostforge.ingest.windowing import (
    WindowConfig,
    build_windows,
    save_windows,
    windows_to_dataframes,
)
from ghostforge.ingest.zeek_parser import zeek_to_flow_features


def test_normalize_columns() -> None:
    df = pl.DataFrame({"Src IP": [1], "Dst-Port": [2]})
    out = normalize_columns(df)
    assert "src_ip" in out.columns
    assert "dst_port" in out.columns


def test_hash_ip() -> None:
    h1 = hash_ip("192.168.1.1")
    h2 = hash_ip("192.168.1.1")
    assert h1 == h2
    assert len(h1) == 8


def test_zeek_features() -> None:
    df = pl.DataFrame(
        {
            "ts": ["0", "1"],
            "proto": ["tcp", "udp"],
            "orig_bytes": ["100", "200"],
            "resp_bytes": ["50", "0"],
            "orig_pkts": ["2", "3"],
            "resp_pkts": ["1", "0"],
        }
    )
    out = zeek_to_flow_features(df)
    assert "total_bytes" in out.columns
    assert out["total_bytes"][0] == 150


def test_argus_clean() -> None:
    df = pl.DataFrame(
        {
            "StartTime": ["0", "1"],
            "Dur": [0.1, 0.2],
            "Proto": ["tcp", "udp"],
            "SrcAddr": ["10.0.0.1", "10.0.0.2"],
            "Label": ["flow=Background", "flow=From-Botnet-V50"],
        }
    )
    df = pl.DataFrame(
        {
            "starttime": ["0", "1"],
            "dur": [0.1, 0.2],
            "proto": ["tcp", "udp"],
            "srcaddr": ["10.0.0.1", "10.0.0.2"],
            "label": ["flow=Background", "flow=From-Botnet-V50"],
        }
    )
    out = clean_argus(df)
    assert "unified_label" in out.columns
    assert out["unified_label"][1] == "attack"


def test_build_graph_from_dataframe() -> None:
    df = pl.DataFrame(
        {
            "src": ["10.0.0.1", "10.0.0.2"],
            "dst": ["10.0.0.2", "10.0.0.3"],
            "bytes": [100, 200],
        }
    )
    snap = build_graph_from_dataframe(df)
    assert snap.num_nodes == 3
    assert snap.num_edges == 2


def test_window_helpers() -> None:
    df = pl.DataFrame({"a": [1, 2, 3, 4], "timestamp": ["2024-01-01 00:00:00"] * 4})
    windows = build_windows(df, WindowConfig(window_seconds=60, stride_seconds=30))
    assert len(windows) >= 1
    dfs = windows_to_dataframes(df, windows)
    assert len(dfs) == len(windows)

    with tempfile.TemporaryDirectory() as td:
        save_windows(windows, Path(td))
        # Should create windows.parquet or csv
        assert any(Path(td).iterdir())
