"""Tests for explain modules."""

import torch

from ghostforge.explain.attention import attention_to_contrib, edge_attention
from ghostforge.explain.attribution import feature_attribution, top_features
from ghostforge.explain.evidence import build_evidence, evidence_to_markdown


def test_attribution() -> None:
    feats = {"flow_duration": 10, "tot_fwd_pkts": 5, "syn_flag": 1}
    baseline = {"flow_duration": 1, "tot_fwd_pkts": 1, "syn_flag": 0}
    attrs = feature_attribution(feats, baseline)
    assert len(attrs) == 3
    top = top_features(attrs, k=1)
    assert len(top) == 1
    assert top[0]["feature"] in feats


def test_attention() -> None:
    edge_attrs = torch.randn(4, 8)
    weights = edge_attention(edge_attrs)
    assert len(weights) == 4
    assert abs(sum(weights) - 1.0) < 1e-5

    flows = [
        {"src": "a", "dst": "b"},
        {"src": "c", "dst": "d"},
        {"src": "e", "dst": "f"},
        {"src": "g", "dst": "h"},
    ]
    top = attention_to_contrib(flows, weights)
    assert len(top) == 4


def test_evidence_build() -> None:
    flows = [{"src": "10.0.0.1", "dst": "10.0.0.2", "port": 445, "flags": "SYN", "contrib": 0.5}]
    ev = build_evidence(
        1, 0.7, "LateralMovement", flows, codebook_path=[12, 37], confidence=0.8, plausibility=1.0
    )
    assert ev.stage == "LateralMovement"
    assert ev.mitre_technique != ""
    assert len(ev.top_flows) == 1
    md = evidence_to_markdown(ev)
    assert "Window 1" in md
    assert "T1021" in md
