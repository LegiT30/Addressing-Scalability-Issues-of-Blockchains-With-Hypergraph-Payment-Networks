#!/usr/bin/env python3
"""
scripts/make_nch_edges.py

Generate NCH hyperjson and (optionally) clique-style edges CSV for Approach A.

Usage:
  python3 scripts/make_nch_edges.py --out_prefix runs/nch_1 --ln_edges ../ln_data/ln_edges.csv --use_edge_capacity --to_clique --max_clique_size 500 --verbose

Outputs:
  <out_prefix>_hyper.json
  <out_prefix>_edges.csv  (only if --to_clique)
"""
import os, json, argparse
import pandas as pd
from collections import defaultdict
from topologies.nch import create_nch
from topologies.utils import edges_df_to_nx

def detect_endpoint_cols(df):
    cols = list(df.columns)
    if 'src' in cols and 'trg' in cols:
        return 'src','trg'
    if 'source' in cols and 'target' in cols:
        return 'source','target'
    # fallback
    return cols[1], cols[2]

def compute_node_totals(df, src_col, trg_col, cap_col='capacity'):
    totals = defaultdict(float)
    if cap_col not in df.columns:
        return {}
    for _, r in df.iterrows():
        try:
            c = float(r.get(cap_col, 0.0))
        except Exception:
            c = 0.0
        totals[r[src_col]] += c
        totals[r[trg_col]] += c
    return dict(totals)

def export_hyperjson(hyperedges, node_caps, path):
    node_caps_serial = { f"{k[0]}|{k[1]}": v for k,v in node_caps.items() }
    j = {"hyperedges":[list(h) for h in hyperedges], "node_caps": node_caps_serial}
    with open(path, "w") as fh:
        json.dump(j, fh)
    return path

def export_clique(hyperedges, node_caps, out_csv, max_clique_size, fee_profile=None):
    rows=[]
    sizes=[len(h) for h in hyperedges]
    if sizes and max(sizes) > max_clique_size:
        raise RuntimeError("Refusing to export clique: max hyperedge size %d > %d" % (max(sizes), max_clique_size))
    for idx, hed in enumerate(hyperedges):
        for u in hed:
            cap_u = node_caps.get((u, idx), 1.0)
            base_fee = fee_profile.get(u, 100.0) if fee_profile else 100.0
            fee_rate = 1.0
            for v in hed:
                if u==v: continue
                rows.append({'src':u,'trg':v,'capacity':cap_u,'base_fee':base_fee,'fee_rate':fee_rate,'enabled':True})
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    return out_csv, len(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out_prefix", required=True)
    p.add_argument("--ln_edges", default="../ln_data/ln_edges.csv")
    p.add_argument("--max_cover_size", type=int, default=None)
    p.add_argument("--use_edge_capacity", action="store_true", help="split node totals across hyperedges")
    p.add_argument("--to_clique", action="store_true")
    p.add_argument("--max_clique_size", type=int, default=500)
    p.add_argument("--verbose", action="store_true")
    args=p.parse_args()

    if not os.path.exists(args.ln_edges):
        raise SystemExit("ln_edges not found: %s" % args.ln_edges)
    df=pd.read_csv(args.ln_edges)
    src_col, trg_col = detect_endpoint_cols(df)
    tmp=df.rename(columns={src_col:'src', trg_col:'trg'})
    G=edges_df_to_nx(tmp)
    if args.verbose:
        print("Graph nodes/edges:", G.number_of_nodes(), G.number_of_edges())

    hyperedges, node_to_hyperedges, node_caps = create_nch(G, max_cover_size=args.max_cover_size, use_edge_capacity=False)
    if args.verbose:
        sizes=[len(h) for h in hyperedges]
        print("Hyperedges:", len(hyperedges), "max:", max(sizes) if sizes else 0)

    # compute node_caps from original capacities if requested
    if args.use_edge_capacity and 'capacity' in df.columns:
        node_totals = compute_node_totals(df, src_col, trg_col, cap_col='capacity')
        node_caps = {}
        for node, hed_idxs in node_to_hyperedges.items():
            if not hed_idxs: continue
            total=node_totals.get(node, 0.0) or 1.0
            per = float(total)/len(hed_idxs)
            for idx in hed_idxs:
                node_caps[(node, idx)] = per
        if args.verbose:
            print("Computed node_caps entries:", len(node_caps))

    out_prefix=args.out_prefix
    os.makedirs(os.path.dirname(out_prefix) or ".", exist_ok=True)
    hyperjson_path = f"{out_prefix}_hyper.json"
    export_hyperjson(hyperedges, node_caps, hyperjson_path)
    print("Wrote:", hyperjson_path)

    if args.to_clique:
        # optional fee profile: reuse fee_base_msat if available
        fee_profile={}
        for col in ['fee_base_msat','base_fee','fee_base_msat']:
            if col in df.columns:
                # build per-node mean
                profile={}
                counts={}
                for _,r in df.iterrows():
                    u=r[src_col]; v=r[trg_col]
                    try:
                        fee=float(r[col])
                    except:
                        fee=0.0
                    profile[u]=profile.get(u,0.0)+fee; counts[u]=counts.get(u,0)+1
                    profile[v]=profile.get(v,0.0)+fee; counts[v]=counts.get(v,0)+1
                fee_profile={n:(profile[n]/counts[n] if counts[n]>0 else 100.0) for n in profile}
                break
        edges_csv = f"{out_prefix}_edges.csv"
        path, rows = export_clique(hyperedges, node_caps, edges_csv, args.max_clique_size, fee_profile)
        print("Wrote clique CSV:", path, "rows:", rows)

if __name__ == "__main__":
    main()
