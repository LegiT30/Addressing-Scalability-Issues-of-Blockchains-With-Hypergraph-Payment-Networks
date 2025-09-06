
# Improving Blockchain Scalability with Hypergraph Payment Networks

This repository contains the data and scripts used in the paper **"Improving Blockchain Scalability with Hypergraph Payment Networks"**.
In addition to the the transaction used in the paper, we add the generate_transactions.py file the allows you to create realistice LN transactions based on the LN topology.
The transaction simulator is based on [LNTrafficSimulator] (https://github.com/ferencberes/LNTrafficSimulator), created by Ferenc et al.

## Repository Contents

- **`Lightning_2022_10k_transactions.csv`**: The generated transaction dataset used in the paper.
- **`1ml_2022_merchants_in_topology.txt`**: The merchant list used to generate transactions.
- **`LN_data_2022.zip`**: The Lightning Network topology data.
- **`LNTrafficSimulator`**: The LNTrafficSimulator directory.
- **`generate_transactions.py`**: A transcation generator file.

## Overview

This project aims to improve blockchain scalability by utilizing hypergraph payment networks. By leveraging the Lightning Network (LN), we demonstrate enhanced transaction throughput and reduced latency in payment processing.

To achieve this, we use the LN transaction generator from LNTrafficSimulator. Our analysis identified 302 merchant nodes present in our Lightning data.

## Methodology

- **Transaction Sampling**: 
  - 80% of payment target nodes are sampled using a biased distribution skewed towards merchants, with the probability proportional to their degree of importance. This approach reflects the flow of payments towards service providers.
  - Payment sources and the remaining 20% of target nodes are sampled uniformly at random for simulation purposes.

- **Payment Values**:
  - As off-chain networks primarily facilitate micropayments, the traffic traces use a fixed payment value of 60,000 SAT, approximately 10 USD as of December 2022.

## Requirements

- Python3

## Usage

To replicate our results or conduct your own analysis, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Improving-Blockchain-Scalability-with-Hypergraph-Payment-Networks.git
   cd Improving-Blockchain-Scalability-with-Hypergraph-Payment-Networks
   ```

2. Install necessary dependencies:
   ```bash
   python3 LNTrafficSimulator-master/setup.py
   ```
   
3. Extract 'LN_data_2022.zip' into 'LNTrafficSimulator/sample_data/'

4. In the 'generate_transactions.py' file, set the 'amount' and 'count' variables to set the transaction size and number of transactions, respectively.

5. Run the simulation:
   ```bash
   python3 generate_transactions.py
   ```

## Citation

If you find this work useful, please consider citing the following authors in your research:

- **Arad Kotzer**
- **Bence Ladoczki**
- **János Tapolcai**
- **Ori Rottenstreich**

```plaintext
@misc{Kotzer2024,
  author = {Arad Kotzer, Bence Ladoczki, János Tapolcai and Ori Rottenstreich},
  title = {Improving Blockchain Scalability with Hypergraph Payment Networks},
  year = {2024}
}
```

## Contact

For questions or further information, please contact:

- Name: Arad Kotzer
- Email: aradk@campus.technion.ac.il
- Institution: Technion
