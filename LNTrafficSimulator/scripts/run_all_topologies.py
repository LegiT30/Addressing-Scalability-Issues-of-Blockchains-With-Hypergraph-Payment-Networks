# scripts/run_all_topologies.py
import subprocess, os, json
from topologies.utils import edges_df_to_nx, create_lnrollup_hyperedges, create_supernode_hyperedges
from topologies.nch import create_nch
from topologies.fhs import create_fhs
import pandas as pd

DATA_DIR = "../ln_data"
BASE_EDGES_CSV = f"{DATA_DIR}/ln_edges.csv"  # or path to original edges DataFrame

def load_edges_df():
    return pd.read_csv(BASE_EDGES_CSV)

def export_and_run(hyperedges, node_caps, out_prefix, params_file):
    # write hyperjson
    j = {'hyperedges':[list(h) for h in hyperedges], 'node_caps': {f"{n}|{i}":cap for (n,i),cap in node_caps.items()}}
    hyperjson = f"{out_prefix}_hyper.json"
    json.dump(j, open(hyperjson,"w"))
    edges_csv = f"{out_prefix}_edges.csv"
    subprocess.check_call(["python", "scripts/hyper_to_edges.py", "--hyperjson", hyperjson, "--out", edges_csv])
    # run simulator in preprocessed mode: snapshot id not used — modify run_simulator to accept edges file directly or use 'raw' mode with json.
    outdir = f"{out_prefix}_results"
    subprocess.check_call(["python", "run_simulator.py", "preprocessed", "0", params_file, outdir])

if __name__ == "__main__":
    edges_df = load_edges_df()
    G = edges_df_to_nx(edges_df)
    # LNrollup
    hln, nt_hln, caps_hln = create_lnrollup_hyperedges(G)
    export_and_run(hln, caps_hln, "runs/lnrollup", "params.json")
    # Supernode
    hsn, nt_sn, caps_sn = create_supernode_hyperedges(G)
    export_and_run(hsn, caps_sn, "runs/supernode", "params.json")
    # NCH
    hnch, nt_nch, caps_nch = create_nch(G)
    export_and_run(hnch, caps_nch, "runs/nch", "params.json")
    # FHS variants
    for m in [3,5,20,5000]:
        hfhs, nt_fhs, caps_fhs = create_fhs(G, m)
        export_and_run(hfhs, caps_fhs, f"runs/fhs_{m}", "params.json")
