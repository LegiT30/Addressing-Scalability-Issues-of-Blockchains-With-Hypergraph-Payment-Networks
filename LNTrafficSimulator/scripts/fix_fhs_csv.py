#!/usr/bin/env python3
import pandas as pd, sys, os, time, random

infile = sys.argv[1] if len(sys.argv) > 1 else "runs/fhs_5_edges.csv"
outfile = sys.argv[2] if len(sys.argv) > 2 else infile.replace(".csv", "_fixed.csv")

df = pd.read_csv(infile)

# Map columns to LN schema
df_fixed = pd.DataFrame()
df_fixed["snapshot_id"] = 0  # all zero (can be changed per experiment)
df_fixed["src"] = df["src"]
df_fixed["trg"] = df["trg"]
df_fixed["last_update"] = int(time.time())  # fake timestamp
df_fixed["channel_id"] = [random.randint(10**14, 10**15-1) for _ in range(len(df))]  # random IDs
df_fixed["capacity"] = df["capacity"]

# Convert enabled/disabled
if "disabled" in df.columns:
    df_fixed["disabled"] = df["disabled"]
elif "enabled" in df.columns:
    df_fixed["disabled"] = ~df["enabled"].astype(bool)
else:
    df_fixed["disabled"] = False

# Fees
if "fee_base_msat" in df.columns:
    df_fixed["fee_base_msat"] = df["fee_base_msat"]
else:
    df_fixed["fee_base_msat"] = df.get("base_fee", 1000.0)

if "fee_rate_milli_msat" in df.columns:
    df_fixed["fee_rate_milli_msat"] = df["fee_rate_milli_msat"]
else:
    df_fixed["fee_rate_milli_msat"] = df.get("fee_rate", 1.0)

# Minimum HTLC (default 1000 msat if missing)
df_fixed["min_htlc"] = 1000.0

df_fixed.to_csv(outfile, index=False)
print(f"✅ Wrote fixed CSV: {outfile} with {len(df_fixed)} edges")
print("Columns:", list(df_fixed.columns))
