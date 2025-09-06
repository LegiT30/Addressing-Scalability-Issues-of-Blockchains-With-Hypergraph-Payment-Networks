# topologies/nch.py
"""
Create NCH hyperedges:
 - compute greedy vertex cover (pick highest-degree node, remove incident edges)
 - for each cover node c, create hyperedge H_c = neighbors(c)
 - compute node_to_hyperedges mapping and default node_caps (empty)
"""
from collections import defaultdict
import networkx as nx

def greedy_vertex_cover(G, max_nodes=None):
    """
    Greedy approx vertex cover: repeatedly pick node with highest degree,
    add to cover and remove incident edges until no edges remain or max_nodes reached.
    """
    H = G.copy()
    cover = set()
    # degree dict
    while H.number_of_edges() > 0:
        # choose node with max degree
        node, deg = max(H.degree(), key=lambda x: x[1])
        cover.add(node)
        # remove node and its edges
        H.remove_node(node)
        if max_nodes is not None and len(cover) >= max_nodes:
            break
    return cover

def create_nch(G: nx.Graph, max_cover_size=None, use_edge_capacity: bool = False):
    """
    Build NCH hyperedges from graph G.
    Returns:
      hyperedges: list of frozenset(member nodes)
      node_to_hyperedges: dict node -> list of hyperedge indices
      node_capacity_in_hyperedge: dict (node, hed_idx) -> capacity (empty if use_edge_capacity False)
    Params:
      max_cover_size: if set, stop cover selection at this many nodes (optional).
      use_edge_capacity: if True, downstream script should compute actual capacity splits.
    """
    cover = greedy_vertex_cover(G, max_nodes=max_cover_size)
    hyperedges = []
    node_to_hyperedges = defaultdict(list)
    for idx, c in enumerate(sorted(list(cover))):
        neighs = set(G.neighbors(c))
        if len(neighs) == 0:
            continue
        hed = frozenset(neighs)
        hyperedges.append(hed)
        for v in hed:
            node_to_hyperedges[v].append(idx)

    # node_caps remains empty here; caller can compute deposits using original capacities
    node_capacity_in_hyperedge = {}
    if use_edge_capacity:
        # placeholder: caller should fill node_capacity_in_hyperedge based on original capacities
        pass

    return hyperedges, dict(node_to_hyperedges), node_capacity_in_hyperedge
