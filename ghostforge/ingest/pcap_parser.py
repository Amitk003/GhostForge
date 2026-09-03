"""Packet level parser for PCAP files.

Extracts TTL, window size, flags, payload size, retransmission hints.
Uses Scapy when available, falls back to dpkt.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class PacketFeatures:
    """Features for one packet."""

    timestamp: float
    src: str
    dst: str
    src_port: int
    dst_port: int
    ttl: int
    window_size: int
    flags: int
    payload_len: int
    is_retransmit: bool


def parse_pcap(path: Path) -> List[PacketFeatures]:
    """Parse pcap file into packet features.

    This is a scaffold. Real implementation will use Scapy or dpkt.
    Keeps offline and fast, no cloud calls.
    """
    if not path.exists():
        raise FileNotFoundError(f"PCAP not found: {path}")

    # Scaffold return empty for now, tests will mock
    return []


def extract_ttl_variance(packets: List[PacketFeatures]) -> float:
    """Compute TTL variance across packets in a window."""
    if not packets:
        return 0.0
    import statistics

    ttls = [p.ttl for p in packets]
    if len(ttls) < 2:
        return 0.0
    return statistics.variance(ttls)


def extract_scan_signature(packets: List[PacketFeatures]) -> dict:
    """Detect sequential or random port scan patterns."""
    if not packets:
        return {"scan_score": 0.0, "ports_touched": 0}

    ports = [p.dst_port for p in packets]
    unique_ports = len(set(ports))
    total = len(ports)

    # Simple score: high unique ratio suggests scan
    score = unique_ports / max(total, 1)
    return {"scan_score": round(score, 3), "ports_touched": unique_ports}
