#!/usr/bin/env python3
"""
scripts/make_fhs_edges.py

Generate FHS hyperedges (fixed hyperedge size grouping) and write a hyperjson file
suitable for the native hyperedge simulator (Approach B).

Optional: also export a clique-style directed edges CSV (Approach A).
Be careful: clique export can blow up O(k^2) for large hyperedges.

Usage:
    python scripts/make_fhs_edges.py --m_max 5 --out_prefix runs/fhs_5 --ln_edges ../ln_data/ln_edges.csv

Options:
    --m_max INT            : fixed hyperedge size (e.g., 3,5,20,5000)
    --out_prefix STR       : prefix for output files (hyperjson and optional edges CSV)
    --ln_edges PATH        : path to ln_edges.csv (default ../ln_data/ln_edges.csv)
    --use_edge_capacity    : compute node deposits from original capacities (default: True)
    --to_clique            : also produce clique edges CSV (may be huge)
    --max_clique_size INT  : maximum hyperedge size allowed for clique export (default: 500)
    --verbose              : print extra info
"""

import os
import json
import argparse
from collections import defaultdict
import pandas as pd
from topologies.fhs import create_fhs
from topologies.utils import edges_df_to_nx

def detect_endpoint_cols(df: pd.DataFrame):
    cols = list(df.columns)
    if 'src' in cols and 'trg' in cols:
        return 'src', 'trg'
    if 'source' in cols and 'target' in cols:
        return 'source', 'target'
    # common alt names
    for a,b in [('node1','node2'), ('u','v'), ('from','to')]:
        if a in cols and b in cols:
            return a,b
    # fallback: use second and third columns (first may be snapshot id)
    if len(cols) >= 3:
        return cols[1], cols[2]
    raise RuntimeError("Cannot detect endpoint columns in ln_edges.csv; columns: %s" % cols)

def compute_node_totals(edges_df, src_col, trg_col, cap_col='capacity'):
    node_totals = defaultdict(float)
    if cap_col not in edges_df.columns:
        # maybe capacity is named differently
        raise RuntimeError("capacity column not found in edges dataframe")
    for _, r in edges_df.iterrows():
        u = r[src_col]
        v = r[trg_col]
        try:
            cap = float(r[cap_col])
        except Exception:
            cap = 0.0
        node_totals[u] += cap
        node_totals[v] += cap
    return dict(node_totals)

def export_hyperjson(hyperedges, node_caps, out_path):
    # normalize node_caps keys as "node|idx" strings for portability
    node_caps_serial = { f"{k[0]}|{k[1]}": v for k,v in node_caps.items() }
    j = {"hyperedges":[list(h) for h in hyperedges], "node_caps": node_caps_serial}
    with open(out_path, "w") as fh:
        json.dump(j, fh)
    return out_path

