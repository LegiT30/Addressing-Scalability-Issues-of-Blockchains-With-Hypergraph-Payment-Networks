import networkx as nx
from collections import deque
from typing import List, Tuple, Dict, Set

def highest_degree_node(G: nx.Graph):
    """Return the node with highest degree. Tie-break deterministically by node id."""
    # degree view -> list of (node, deg)
    # Use sorted with reverse degree, then node for deterministic tie-break
    return max(G.nodes(), key=lambda n: (G.degree(n), -hash(n)))  # hash used to give deterministic-ish order

def bfs_collect_m(G: nx.Graph, start_node, m_max: int) -> List:
    """
    BFS from start_node collecting at most m_max distinct nodes (including start_node).
    Returns list of nodes in the order visited (root first).
    """
    visited = set([start_node])
    q = deque([start_node])
    collected = [start_node]
    while q and len(collected) < m_max:
        cur = q.popleft()
        for nb in G.neighbors(cur):
            if nb not in visited:
                visited.add(nb)
                q.append(nb)
                collected.append(nb)
                if len(collected) >= m_max:
                    break
    return collected

def create_fhs(G_input: nx.Graph, m_max: int, use_edge_capacity: bool = True):
    """
    Generate Fixed-Hyperedge-Size hypergraph from copy of G_input.
    Returns:
      - hyperedges: list of frozenset(nodes)
      - node_to_hyperedges: dict node -> list of hyperedge indices
      - node_capacity_in_hyperedge: dict (node, hedg_idx) -> capacity (float) [optional]
    The algorithm destructively updates a copy of the graph (G_work).
    """
    # Work on a copy
    G = G_input.copy()

    hyperedges: List[frozenset] = []
    node_to_hyperedges: Dict = {n: [] for n in G_input.nodes()}

    # main loop: while there are edges left in G
    while G.number_of_edges() > 0:
        # find highest-degree node (deterministic tie-break)
        # guard: if graph became empty of nodes, break
        if G.number_of_nodes() == 0:
            break
        # pick highest-degree node (deterministic by node's hash if tie)
        # safer deterministic ordering: sort nodes by (degree, node id)
        # here we use tuple (degree, -hash(node)) so larger degree -> selected
        node = max(G.nodes(), key=lambda n: (G.degree(n), -hash(n)))

        # run BFS to collect up to m_max nodes
        Ve_list = bfs_collect_m(G, node, m_max)
        Ve_set = set(Ve_list)
        if len(Ve_set) == 0:
            # nothing to add (shouldn't happen), break to avoid infinite loop
            break

        # add hyperedge
        hed_idx = len(hyperedges)
        hyperedges.append(frozenset(Ve_set))
        for v in Ve_set:
            node_to_hyperedges[v].append(hed_idx)

        # remove edges internal to Ve from G
        # create list to remove to avoid modifying while iterating
        internal_edges = [(u, v) for u in Ve_set for v in G.neighbors(u) if v in Ve_set and u < v]
        G.remove_edges_from(internal_edges)

        # remove now-isolated nodes from G
        isolated = [n for n, d in G.degree() if d == 0]
        if isolated:
            G.remove_nodes_from(isolated)

    # Optional: capacity distribution like in NCH:
    node_capacity_in_hyperedge: Dict[Tuple, float] = {}
    if use_edge_capacity:
        # detect if capacities exist
        has_capacity_attr = any('capacity' in d for _, _, d in G_input.edges(data=True))
        if has_capacity_attr:
            # compute node_total from original graph (sum of incident edge capacities)
            node_total = {n: 0.0 for n in G_input.nodes()}
            for u, v, data in G_input.edges(data=True):
                cap = float(data.get('capacity', 0.0))
                # assuming paper credited capacity to both endpoints
                node_total[u] += cap
                node_total[v] += cap

            # split node_total evenly across hyperedges the node participates in
            for v, hed_idxs in node_to_hyperedges.items():
                if not hed_idxs:
                    continue
                total_v = node_total.get(v, 0.0)
                per_hed = total_v / len(hed_idxs)
                for idx in hed_idxs:
                    node_capacity_in_hyperedge[(v, idx)] = per_hed
        else:
            # fallback: uniform 1.0 split
            for v, hed_idxs in node_to_hyperedges.items():
                if not hed_idxs:
                    continue
                per_hed = 1.0 / len(hed_idxs)
                for idx in hed_idxs:
                    node_capacity_in_hyperedge[(v, idx)] = per_hed

    return hyperedges, node_to_hyperedges, node_capacity_in_hyperedge


# quick self-test / demo
if __name__ == "__main__":
    G = nx.Graph()
    G.add_edges_from([
        (1,2),(1,3),(1,4),(2,5),(3,6),(4,7),(5,6),(6,7),(7,8),(8,9),(9,10)
    ])
    for u, v in G.edges():
        G.edges[u,v]['capacity'] = 100.0

    hyperedges, n2h, caps = create_fhs(G, m_max=3, use_edge_capacity=True)
    print("Hyperedges:")
    for i, h in enumerate(hyperedges):
        print(i, sorted(h))
    print("Node->hyperedges:", {k:v for k,v in n2h.items() if v})
    print("Example capacities:", {k:caps[k] for k in list(caps)[:8]})
