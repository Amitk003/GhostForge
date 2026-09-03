"""Tests for ingest modules."""

import polars as pl

from ghostforge.ingest.flow_parser import clean_dataframe, infer_role
from ghostforge.ingest.graph_builder import build_graph
from ghostforge.ingest.pcap_parser import extract_scan_signature, extract_ttl_variance
from ghostforge.ingest.windowing import WindowConfig, build_windows


def test_infer_role() -> None:
    assert infer_role(445) == "server"
    assert infer_role(502) == "ot"
    assert infer_role(12345) == "workstation"


def test_clean_dataframe() -> None:
    df = pl.DataFrame({"a": [1, 2, None], "src_ip": ["1.1.1.1", "2.2.2.2", "3.3.3.3"]})
    cleaned = clean_dataframe(df, drop_leakage=True)
    assert "src_ip" not in cleaned.columns


def test_build_graph() -> None:
    flows = [
        {"src": "10.0.0.1", "dst": "10.0.0.2", "bytes": 100, "packets": 2, "flags": 2},
        {"src": "10.0.0.2", "dst": "10.0.0.3", "bytes": 200, "packets": 3, "flags": 2},
    ]
    snap = build_graph(flows, window_id=0)
    assert snap.num_nodes == 3
    assert snap.num_edges == 2


def test_windowing_no_timestamp() -> None:
    df = pl.DataFrame({"a": [1, 2, 3]})
    windows = build_windows(df, WindowConfig())
    assert len(windows) == 1
    assert windows[0].rows == 3


def test_ttl_variance() -> None:
    from ghostforge.ingest.pcap_parser import PacketFeatures

    packets = [
        PacketFeatures(timestamp=0, src="a", dst="b", src_port=1, dst_port=80, ttl=64, window_size=100, flags=2, payload_len=10, is_retransmit=False),
        PacketFeatures(timestamp=1, src="a", dst="b", src_port=1, dst_port=80, ttl=64, window_size=100, flags=2, payload_len=10, is_retransmit=False),
    ]
    assert extract_ttl_variance(packets) == 0.0


def test_scan_signature() -> None:
    from ghostforge.ingest.pcap_parser import PacketFeatures

    packets = [
        PacketFeatures(timestamp=i, src="a", dst="b", src_port=1, dst_port=80 + i, ttl=64, window_size=100, flags=2, payload_len=10, is_retransmit=False)
        for i in range(5)
    ]
    sig = extract_scan_signature(packets)
    assert sig["ports_touched"] == 5
