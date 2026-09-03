"""Graph builder for temporal host graphs.

Hosts are nodes, flows are timed edges.
This is what makes lateral movement visible as graph movement.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import networkx as nx


@dataclass
class GraphSnapshot:
    """One graph snapshot S_t."""

    window_id: int
    graph: nx.DiGraph
    num_nodes: int
    num_edges: int
    stats: Dict[str, float]


def build_graph(
    flows: List[dict],
    window_id: int = 0,
) -> GraphSnapshot:
    """Build directed graph from flow dicts.

    Each flow dict should have src, dst, and edge attributes.
    Hosts are deduplicated as nodes.

    Args:
        flows: List of flow dicts with src, dst, bytes, packets, flags
        window_id: Window identifier

    Returns:
        GraphSnapshot with DiGraph and stats
    """
    g = nx.DiGraph()

    for f in flows:
        src = f.get("src", "unknown")
        dst = f.get("dst", "unknown")
        if src not in g:
            g.add_node(src, role=f.get("src_role", "workstation"))
        if dst not in g:
            g.add_node(dst, role=f.get("dst_role", "workstation"))

        g.add_edge(
            src,
            dst,
            bytes=f.get("bytes", 0),
            packets=f.get("packets", 0),
            flags=f.get("flags", 0),
            duration=f.get("duration", 0.0),
        )

    stats = {
        "avg_degree": sum(dict(g.degree()).values()) / max(len(g.nodes), 1),
        "density": nx.density(g) if len(g.nodes) > 1 else 0.0,
    }

    return GraphSnapshot(
        window_id=window_id,
        graph=g,
        num_nodes=g.number_of_nodes(),
        num_edges=g.number_of_edges(),
        stats=stats,
    )


def graph_to_tensors(snapshot: GraphSnapshot) -> Tuple[List[int], List[List[int]], List[float]]:
    """Convert graph to tensors for model input.

    Returns node list, edge index, edge attrs.
    Scaffold for torch_geometric integration.
    """
    nodes = list(snapshot.graph.nodes)
    node_to_idx = {n: i for i, n in enumerate(nodes)}
    edge_index = []
    edge_attr = []

    for src, dst, data in snapshot.graph.edges(data=True):
        edge_index.append([node_to_idx[src], node_to_idx[dst]])
        edge_attr.append(float(data.get("bytes", 0)))

    return nodes, edge_index, edge_attr