def export_clique_edges_csv(hyperedges, node_caps, out_path, warn_threshold=500):
    # refuse to create clique if any hyperedge is larger than warn_threshold unless user overrides
    sizes = [len(h) for h in hyperedges]
    if sizes and max(sizes) > warn_threshold:
        raise RuntimeError("Refusing to export clique: hyperedge max size %d > warn_threshold %d" % (max(sizes), warn_threshold))
    rows = []
    for idx, hed in enumerate(hyperedges):
        for u in hed:
            cap = node_caps.get((u, idx), None)
            if cap is None:
                cap = 1.0
            for v in hed:
                if u == v:
                    continue
                rows.append({'src': u, 'trg': v, 'capacity': cap, 'base_fee': 100, 'fee_rate': 1, 'enabled': True})
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    return out_path, len(rows)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--m_max", type=int, required=True, help="fixed hyperedge size (m_max)")
    p.add_argument("--out_prefix", type=str, required=True, help="output prefix (path without extension)")
    p.add_argument("--ln_edges", type=str, default="../ln_data/ln_edges.csv", help="path to ln_edges.csv")
    p.add_argument("--use_edge_capacity", action="store_true", default=True, help="compute node deposits from original capacities")
    p.add_argument("--to_clique", action="store_true", help="also export clique-style edges CSV (may be huge)")
    p.add_argument("--max_clique_size", type=int, default=500, help="max hyperedge size allowed to export clique")
    p.add_argument("--verbose", action="store_true", help="verbose output")
    args = p.parse_args()

    ln_path = args.ln_edges
    if not os.path.exists(ln_path):
        raise SystemExit("ln_edges.csv not found at %s" % ln_path)

    df = pd.read_csv(ln_path)
    if args.verbose:
        print("Loaded ln_edges:", ln_path, "shape:", df.shape)

    # detect endpoint columns robustly
    src_col, trg_col = detect_endpoint_cols(df)
    if args.verbose:
        print("Detected endpoint columns:", src_col, trg_col)

    # build undirected networkx graph for topology grouping
    # edges_df_to_nx expects 'src','trg' column names, so rename temporarily
    tmp = df.rename(columns={src_col:'src', trg_col:'trg'})
    G = edges_df_to_nx(tmp)
    if args.verbose:
        print("Constructed NX graph nodes/edges:", G.number_of_nodes(), G.number_of_edges())

    # create FHS hyperedges
    hyperedges, node_to_hyperedges, node_caps = create_fhs(G, args.m_max, use_edge_capacity=False)
    # create_fhs returns node_caps if use_edge_capacity True; we passed False for now
    if args.verbose:
        sizes = [len(h) for h in hyperedges]
        print("FHS created hyperedges:", len(hyperedges))
        if sizes:
            print("size stats: max=%d median=%d mean=%.1f" % (max(sizes), sorted(sizes)[len(sizes)//2], sum(sizes)/len(sizes)))

    # Compute node_caps using original capacities if requested
    if args.use_edge_capacity:
        if 'capacity' not in df.columns:
            print("Warning: 'capacity' column not found in ln_edges.csv; falling back to uniform deposits.")
        else:
            if args.verbose:
                print("Computing node total capacities from ln_edges.csv and splitting across hyperedges")
            node_totals = compute_node_totals(df, src_col, trg_col, cap_col='capacity')
            node_caps = {}
            for node, hed_idxs in node_to_hyperedges.items():
                if not hed_idxs:
                    continue
                total = node_totals.get(node, 0.0)
                # Avoid zero total: if zero, assign small positive deposit so hyperedge exists
                if total <= 0.0:
                    total = 1.0
                per = total / len(hed_idxs)
                for idx in hed_idxs:
                    node_caps[(node, idx)] = float(per)
            if args.verbose:
                print("Computed node_caps entries:", len(node_caps))

    # Ensure output directory exists
    out_prefix = args.out_prefix
    out_dir = os.path.dirname(out_prefix)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    hyperjson_path = f"{out_prefix}_hyper.json"
    export_hyperjson(hyperedges, node_caps, hyperjson_path)
    print("Wrote hyperjson:", hyperjson_path, "  hyperedges:", len(hyperedges))

    # print some hyperedge size histogram info
    if hyperedges:
        sizes = [len(h) for h in hyperedges]
        print("Hyperedge size stats: count=%d min=%d max=%d median=%d mean=%.2f" %
              (len(sizes), min(sizes), max(sizes), sorted(sizes)[len(sizes)//2], sum(sizes)/len(sizes)))

    # Optionally export clique edges CSV (Approach A)
    if args.to_clique:
        max_size = max([len(h) for h in hyperedges]) if hyperedges else 0
        if max_size > args.max_clique_size:
            raise SystemExit("Refusing to export clique: max hyperedge size %d > max_clique_size %d. Use smaller m_max or skip clique export." % (max_size, args.max_clique_size))
        edges_csv_path = f"{out_prefix}_edges.csv"
        path, rows = export_clique_edges_csv(hyperedges, node_caps, edges_csv_path, warn_threshold=args.max_clique_size)
        print("Wrote clique edges CSV:", path, "rows:", rows)

    print("Done.")

if __name__ == "__main__":
    main()
