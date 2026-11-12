# Results, M4

Every table and figure here is written by `Code/src/run_all_analysis.py` (and `summary_tables.py`, `make_model_figure.py`).
Files with the suffix `_exact` use the exact edge probabilities (main results). Files without a suffix use the probabilities estimated from 100 sampled graphs (robustness check).

## Folders

| Folder | Content |
|---|---|
| `tables/` | CSV tables, one set per tag |
| `figures/` | PNG figures, one set per tag, plus the summary figures |
| `qG_exact/` | 760 `.npz` files, exact edge probabilities and true graphs (input of the analysis) |
| `qG_export/` | 760 `.npz` files, probabilities estimated from 100 sampled graphs |
| `m4_export_report.txt`, `m4_exact_report.txt` | Reports printed on the workstation (counts per method, exact-versus-sampled check) |

## Tags

Rhino synthetic: `synth_rhino`, `synth_rhino_g`, `synth_rhino_s`, `synth_rhino_shipped` (paper settings, Rhino+g, Rhino+s, released config).
Real data (calibration fitted on the synthetic Rhino runs): `shift_netsim_rhino_paper`, `shift_netsim_rhino_shipped`, `shift_dream3_rhino_paper`, `shift_dream3_rhino_g_paper`.

## Tables per tag (`<tag>` or `<tag>_exact`)

| File | Content |
|---|---|
| `table_probability_quality_<tag>.csv` | Pooled ECE with bootstrap 95% CI, pooled Brier and log-loss, per-dataset mean, SD and 95% CI of Brier, log-loss, AUROC, AUPRC. Rows: raw, temperature. |
| `table_fdr_control_<tag>.csv` | For each budget alpha and rule (raw, temperature, cutoff_pooled, cutoff_same_dim): promised error, realised FDP (mean, SD, 95% CI), power, F1, share of empty selections, mean number of selected edges. |
| `table_graph_rules_<tag>.csv` | F1 of the 0.5 threshold, the expected-F1 rule and the oracle threshold. |
| `table_paired_tests_<tag>.csv` | Paired mean differences with 95% CI, wins and losses, Wilcoxon p and Holm-corrected p (raw against temperature). |
| `per_dataset_<tag>.csv`, `per_dataset_fdr_<tag>.csv` | One row per dataset and rule. The basis of every table above. |

Summary tables: `table_summary_all(_exact).csv` (all variants and data sets, saturation, ECE, realised FDP and power), `table_breakdown_rhino(_exact).csv` (dimension times history-dependent noise).

## Where each report item comes from

| Report item | File |
|---|---|
| Table 4 | `table_probability_quality_synth_rhino_exact.csv` |
| Table 5 | `table_breakdown_rhino_exact.csv` |
| Table 6, Fig. 3 | `table_fdr_control_synth_rhino_exact.csv`, `fig_fdr_control_synth_rhino_exact.png` |
| Table 7 | `table_summary_all_exact.csv`, `per_dataset_synth_*_exact.csv`, `table_fdr_control_synth_*_exact.csv` |
| Table 8 | `table_summary_all_exact.csv`, `table_fdr_control_shift_*_exact.csv` |
| Table 9 | `table_paired_tests_synth_rhino_exact.csv` and the paired tests of the selection rules computed in `build_report.py` from `per_dataset_fdr_synth_rhino_exact.csv` |
| Table A1 | the same tables without and with the suffix `_exact` |
| Fig. 1 | `figures/fig_model.png` |
| Fig. 2 | `figures/fig_reliability_synth_rhino_exact.png` |
| Other figures | `fig_fdr_control_all_methods(_exact).png`, `fig_false_certainty(_exact).png`, `fig_brier_and_tau_<tag>.png` |

## Headline numbers (exact probabilities, 120 synthetic Rhino datasets, mean and 95% CI over datasets)

- 9.4% of the edge entries have p above 0.999, and 23.3% of those are not edges. 46.1% have p below 0.001, and 17.6% of those are true edges.
- Budget 0.01: promised 0.004, realised FDP 0.306 [0.277, 0.335].
- Temperature scaling (tau 5.23): pooled ECE 0.200 to 0.039, log-loss 1.39 to 0.51. At budget 0.2 the realised FDP is 0.314 against 0.195 promised.
- Learned cutoff (pooled): realised FDP 0.062, 0.244, 0.311 at budgets 0.1, 0.2, 0.3, with power 0.026, 0.369, 0.499.
- DREAM3: 85.9% of the edges selected at budget 0.1 are wrong.

The values in the CSV files are the reference. If a number in this README and a CSV differ, the CSV is right.
