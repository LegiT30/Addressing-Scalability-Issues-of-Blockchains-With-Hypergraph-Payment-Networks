#!/usr/bin/env python3
# scripts/make_supernode_edges_fixed.py

import pandas as pd, json, os, sys
from topologies.utils import edges_df_to_nx, create_supernode_hyperedges

DATA_DIR = "../ln_data"
BASE_EDGES_CSV = f"{DATA_DIR}/ln_edges.csv"
OUT_DIR = "runs"
OUT_HYPERJSON = os.path.join(OUT_DIR, "supernode_hyper.json")
OUT_EDGES_CSV = os.path.join(OUT_DIR, "supernode_edges.csv")
os.makedirs(OUT_DIR, exist_ok=True)

print("Loading:", BASE_EDGES_CSV)
if not os.path.exists(BASE_EDGES_CSV):
    raise SystemExit("Base edges CSV not found at %s" % BASE_EDGES_CSV)

df = pd.read_csv(BASE_EDGES_CSV)
print("Loaded edges_df shape:", df.shape)
print("columns:", list(df.columns))

# --- identify endpoint columns robustly ---
cands = list(df.columns)
# common names
if 'src' in cands and 'trg' in cands:
    src_col, trg_col = 'src', 'trg'
elif 'source' in cands and 'target' in cands:
    src_col, trg_col = 'source', 'target'
else:
    # fallback to using 2nd and 3rd columns (after snapshot_id)
    src_col, trg_col = cands[1], cands[2]
print("Using endpoint columns:", src_col, trg_col)

# --- Option: filter to enabled channels for topology building ---
# If you want disabled channels included, set include_disabled=True
include_disabled = False
if 'disabled' in df.columns and not include_disabled:
    print("Filtering out disabled channels (disabled=True). Before:", len(df))
    df = df[df['disabled'] != True]
    print("After:", len(df))

# Build graph (only using endpoints), do NOT filter by capacity to create topology
G = edges_df_to_nx(df.rename(columns={src_col:'src', trg_col:'trg'}))
print("Constructed graph nodes,edges:", G.number_of_nodes(), G.number_of_edges())

# Create supernode hyperedges
print("Running supernode selection...")
hyperedges, node_to_hyperedges, node_caps = create_supernode_hyperedges(G)
print("Hyperedges count:", len(hyperedges))
if len(hyperedges) > 0:
    sizes = [len(h) for h in hyperedges]
    print("Hyperedge sizes: max", max(sizes), "median", sorted(sizes)[len(sizes)//2])

# If capacities are present in original df, compute node_caps if empty
if not node_caps and 'capacity' in df.columns:
    print("Computing realistic node_caps from original capacities.")
    node_total = {}
    for _, r in df.iterrows():
        u, v, cap = r[src_col], r[trg_col], float(r['capacity'])
        node_total[u] = node_total.get(u, 0.0) + cap
        node_total[v] = node_total.get(v, 0.0) + cap
    for v, idxs in node_to_hyperedges.items():
        if not idxs:
            continue
        per = node_total.get(v, 1.0) / len(idxs)
        for idx in idxs:
            node_caps[(v, idx)] = per

# Save hyperjson (for inspection)
with open(OUT_HYPERJSON, 'w') as f:
    j = {'hyperedges':[list(h) for h in hyperedges], 'node_caps': {f"{k[0]}|{k[1]}":v for k,v in node_caps.items()}}
    json.dump(j, f)
print("Wrote hyperjson:", OUT_HYPERJSON)

# Convert hyperedges -> directed clique edges (fallback to original edges if none)
rows = []
for idx, hed in enumerate(hyperedges):
    if not hed: 
        continue
    for u in hed:
        cap = node_caps.get((u, idx), None)
        if cap is None:
            cap = 1.0
        for v in hed:
            if u == v: 
                continue
            rows.append({'src':u, 'trg':v, 'capacity':cap, 'base_fee':100, 'fee_rate':1, 'enabled':True})

if rows:
    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_EDGES_CSV, index=False)
    print("Wrote supernode edges CSV with %d rows -> %s" % (len(out_df), OUT_EDGES_CSV))
else:
    print("No hyperedges generated; falling back to original edges CSV copy.")
    df.rename(columns={src_col:'src', trg_col:'trg'}).to_csv(OUT_EDGES_CSV, index=False)
    print("Wrote fallback original edges CSV ->", OUT_EDGES_CSV)
