"""Attention over flows and graph edges.

Gives per edge weight that drove the latent drift.
Works with simple mean pool now, will hook into GNN attention later.
"""

from typing import Dict, List

import torch
import torch.nn.functional as F


def edge_attention(
    edge_attrs: torch.Tensor,
    latent: torch.Tensor | None = None,
) -> List[float]:
    """Compute attention weights for edges.

    For scaffold, use softmax over edge magnitude as proxy for attention.
    Real version will use learned attention from TGN.

    Args:
        edge_attrs: Tensor [num_edges, dim]
        latent: Optional latent to condition on

    Returns:
        List of weights summing to 1
    """
    if edge_attrs.numel() == 0:
        return []

    # Magnitude per edge
    mag = edge_attrs.norm(dim=1)  # [E]
    # Softmax to get attention
    weights = F.softmax(mag, dim=0)
    return weights.tolist()


def top_edges(
    flows: List[Dict],
    weights: List[float],
    k: int = 5,
) -> List[Dict]:
    """Pair flows with attention and return top k."""
    paired = list(zip(flows, weights))
    paired.sort(key=lambda x: x[1], reverse=True)
    out = []
    for flow, w in paired[:k]:
        out.append({**flow, "attention": float(w)})
    return out


def attention_to_contrib(flows: List[Dict], weights: List[float]) -> List[Dict]:
    """Convert attention to contrib field expected by evidence builder."""
    top = top_edges(flows, weights, k=5)
    for f in top:
        f["contrib"] = f.pop("attention")
        f["reason"] = "high attention on drift"
    return top
