# Code

The experiments use the authors' released code: `microsoft/causica`, tag `v0.0.0` (commit `b3c79a0`). It is **not** included here and it was **not edited**.
To get it:

```
git clone https://github.com/microsoft/causica.git causica
cd causica
git checkout v0.0.0
```

Everything in this folder wraps that code. It was run on Windows 11, Python 3.9, CPU only (torch 1.12.1+cpu), up to 16 parallel workers with 2 threads each.
`environment/pip_freeze.txt` lists the exact package versions.

## Layout

| Path | Content |
|---|---|
| `scripts/` | All scripts written for this project (see below). |
| `configs/` | Model configs. `rhino*.json` for synthetic data, `real/` for DREAM3 and Netsim. |
| `jobs/` | The job lists that were run (`jobs.csv`: 720 synthetic jobs, `jobs_queue.csv`: real data, lag ablation and extra runs). |

## Order to reproduce

Run from the folder that contains `causica/` and `scripts/`.

```
powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1 -EnvDir rhino_env
python scripts\make_configs.py
python scripts\make_manifest.py --dims 5 10 20 --seeds 0 1 2 3 4 --out jobs.csv
python scripts\gen_datasets.py --jobs jobs.csv --procs 6
python scripts\prep_real_data.py                  # after downloading DREAM3 and Netsim (see Data/README.md)
python scripts\make_real_configs.py
python scripts\make_real_manifest.py --out jobs_real.csv
python scripts\make_manifest.py --dims 5 10 20 --methods rhino_lag1 rhino_lag3 --out jobs_lag.csv
python scripts\make_manifest.py --dims 5 10 --methods rhino_shipped --out jobs_shipped_synth.csv
python scripts\make_queue.py
powershell -File scripts\run_full.ps1 -Jobs jobs_queue.csv -Workers 12 -Threads 2 -TimeoutHours 10
python scripts\cate_worker.py --threads 2         # treatment effects, can run beside the workers
python scripts\analyze_synth.py                   # tables and figures of the synthetic experiments
python scripts\analyze_real.py                    # tables and figures of DREAM3 and Netsim
python scripts\analyze_extra.py                   # lag ablation, treatment effect and extra tables
python scripts\report_extra_stats.py              # extra statistics used in the report
python scripts\report_real_stats.py
python scripts\report_figures.py
python scripts\build_report.py                    # writes Report/*.docx
```

Workers claim jobs with lock files, so more workers can be started at any time. A finished job is never repeated.

## Scripts

| Script | Purpose |
|---|---|
| `setup_env.ps1` | Builds the Python environment from the pinned versions. |
| `make_configs.py`, `make_real_configs.py` | Write the model configs for synthetic and real data. |
| `make_manifest.py`, `make_real_manifest.py`, `make_queue.py` | Build the job lists. |
| `gen_datasets.py`, `gen_one.py` | Generate the synthetic datasets with the authors' generator. |
| `prep_real_data.py` | Convert DREAM3 and Netsim into the format of the code. |
| `worker.py`, `launch_workers.ps1`, `run_full.ps1` | Run the jobs in parallel. |
| `cate_worker.py` | Treatment effect evaluation on the trained models (paper Fig 2). |
| `collect.py`, `watch.py` | Collect results and show live progress. |
| `analyze_synth.py`, `analyze_real.py`, `analyze_extra.py` | Statistics, tables and figures. |
| `adopt.py` | Finishes long DREAM3 jobs whose training outlived the 10 hour worker limit. |
| `report_extra_stats.py`, `report_real_stats.py`, `report_figures.py`, `build_report.py` | Extra statistics, figures and the report document. |

## Things that were found while building this

The same list is in `Results/STATUS.md`. In short: the Netsim ground truth must be transposed (`Gref[i,j] = 1` means j causes i), the final evaluation needs the flag `-ede`
to count self-connections, `-te` needs `-el` to avoid a crash in the released code, and each job uses its own MLflow folder to avoid a race between workers.
