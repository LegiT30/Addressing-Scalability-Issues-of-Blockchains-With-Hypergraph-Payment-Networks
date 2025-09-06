
# Addressing Scalability Issues of Blockchains With Hypergraph Payment Networks

This repository contains the data and scripts used in the paper (1)**"Improving Blockchain Scalability with Hypergraph Payment Networks"** and adds an extra layer for simulating the research work of (2)**"Addressing Scalability Issues of Blockchains With Hypergraph Payment Networks"**.
In addition to the the transaction used in the paper (1), there is the generate_transactions.py file that allows you to create realistice LN transactions based on the LN topology.
The transaction simulator is based on [LNTrafficSimulator] (https://github.com/ferencberes/LNTrafficSimulator), created by Ferenc et al.

## Repository Contents

- **`Lightning_2022_10k_transactions.csv`**: The generated transaction dataset used in the paper.
- **`1ml_2022_merchants_in_topology.txt`**: The merchant list used to generate transactions.
- **`LN_data_2022.zip`**: The Lightning Network topology data.
- **`LNTrafficSimulator`**: The LNTrafficSimulator directory.
- **`generate_transactions.py`**: A transcation generator file.


## Requirements

- Python3

## Usage

To replicate our results: Kindly go through the Readme file inside the LNTrafficSimulator directory.

