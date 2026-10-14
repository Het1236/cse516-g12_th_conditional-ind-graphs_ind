# Is my reproduction set up the way the authors do it?

This file lists each choice in my reproduction and what the authors' code or paper does. I read the repository (github.com/Harshs27/uGLAD, version 2.0.0) and the paper text for this.

## Checklist

| # | Choice | What the authors do | What I do | Status |
|---|---|---|---|---|
| 1 | Model call | `uGLAD_GL().fit(X, mode="cv", ...)` in `main.py` | Same call, through `official.py` | Same |
| 2 | Settings | Defaults: epochs 250, learning rate 0.002, L = 15, 3 folds, `INIT_DIAG` 0, `eval_offset` 0.1 | Same defaults | Same |
| 3 | Input scaling | `fit()` calls `process_table(..., NORM="min_max")` itself. It also drops constant and duplicate columns. | I pass raw data and let `fit()` scale it. No column is dropped for this data. | Same |
| 4 | Baseline | `GraphicalLassoCV().fit(X)` on raw data in the demo notebook | Same, default settings (5 folds) | Same |
| 5 | AUC and AUPR | `report_metrics_all`: `roc_curve` + `auc`, and `average_precision_score`, on the absolute value of the upper triangle of the estimated precision matrix | `metrics.score_metrics`: `roc_auc_score` and `average_precision_score` on the same entries | Same |
| 6 | Data generator | `get_data`: random matrix with entries U(w_min, w_max), multiplied by the graph, **then averaged with its transpose**, identity added, shifted to smallest eigenvalue `eig_offset` | **First run:** my own generator with one symmetric U(−1, 1) draw per edge and no averaging. **Now:** the authors' `get_data` with w_min = −1, w_max = 1, eig_offset = 1, p = 0.1 (the paper's settings) | **Was different, fixed** |
| 7 | Seeds | `get_data` uses an unseeded graph, so every call differs | I seed Python's and numpy's generators with 2026 + graph index | Needed for repeatability |
| 8 | Graphs per size | 20 test graphs | 20 | Same |

## The one real difference: the data generator

The authors average the weight matrix with its transpose. The average of two U(−1, 1) numbers is smaller in size than one U(−1, 1) number, so the edges are weaker and the problem is harder. I measured this over 20 graphs (`generator_audit.csv`):

| | My generator | Authors' generator |
|---|---|---|
| Mean size of an edge value | 0.449 | 0.327 |
| Mean size of a true partial correlation | 0.171 | 0.145 |
| Mean number of true edges | 29.6 | 30.5 |

The effect on the baseline (SGLCV, default settings, mean AUPR over 20 graphs):

| M | Paper | My generator | Authors' generator |
|---|---|---|---|
| 10 | 0.112 | 0.145 | **0.123** |
| 25 | 0.132 | 0.205 | **0.153** |
| 50 | 0.219 | 0.360 | **0.240** |

And mean AUC:

| M | Paper | My generator | Authors' generator |
|---|---|---|---|
| 10 | 0.505 | 0.542 | **0.518** |
| 25 | 0.532 | 0.584 | **0.540** |
| 50 | 0.617 | 0.670 | **0.604** |

With the authors' generator the baseline numbers move close to the paper's. So my first reproduction (my generator) made the problem too easy for graphical lasso. It is not used in M2 and its files are kept outside this folder for M3. The run in `table1_author_generator/` uses the authors' generator and replaces it.

The paper's text says "entries U(−1, 1), then a multiple of the identity is added so the smallest eigenvalue is 1". The authors' code does this and also averages with the transpose. The text does not mention the averaging, which is why I missed it.

## Things I could not verify

- The paper gives a learning rate range of 0.0001 to 0.001 but the code default is 0.002. The paper does not state the number of epochs. I use the code defaults. Other training settings are planned for M3.
- The paper does not say how many CV folds uGLAD used. The code default is 3. The demo notebook uses 5.
- The paper does not state the fold count for SGLCV. I use scikit-learn's default of 5.
