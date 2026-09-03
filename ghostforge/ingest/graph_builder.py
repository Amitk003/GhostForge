"""Graph builder for temporal host graphs.

Hosts are nodes, flows are timed edges.
This is what makes lateral movement visible as graph movement.
"""

from dataclasses import dataclass

import networkx as nx


@dataclass
class GraphSnapshot:
    """One graph snapshot S_t."""

    window_id: int
    graph: nx.DiGraph
    num_nodes: int
    num_edges: int
    stats: dict[str, float]


def build_graph(
    flows: list[dict],
    window_id: int = 0,
) -> GraphSnapshot:
    """Build directed graph from flow dicts.

    Each flow dict should have src, dst, and edge attributes.
    Hosts are deduplicated as nodes. Handles missing fields safely.

    Args:
        flows: List of flow dicts with src, dst, bytes, packets, flags
        window_id: Window identifier

    Returns:
        GraphSnapshot with DiGraph and stats
    """
    g = nx.DiGraph()

    for f in flows:
        src = str(f.get("src") or f.get("src_ip") or f.get("orig_h") or "unknown")
        dst = str(f.get("dst") or f.get("dst_ip") or f.get("resp_h") or "unknown")
        if src == "unknown" and dst == "unknown":
            continue
        src_role = f.get("src_role") or f.get("role_src") or "workstation"
        dst_role = f.get("dst_role") or f.get("role_dst") or "workstation"

        if src not in g:
            g.add_node(src, role=src_role)
        if dst not in g:
            g.add_node(dst, role=dst_role)

        # Edge dedup: sum if same edge repeats in window
        if g.has_edge(src, dst):
            prev = g[src][dst]
            g[src][dst]["bytes"] = prev.get("bytes", 0) + int(
                f.get("bytes", f.get("totbytes", f.get("total_bytes", 0))) or 0
            )
            g[src][dst]["packets"] = prev.get("packets", 0) + int(
                f.get("packets", f.get("totpkts", 0)) or 0
            )
            # Keep max flags
            g[src][dst]["flags"] = max(prev.get("flags", 0), int(f.get("flags", 0) or 0))
        else:
            g.add_edge(
                src,
                dst,
                bytes=int(f.get("bytes", f.get("totbytes", f.get("total_bytes", 0))) or 0),
                packets=int(f.get("packets", f.get("totpkts", f.get("total_pkts", 0))) or 0),
                flags=int(f.get("flags", 0) or 0),
                duration=float(f.get("duration", f.get("dur", 0.0)) or 0.0),
            )

    num_nodes = g.number_of_nodes()
    num_edges = g.number_of_edges()

    # Stats with safe guards
    try:
        avg_deg = sum(dict(g.degree()).values()) / max(num_nodes, 1)
    except Exception:
        avg_deg = 0.0
    try:
        dens = nx.density(g) if num_nodes > 1 else 0.0
    except Exception:
        dens = 0.0
    # Extra stats for model
    total_bytes = sum(d.get("bytes", 0) for _, _, d in g.edges(data=True))
    stats = {
        "avg_degree": float(avg_deg),
        "density": float(dens),
        "total_bytes": float(total_bytes),
        "bytes_per_edge": float(total_bytes / max(num_edges, 1)),
    }

    return GraphSnapshot(
        window_id=window_id,
        graph=g,
        num_nodes=num_nodes,
        num_edges=num_edges,
        stats=stats,
    )


def build_graph_from_dataframe(
    df, window_id: int = 0, src_col: str = "src", dst_col: str = "dst"
) -> GraphSnapshot:
    """Build graph directly from polars or pandas dataframe.

    Tries to find src and dst columns case insensitive.
    """
    # Convert to list of dicts safely
    try:
        # Polars
        flows = df.to_dicts()
    except Exception:
        try:
            flows = df.to_dict(orient="records")
        except Exception:
            flows = []

    # Normalize src/dst col names if not exact
    normalized_flows = []
    for row in flows:
        # Case insensitive lookup
        src = None
        dst = None
        for k in row.keys():
            if k.lower() in {src_col.lower(), "src_ip", "id.orig_h", "srcaddr"}:
                src = row[k]
            if k.lower() in {dst_col.lower(), "dst_ip", "id.resp_h", "dstaddr"}:
                dst = row[k]
        normalized_flows.append({"src": src, "dst": dst, **row})

    return build_graph(normalized_flows, window_id=window_id)


def graph_to_tensors(snapshot: GraphSnapshot) -> tuple[list[int], list[list[int]], list[float]]:
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
