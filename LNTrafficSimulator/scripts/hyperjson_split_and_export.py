#!/usr/bin/env python3
"""
hyperjson_split_and_export.py

Input: a hyperjson file (runs/nch_1_hyper.json)
Output:
 - small clique CSV for hyperedges with size <= threshold: <out_prefix>_small_edges.csv
 - big-hyperjson file containing only hyperedges > threshold: <out_prefix>_big_hyper.json

Usage:
 python3 scripts/hyperjson_split_and_export.py --hyper runs/nch_1_hyper.json --out_prefix runs/nch_1 --threshold 500 --verbose
"""
import argparse, json, os
import pandas as pd

def parse_node_caps(raw):
    node_caps = {}
    for k,v in raw.items():
        if "|" in k:
            node, idx = k.split("|",1)
            node_caps[(node, int(idx))] = float(v)
        else:
            try:
                nk = eval(k)
                node_caps[(nk[0], int(nk[1]))] = float(v)
            except Exception:
                pass
    return node_caps

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hyper", required=True)
    p.add_argument("--out_prefix", required=True)
    p.add_argument("--threshold", type=int, default=500)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    j = json.load(open(args.hyper))
    hyperedges = j.get("hyperedges", [])
    node_caps = parse_node_caps(j.get("node_caps", {}))

    small_rows = []
    big_hyperedges = []
    big_node_caps = {}

    skipped = 0
    for idx, hed in enumerate(hyperedges):
        k = len(hed)
        if k <= args.threshold:
            # convert to clique rows
            for u in hed:
                cap_u = node_caps.get((u, idx), 1.0)
                # base_fee & fee_rate defaults (adjust if you need)
                base_fee = 100.0
                fee_rate = 1.0
                for v in hed:
                    if u == v: continue
                    small_rows.append({
                        "src": u, "trg": v, "capacity": cap_u,
                        "base_fee": base_fee, "fee_rate": fee_rate, "enabled": True
                    })
        else:
            # keep hyperedge and its node_caps
            big_hyperedges.append(hed)
            for u in hed:
                if (u, idx) in node_caps:
                    big_node_caps[(u, len(big_hyperedges)-1)] = node_caps[(u, idx)]
            skipped += 1

    # write small clique CSV if any
    small_csv = f"{args.out_prefix}_small_edges.csv"
    if small_rows:
        pd.DataFrame(small_rows).to_csv(small_csv, index=False)
        if args.verbose:
            print("Wrote small clique CSV:", small_csv, "rows:", len(small_rows))
    else:
        print("No small hyperedges to convert (all were > threshold).")

    # write big hyperjson if any
    big_hyperjson = f"{args.out_prefix}_big_hyper.json"
    if big_hyperedges:
        # serialize node_caps with new index mapping (big hyperedges 0..)
        node_caps_serial = {}
        for (n, idx), cap in big_node_caps.items():
            # idx now corresponds to position in big_hyperedges
            node_caps_serial[f"{n}|{idx}"] = cap
        j2 = {"hyperedges": [list(h) for h in big_hyperedges], "node_caps": node_caps_serial}
        json.dump(j2, open(big_hyperjson, "w"))
        if args.verbose:
            sizes = [len(h) for h in big_hyperedges]
            print("Wrote big hyperjson:", big_hyperjson, "big_count:", len(big_hyperedges), "max_size:", max(sizes))
    else:
        print("No big hyperedges; big hyperjson not written.")

    print("Summary: hyperedges_total=%d small_converted=%d big_skipped=%d" % (len(hyperedges), len(small_rows)>0 and len(set(tuple(r.items()) for r in small_rows)) or 0, skipped))

if __name__ == '__main__':
    main()
