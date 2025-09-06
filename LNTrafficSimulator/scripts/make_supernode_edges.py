#!/usr/bin/env python3
# scripts/make_supernode_edges.py
import pandas as pd
import json
import os
import sys
from topologies.utils import edges_df_to_nx, create_supernode_hyperedges

# --- CONFIG --- adjust these paths if needed
DATA_DIR = "../ln_data"                # where your ln_edges.csv or base edge CSV lives
BASE_EDGES_CSV = f"{DATA_DIR}/ln_edges.csv"
OUT_HYPERJSON = "runs/supernode_hyper.json"
OUT_EDGES_CSV = "runs/supernode_edges.csv"
os.makedirs("runs", exist_ok=True)

# --- load base (pairwise) edges CSV and build NX graph ---
print("Loading base edges CSV:", BASE_EDGES_CSV)
edges_df = pd.read_csv(BASE_EDGES_CSV)
G = edges_df_to_nx(edges_df)   # builds an undirected NetworkX graph from src/trg columns

# --- create supernode hyperedges ---
print("Creating supernode hyperedges...")
hyperedges, node_to_hyperedges, node_caps = create_supernode_hyperedges(G)

# node_caps may be uniform (1.0) from the utils helper; if you want realistic capacities,
# compute node_total from edges_df and split evenly across hyperedges for each node.
# We'll try to produce node_caps from edges_df if node_caps seems uniform:

# try to make realistic capacities if edges_df has 'capacity' column
if len(node_caps) == 0 and "capacity" in edges_df.columns:
    print("Computing realistic node_caps from original edge capacities...")
    # sum incident capacities per node
    node_totals = {}
    for _, r in edges_df.iterrows():
        u, v, cap = r['src'], r['trg'], float(r['capacity'])
        node_totals[u] = node_totals.get(u, 0.0) + cap
        node_totals[v] = node_totals.get(v, 0.0) + cap
    # split node_total evenly across hyperedges the node participates in
    for node, idxs in node_to_hyperedges.items():
        if not idxs:
            continue
        total = node_totals.get(node, 1.0)
        per = total / len(idxs)
        for idx in idxs:
            node_caps[(node, idx)] = per

# --- write hyperjson (simple format) ---
print("Writing hyperjson:", OUT_HYPERJSON)
j = {
    "hyperedges": [list(h) for h in hyperedges],
    "node_caps": { f"{n}|{i}": v for (n,i), v in node_caps.items() }
}
with open(OUT_HYPERJSON, "w") as f:
    json.dump(j, f)

# --- convert hyperjson -> directed edges CSV using script if present, or inline convert ---
print("Converting hyperedges to directed edges CSV:", OUT_EDGES_CSV)
rows = []
for idx, hed in enumerate(hyperedges):
    for u in hed:
        # capacity contributed by u in this hyperedge
        cap = node_caps.get((u, idx), None)
        if cap is None:
            # fallback: small uniform deposit so edges survive drop_low_cap check
            cap = 1.0
        for v in hed:
            if u == v:
                continue
            rows.append({
                "src": u,
                "trg": v,
                "capacity": cap,
                "base_fee": 100,      # adjust if you want to copy original fees
                "fee_rate": 1,
                "enabled": True
            })

out_df = pd.DataFrame(rows)
out_df.to_csv(OUT_EDGES_CSV, index=False)
print("Wrote edges CSV with %d rows" % len(out_df))
print("Done. Now run the simulator on:", OUT_EDGES_CSV)
