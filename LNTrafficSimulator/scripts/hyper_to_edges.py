# scripts/hyper_to_edges.py
import json, pandas as pd, argparse
from topologies import nch, fhs, supernodes, utils

def hyperedges_to_directed_edges_df(hyperedges, node_capacity_map, base_fee=100, fee_rate=1):
    rows = []
    for idx, hed in enumerate(hyperedges):
        for u in hed:
            cap = node_capacity_map.get((u, idx), node_capacity_map.get(u, 1.0))
            for v in hed:
                if u == v: continue
                rows.append({'src':u,'trg':v,'capacity':cap,'base_fee':base_fee,'fee_rate':fee_rate,'enabled':True})
    return pd.DataFrame(rows)

# CLI to load hyperedges JSON and export edges CSV
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hyperjson", required=True)  # json with keys: hyperedges(list of lists), node_caps dict (tuple strings)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    j = json.load(open(args.hyperjson))
    hyperedges = [set(h) for h in j['hyperedges']]
    node_caps = {}
    for k,v in j.get('node_caps', {}).items():
        # keys might be "node|idx" -> parse
        node, idx = k.split("|")
        node_caps[(node, int(idx))] = v
    df = hyperedges_to_directed_edges_df(hyperedges, node_caps)
    df.to_csv(args.out, index=False)
