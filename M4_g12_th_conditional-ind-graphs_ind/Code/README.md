# Code, M4

Everything needed to regenerate every table, figure and number of the M4 report from the exported edge probabilities.
No model is trained in M4. The Rhino models come from M3 (`../../M3_g12_th_conditional-ind-graphs_ind`).

## Folder map

| Path | What it is |
|---|---|
| `src/export_qG.py` | Runs on the workstation. Estimates each edge probability from the 100 graphs that Rhino saves per run (`adj_matrices.npy`) and pairs it with the true graph. |
| `src/export_exact_q.py` | Runs on the workstation. Computes the exact edge probabilities from the logits in the saved `model.pt` (numpy and `torch.load` only). Checks them against the 100-sample mean. |
| `src/calib_fdr.py` | The analysis: calibration (Brier, log-loss, ECE), temperature scaling, Bayesian FDR selection, the learned cutoff, paired tests. |
| `src/summary_tables.py` | Consolidated tables and figures across the Rhino variants and data sets. |
| `src/run_all_analysis.py` | Runs the analysis for every variant and data set, then the summary. |
| `src/make_model_figure.py` | Draws Fig. 1 of the report. |
| `src/build_report.py`, `src/latex_lib.py` | Build the report as LaTeX in the layout of an ICLR paper and compile it with pdflatex. All numbers are read from `Results/tables`. (`src/report_lib.py` is the older Word backend, also used by `build_slides.py` for the speaker notes.) |
| `src/make_slide_figures.py` (logo in `src/assets`) | Figures for the slides: numbers typed from the Rhino paper (Tables 1 to 3) and three schematics. No project result. |
| `src/build_slides.py` | Builds the 30 slides (pptx), the speaker notes (docx) and their PDFs. Set `M4_PRES_OUT` to write somewhere else. |
| `src/tests/test_calib_fdr.py` | Code tests on **simulated** probabilities. Not results. |
| `workstation/` | The kit that was run on the lab workstation (see below). |
| `requirements.txt` | Package versions of the analysis environment. |

## Environment

Windows 11, Python 3.14.2. `pip install -r requirements.txt`. The report needs `pdflatex` (MiKTeX 25.12 was used; no extra package such as natbib is needed). The slides and speaker notes need Microsoft PowerPoint and Word for the PDF conversion.
The M3 runs used Python 3.9, torch 1.12.1 (CPU), causica v0.0.0 on the lab workstation. The M3 environment recipe is in the M3 folder.

## Reproduce the numbers (about 5 minutes)

```bash
cd Code/src
python tests/test_calib_fdr.py          # 6 code tests on simulated data
python run_all_analysis.py --exact      # exact probabilities  (Results/qG_exact)  -> *_exact tables and figures (main results)
python run_all_analysis.py              # sampled probabilities (Results/qG_export) -> tables and figures without suffix (robustness)
python make_model_figure.py
python build_report.py                  # Report/*.docx   (then convert to PDF with Word)
python make_slide_figures.py
python build_slides.py --pdf            # Presentation/*.pptx, speaker notes, PDFs
```

Seeds: the grouped 5-fold split uses `numpy.random.default_rng(0)`. The bootstrap of the pooled ECE uses seed 0 and 1000 resamples.
Nothing else is random. The analysis is deterministic given the exported files.

## How the exported files were made (workstation)

1. Put `workstation/run_m4_export.ps1`, `workstation/run_m4_exact.ps1`, `src/export_qG.py` and `src/export_exact_q.py` in one folder on the workstation.
2. `run_m4_export.ps1 -Root <M3 folder with results\ and runs\>` writes `M4_qG_export_return.zip` and `m4_export_report.txt`.
3. `run_m4_exact.ps1 -Root <same>` writes `M4_qG_exact_return.zip` and `m4_exact_report.txt`.
4. The returned files were unzipped into `Results/qG_export`, `Results/qG_exact`. The two reports are in `Results/`.

The scripts only read M3 output (`results\`, `runs\`, `causica\data`). They train nothing and change nothing.
No GPU was used anywhere in M4.

## Method in three lines

- Probability of each edge entry: exact softmax of the saved logits (`export_exact_q.py`, Appendix B of the report).
- Bayesian FDR: sort by p, keep the largest top-k with mean(1 - p) <= alpha (`calib_fdr.bfdr_select`).
- Calibration: temperature `p' = sigmoid(logit(p)/tau)` and a log-odds cutoff learned on other datasets (`calib_fdr.fit_tau`, `calib_fdr.cutoff_for_alpha`).

## Known limits of the code

- The cutoff rule has no finite-sample guarantee (report, Section 15).
- Datasets with a 3-D truth (synthetic) and a 2-D truth (Netsim, DREAM3) are handled as in the official evaluation: for 2-D truth an edge exists if it exists at any lag.
- `export_exact_q.py` relies on the logit layout of causica v0.0.0 (`var_dist_A.logits`, `var_dist_A.logits_lag`). The check against the sampled graphs
  (mean absolute difference 0.0067, largest single difference 0.206) is printed in `Results/m4_exact_report.txt`.
