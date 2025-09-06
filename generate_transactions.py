from lnsimulator.ln_utils import preprocess_json_file
import lnsimulator.simulator.transaction_simulator as ts
import pandas as pd


node_meta = pd.read_csv("LNTrafficSimulator/sample_data/1ml_meta_data_2022.csv")

providers = list(node_meta["pub_key"])


data_dir = "LNTrafficSimulator/sample_data/LN_data_2022.json"
directed_edges = preprocess_json_file(data_dir)



amount = 60000
count = 100000
epsilon = 0.8
drop_disabled = True
drop_low_cap = True
with_depletion = True

simulator = ts.TransactionSimulator(directed_edges, providers, amount, count, drop_disabled=drop_disabled, drop_low_cap=drop_low_cap, epsilon=epsilon, with_depletion=with_depletion)
transactions = simulator.transactions
src_dst = transactions[['transaction_id', 'source', 'target']]
src_dst.to_csv('100K_transactions.csv', index=False)