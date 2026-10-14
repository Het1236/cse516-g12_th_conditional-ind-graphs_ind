# Results: M2

All numbers here come from the code in `../Code/`. Nothing is typed in by hand.

## Folders

| Folder | What it holds |
|---|---|
| `reproduction/table1_author_generator/` | The main experiment: the paper's Table 1 setting run with the authors' code, graphical lasso and my implementation. |
| `m2_figures/` | The six figures of the report and the slides (PDF and PNG), `captions.json` and `numbers.json` with every number used in a caption. |
| `validation/` | The 23 mathematical checks. `validation_report.md` is the readable version. Also the query time table. |
| `reproduction/VERIFICATION.md` | The audit of my setup against the authors' code, and what I fixed. |
| `reproduction/generator_audit.csv` | The numbers behind that audit. |
| `demo/` | The figure made by `demo.py`. One small run for the video, not a result. |

## Files in `reproduction/table1_author_generator/`

| File | Content |
|---|---|
| `table1_raw.csv` | One row per method and dataset for graphical lasso (SGLCV) and the authors' uGLAD: AUPR, AUC, predicted edges, seconds. |
| `mine_raw.csv` | The same for my implementation. |
| `kpis_raw.csv`, `kpis_summary.csv`, `kpis_summary.md` | Held-out likelihood and conditional prediction error. |
| `table1_comparison.md`, `table1_comparison.csv`, `table1_paired.csv` | The paper's numbers against mine, and the paired tests. |
| `matrices/`, `mine_matrices/` | Samples, true matrix and every learned matrix of every dataset. |
| `fig_table1_reproduction.png`, `boxplot_aupr_auc.png` | Quick plots made from the saved results. |

## Setting

D = 25 variables, edge probability 0.1, M = 10, 25, 50, 20 graphs for each M, the authors' data generator, uGLAD at the code defaults (250 epochs, learning rate 0.002, 3 folds). Every cell in a table is a mean and a standard deviation over the 20 graphs.

## Main findings so far

1. The baseline is reproduced: SGLCV agrees with the paper within one standard deviation.
2. uGLAD at its code defaults ties SGLCV at M = 10 and is behind it at M = 25 and 50. It returns an empty graph on about half of the graphs at M = 25 and 50.
3. My implementation and the authors' code agree on all 60 datasets (AUPR correlation 1.00).
4. The prediction error of the conditional mean is close to the true model for every method, so it cannot tell a good graph from a poor one. The held-out likelihood can.

These are preliminary results with 20 graphs and the default training settings. The report gives the limits.

## Reproduce

See `../Code/README.md`.
