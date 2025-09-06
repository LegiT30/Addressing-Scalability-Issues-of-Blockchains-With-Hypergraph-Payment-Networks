# topologies/supernodes.py
import networkx as nx
from collections import deque
from typing import Set, Dict

def select_supernodes(G: nx.Graph, max_search_depth: int = 4, max_states: int = 5000) -> Set:
    """
    Select supernodes following Algorithm 1 (practical version).
    - G: undirected NetworkX graph
    - max_search_depth: maximum path length (edges) to consider when searching for monotone paths
    - max_states: safety cap for number of BFS states explored in exists_monotone_path
    Returns: set S of chosen supernodes
    """

    # deterministic integer id map for nodes (used in monotonicity check)
    node_list = list(G.nodes())
    id_map: Dict = {}
    for i, n in enumerate(node_list):
        try:
            id_map[n] = int(n)
        except Exception:
            id_map[n] = i

    S = set(G.nodes())

    # Precompute neighbor sets for speed
    neigh = {n: set(G.neighbors(n)) for n in G.nodes()}

    def two_hop_nodes(n):
        # BFS up to depth 2, return set of nodes within 2 hops (including n)
        visited = {n}
        q = deque([(n, 0)])
        while q:
            cur, d = q.popleft()
            if d >= 2:
                continue
            for nb in neigh[cur]:
                if nb not in visited:
                    visited.add(nb)
                    q.append((nb, d + 1))
        return visited

    def exists_monotone_path(u, v, Vn_set, max_depth, max_states_local):
        """
        Return True if there exists a simple path from u to v inside Vn_set of length <= max_depth
        whose internal nodes (excluding u and v) have strictly decreasing id() values
        along the path: id(u2) > id(u3) > ... > id(ul-1).

        Implementation notes:
         - We treat states as (current_node, prev_internal_id)
         - prev_internal_id is None if we haven't visited any internal node yet (i.e., at start).
         - We maintain a seen_states set of (node, prev_internal_id) to avoid duplicate work.
         - We cap number of explored states to max_states_local to avoid explosion.
        """
        if u == v:
            return True
        # quick check: both must be in Vn_set
        if u not in Vn_set or v not in Vn_set:
            return False

        # BFS queue: (current_node, prev_internal_id, depth)
        q = deque()
        # initial: at u, no internal yet, depth=0
        q.append((u, None, 0))
        seen_states = set()
        # count visited states to avoid explosion
        states_explored = 0

        while q:
            cur, prev_internal_id, depth = q.popleft()
            # safety
            states_explored += 1
            if states_explored > max_states_local:
                # give up (treat as not found to be conservative)
                return False

            if depth >= max_depth:
                continue

            for nb in neigh[cur]:
                if nb not in Vn_set:
                    continue
                # skip returning to already visited nodes along the same path by using seen_states
                # state key depends on whether we have started internal monotone sequence
                if nb == v:
                    # reaching destination: check monotone constraint for the last internal if needed
                    if prev_internal_id is None:
                        return True
                    # If prev_internal_id exists, ensure prev_internal_id > id(v) only if v counts as internal
                    # but v is destination so we allow it. The monotone rule applies only to internal nodes,
                    # so reaching v is always allowed (we enforced monotonicity while traversing internal nodes).
                    return True

                # nb is an internal candidate (not u and not v)
                if prev_internal_id is None:
                    # first internal node after u: allowed, set new prev_internal_id = id(nb)
                    new_state = (nb, id_map.get(nb, 0))
                    if new_state in seen_states:
                        continue
                    seen_states.add(new_state)
                    q.append((nb, new_state[1], depth + 1))
                else:
                    # must have strictly decreasing ids: prev_internal_id > id(nb)
                    nb_id = id_map.get(nb, 0)
                    if prev_internal_id > nb_id:
                        new_state = (nb, nb_id)
                        if new_state in seen_states:
                            continue
                        seen_states.add(new_state)
                        q.append((nb, nb_id, depth + 1))
                    else:
                        # cannot extend this neighbor because monotonicity violated
                        continue

        return False

    # Main selection loop
    for n in list(G.nodes()):
        Vn = two_hop_nodes(n)
        Vn_set = Vn  # already a set
        NGn = neigh[n]
        removed = False
        NGn_list = list(NGn)
        ln = len(NGn_list)
        for i in range(ln):
            if removed:
                break
            u = NGn_list[i]
            for j in range(i + 1, ln):
                v = NGn_list[j]
                # quick check: if neighbors directly connected => remove n
                if v in neigh[u]:
                    if n in S:
                        S.discard(n)
                    removed = True
                    break
                # otherwise, try to find a monotone path within Vn up to max_search_depth
                # but first cheap check: both u and v must be in Vn_set (they should be)
                if u not in Vn_set or v not in Vn_set:
                    continue
                found = exists_monotone_path(u, v, Vn_set, max_search_depth, max_states)
                if found:
                    if n in S:
                        S.discard(n)
                    removed = True
                    break
    return S
