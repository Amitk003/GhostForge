"""Explain package for evidence chains."""

from ghostforge.explain.attention import attention_to_contrib, edge_attention
from ghostforge.explain.attribution import feature_attribution, top_features
from ghostforge.explain.evidence import EvidenceChain, build_evidence, evidence_to_markdown

__all__ = [
    "EvidenceChain",
    "build_evidence",
    "evidence_to_markdown",
    "feature_attribution",
    "top_features",
    "edge_attention",
    "attention_to_contrib",
]
