# Data, M4

No new data set is used in M4. The study re-uses the finished M3 runs. The raw data are not stored in this repository.

## Original data (see the M3 folder for details and checksums)

| Data | Source | Used for |
|---|---|---|
| Synthetic temporal data | Authors' generator, `causica.data_generation.temporal_synthetic` (causica v0.0.0, github.com/microsoft/causica/tree/v0.0.0). 5, 10, 20 nodes, ER or SF graphs, with or without instantaneous effects, with or without history-dependent noise, data seeds 0 to 4. 40 datasets per dimension. | 440 of the analysed runs |
| DREAM3 in silico, size 100 | http://gnw.sourceforge.net/resources/DREAM3%20in%20silico%20challenge.zip | 50 runs (Rhino, Rhino+g) |
| Netsim Sim-3 | https://github.com/sakhanna/SRU_for_GCI/tree/master/data/netsim | 10 runs (paper settings and released config) |

Preparation steps and SHA-256 checksums of the downloaded files are in `../../M3_g12_th_conditional-ind-graphs_ind/Data/`.

## Data produced for M4 (stored in `../Results`)

One small `.npz` file per finished M3 run, with the same fields in both folders:

| Field | Meaning |
|---|---|
| `probs` | Edge probabilities. Shape `[lag+1, N, N]` for synthetic data (slice 0 instantaneous), `[N, N]` for Netsim and DREAM3 (an edge exists if it exists at any lag). |
| `truth` | True graph, same shape and index convention as the official evaluation. |
| `mask` | 1 for edge entries that are evaluated (the instantaneous diagonal is excluded). |
| `n_samples` | 100 for `qG_export` (probabilities estimated from 100 sampled graphs). 1000000 for `qG_exact` (exact probabilities). |
| `logodds` | Only in `qG_exact`, synthetic runs. Exact log-odds, used to rank entries whose probability rounds to 1. |
| `meta` | JSON string: job id, method, dataset, dimension, graph type, instantaneous and history flags, seed. |

| Folder | Files | How it was made |
|---|---|---|
| `Results/qG_export` | 760 | `Code/src/export_qG.py` on the workstation, from `adj_matrices.npy` |
| `Results/qG_exact` | 760 | `Code/src/export_exact_q.py` on the workstation, from `model.pt` logits |

760 runs were exported (Rhino 120, Rhino+g 120, Rhino+s 120, Rhino released config 80, lag ablation 240, Netsim 30, DREAM3 50). The report analyses 500 of them (see the report, Appendix C).
The workstation reports `Results/m4_export_report.txt` and `Results/m4_exact_report.txt` list the counts per method.
