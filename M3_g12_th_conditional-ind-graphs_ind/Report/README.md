# Report

`M3_g12_th_conditional-ind-graphs_ind_Report.pdf` is the Milestone 3 report. The `.docx` next to it is the editable source, built by `Code/scripts/build_report.py`.

The figures of the report are in `Results/figures/report/`. The extra tables behind it (paired tests by group, precision and recall, treatment effect correlations,
real-data Welch tests, Fig 9 summary numbers) are in `Results/tables/report_extra/`. They are produced by `Code/scripts/report_extra_stats.py`, `report_real_stats.py` and `report_figures.py`.
The other figures in `Results/figures/` were drawn by the experiment scripts and are kept as they were exported.

## Which file supports which part of the paper

| Paper element | File in `Results/` |
|---|---|
| Fig 1, F1 of Inst., Lag and Temporal graph | `figures/fig_synth_main_orientation.png` (adjacency F1: `..._adjacency.png`), `tables/synth_summary_*.csv` |
| Fig 3, graph type | `figures/fig_synth_graphtype_*.png`, `tables/synth_factors_*.csv` |
| Fig 4, history-dependent noise | `figures/fig_synth_history_*.png` |
| Fig 5, instantaneous effects | `figures/fig_synth_inst_*.png` |
| Table 1, lag ablation | `tables/table1_lag_ablation.csv`, `tables/table1_lag_paired_tests.csv` |
| Fig 2, treatment effect RMSE | `figures/fig2_treatment_effect_rmse.png`, `tables/te_summary.csv` |
| Table 2, DREAM3 | `figures/fig_dream3_auroc.png`, `tables/real_dream3_auroc.csv` |
| Table 3, Netsim | `figures/fig_netsim_auroc.png`, `tables/real_netsim_auroc.csv` |
| Fig 8, AUROC, F1 and likelihood during training | `figures/fig8_netsim_*.png`, `tables/fig8_netsim_*.csv` |
| Paired tests, Rhino against each baseline | `tables/synth_paired_*.csv` |
| Run times | `tables/synth_runtime.csv` |
| Status, assumptions and problems | `STATUS.md` |
