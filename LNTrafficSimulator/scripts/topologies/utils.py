# topologies/utils.py
import networkx as nx
import pandas as pd
from .supernodes import select_supernodes

def edges_df_to_nx(edges_df):
    G = nx.Graph()
    for _, r in edges_df.iterrows():
        G.add_edge(r['src'], r['trg'])
    return G

def create_lnrollup_hyperedges(G):
    # single hyperedge of all nodes
    return [frozenset(G.nodes())], {n:[0] for n in G.nodes()}, { (n,0): 1.0 for n in G.nodes() }

def create_supernode_hyperedges(G):
    S = select_supernodes(G)
    hyperedges = []
    node_to_hyperedges = {n: [] for n in G.nodes()}
    for i, s in enumerate(S):
        neighbors = set(G.neighbors(s))
        if not neighbors:
            continue
        hed = frozenset(neighbors)
        hyperedges.append(hed)
        for v in hed:
            node_to_hyperedges[v].append(i)
    # Please compute capacities using node totals in calling code (or set uniform)
    node_capacity = {}
    for v, idxs in node_to_hyperedges.items():
        for idx in idxs:
            node_capacity[(v, idx)] = 1.0/len(idxs) if idxs else 0.0
    return hyperedges, node_to_hyperedges, node_capacity
