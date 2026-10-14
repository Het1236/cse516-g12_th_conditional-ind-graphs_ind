# Data: M2

There is nothing to download. All data is synthetic. It is made by `Code/src/data.py` and, for the paper's setting, by the authors' own generator through `Code/src/official.py`.

## How a dataset is made

This follows Section 7.1 of the uGLAD paper and the authors' code (`get_data` in their repository, with the paper's settings).

1. Pick the number of variables D = 25.
2. For every pair of variables put an edge with probability p = 0.1. This is an Erdős-Rényi random graph.
3. Draw a full matrix W of independent values from U(−1, 1). Keep the entries that sit on edges.
4. Average that matrix with its transpose. Each edge value is then the mean of two uniform draws.
5. Add a multiple of the identity so that the smallest eigenvalue is 1. This is the true precision matrix.
6. Draw M samples from a Gaussian with mean 0 and covariance equal to the inverse of that matrix.

## What I generate

| Item | Value |
|---|---|
| Variables D | 25 |
| Edge probability p | 0.1 (about 30 true edges out of 300 pairs) |
| Training samples M | 10, 25, 50 |
| Graphs per M | 20 (index k = 0 to 19) |
| Test samples | 1000 per graph, never used for training |
| Seed for graph k | 2026 + k |

The same seed gives the same data on any machine. The 60 datasets and every matrix that was learned on them are saved in `../Results/reproduction/table1_author_generator/matrices/`. Each file `M<m>_g<k>.npz` holds the samples `x`, the true precision matrix `theta_true`, and the estimates `prec_SGLCV` and `prec_uGLAD`. The estimate of my own implementation is in `mine_matrices/`.

## Real data

I have not used a real dataset in M2.
