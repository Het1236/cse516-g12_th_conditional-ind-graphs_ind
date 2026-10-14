# Code: M2 implementation

Everything here is written in Python. It builds a Gaussian graphical model, learns its graph with uGLAD and with a baseline, and answers inference queries. All experiments are seeded.

## Environment

| Item | Value used |
|---|---|
| OS | Windows 11 |
| Python | 3.14.2 |
| Hardware | CPU only, no GPU needed (Intel i5-10300H, 7.8 GB RAM) |
| Packages | exact versions in `requirements.txt` |

Setup:

```bash
python -m venv .venv
source .venv/Scripts/activate        # on Linux or Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Files in `src/`

| File | What it does |
|---|---|
| `data.py` | Synthetic data. `make_dataset(..., generator="authors")` follows the authors' own generator (weights averaged with their transpose). The older `"symmetric"` generator is kept so earlier results can be repeated. |
| `ggm.py` | The graphical model as a class: variables, edges, factors, partial correlation, marginal and conditional queries. |
| `uglad_model.py` | My PyTorch version of uGLAD: unrolled network, custom square root layer, training with 3-fold CV. Also the classical alternating minimization used for checking. |
| `baselines.py` | Graphical lasso (block coordinate descent), and PC, GES and hill climbing with their conversion to undirected graphs. Only graphical lasso is benchmarked in M2. |
| `metrics.py` | SHD, precision, recall, F1, AUC, AUPR, held-out likelihood, conditional prediction error. |
| `validate.py` | The mathematical checks V1 to V8 (23 checks). Writes `Results/validation/`. |
| `demo.py` | One small end-to-end run for the video. |
| `official.py` | Wrapper around the authors' public uGLAD code, and the authors' data generator. |
| `reproduce_table1.py` | Runs the paper's Table 1 setting with the authors' code and graphical lasso. Saves every matrix. |
| `run_mine_on_saved.py` | Runs my implementation on the datasets that `reproduce_table1.py` saved. |
| `compute_kpis.py` | Held-out likelihood and conditional prediction error from the saved matrices. |
| `analyze_reproduction.py` | Comparison with the paper's numbers and the paired tests. |
| `make_m2_figures.py` | The six figures of the report and the slides, and the numbers behind their captions. |
| `plot_saved.py` | Make graph pictures or box plots from the saved results at any time. |
| `monitor_progress.py` | A live progress bar with time left. Run it in a separate terminal. |
| `run_reproduction_queue.sh` | The exact command used for the reproduction run. |

## Run commands

Run every command from `Code/src/`.

Quick demo (D = 25, M = 50, the same setting as the experiments):

```bash
python demo.py
```

Mathematical checks (23 checks):

```bash
python validate.py --out ../../Results/validation
```

## Reproducing Table 1 of the uGLAD paper

This needs the authors' code. Clone it once and point `UGLAD_OFFICIAL_PATH` at it. It needs Python 3.13 or newer.

```bash
git clone https://github.com/Harshs27/uGLAD
export UGLAD_OFFICIAL_PATH=/path/to/uGLAD
```

Then run these in order:

```bash
python reproduce_table1.py --out ../../Results/reproduction/table1_author_generator/table1_raw.csv --workers 2 --graphs 20 --sizes 10 25 50 --epochs 250 --generator author --matrix_dir ../../Results/reproduction/table1_author_generator/matrices --progress ../../Results/reproduction/table1_author_generator/progress.json
python run_mine_on_saved.py --folder ../../Results/reproduction/table1_author_generator --workers 3
python compute_kpis.py --folder ../../Results/reproduction/table1_author_generator
python analyze_reproduction.py --results ../../Results/reproduction/table1_author_generator
python make_m2_figures.py
```

In a second terminal you can watch the first command:

```bash
python monitor_progress.py ../../Results/reproduction/table1_author_generator/progress.json
```

A stopped run starts again where it stopped, because finished datasets are skipped.

How long it takes on my laptop: one uGLAD fit of the authors' code takes about 85 to 95 seconds on one CPU core, and extra threads do not help, so use several processes. The 60 datasets took about 50 minutes with 2 workers. My implementation took about 12 minutes on the same 60 datasets with 3 workers. Use 3 workers or fewer on a laptop with 8 GB of RAM.

## Seeds

| What | Seed |
|---|---|
| Graph and data number k | 2026 + k (k = 0 to 19), set for both Python's and numpy's random generators |
| Test data (1000 samples) | 2026 + k + 1,000,000 |
| uGLAD network start | 2026 + k |

## What is not in M2

The multi-method runner, the PC, GES and hill climbing experiments, the training-length study and the 1000-epoch runs are planned for M3. They are kept outside this folder until then.
