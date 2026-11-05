# Status of the results

Generated: 2026-11-05 08:15 (workstation clock).

Every table and figure in this folder is produced from the job results listed here. A row marked `no` is incomplete, so the matching table or figure is partial.

## Jobs finished per method

| method | finished_ok | finished_not_ok | total | complete |
|---|---|---|---|---|
| dream3_dynotears | 5 | 0 | 5 | yes |
| dream3_pcmci_plus | 5 | 0 | 5 | yes |
| dream3_rhino_g_paper | 22 | 3 | 25 | no |
| dream3_rhino_g_shipped | 0 | 0 | 25 | no |
| dream3_rhino_paper | 19 | 6 | 25 | no |
| dream3_rhino_shipped | 0 | 0 | 25 | no |
| dynotears | 120 | 0 | 120 | yes |
| netsim_dynotears | 1 | 0 | 1 | yes |
| netsim_pcmci_plus | 1 | 0 | 1 | yes |
| netsim_rhino_g_paper | 5 | 0 | 5 | yes |
| netsim_rhino_g_shipped | 5 | 0 | 5 | yes |
| netsim_rhino_noinst_paper | 5 | 0 | 5 | yes |
| netsim_rhino_noinst_shipped | 5 | 0 | 5 | yes |
| netsim_rhino_paper | 5 | 0 | 5 | yes |
| netsim_rhino_shipped | 5 | 0 | 5 | yes |
| netsim_varlingam | 1 | 0 | 1 | yes |
| pcmci_plus | 120 | 0 | 120 | yes |
| rhino | 120 | 0 | 120 | yes |
| rhino_g | 120 | 0 | 120 | yes |
| rhino_lag1 | 120 | 0 | 120 | yes |
| rhino_lag3 | 119 | 1 | 120 | no |
| rhino_s | 120 | 0 | 120 | yes |
| rhino_shipped | 80 | 0 | 80 | yes |
| varlingam | 120 | 0 | 120 | yes |


Treatment-effect evaluations finished (Fig 2): 360 of 360 planned.


## Not run

- Synthetic datasets with 40 nodes (too expensive on the available machine). Table 1, Fig 1 and Fig 2 therefore cover 5, 10 and 20 nodes only.
- The baselines cMLP, cLSTM, TCDF, SRU and eSRU. The paper quotes their numbers from Khanna and Tan (2019). They are quoted here too and not reproduced.
- DREAM3 with the released (shipped) configs: no run finished. About 12 of the 50 jobs were started and stopped at the compute cut-off. Their logs are in `failed_infra/stopped_20261104/`. Only the paper settings (Table 4) are reported for DREAM3.
- DREAM3 paper settings: Ecoli 2 Rhino, Yeast 2 Rhino and Yeast 2 Rhino+g have 2 seeds (seeds 2 and 3), not 5. Seeds 0 and 1 hit the 10 hour limit and seed 4 was not started. A mean over 2 seeds has a very wide interval.
- Lag ablation: one 20-node Lag-3 job (SF_SF, NoHistDep, seed 0) hit the 10 hour limit, so that cell has 39 of 40 datasets. The pairs for the tests use the available ones.
- VAR-LiNGAM without pruning (planned sensitivity check) was not run.


## Assumptions that are not stated in the paper

1. Synthetic grid: connection factor 2 and the same graph family for the instantaneous and lagged graph (40 datasets per dimension, 5 seeds each).
2. Netsim: subjects 2 to 6 mean the files `sim3_subject_2` to `sim3_subject_6` (names start at 0). Subjects 7 and 8 are the validation set.
3. DREAM3: the final fit uses an 80/20 split of the 46 series by series (seed 0), as in the paper's tuning split.
4. Netsim lag is 2. The DYNOTEARS training parameters on Netsim are the ones of Table 5.
5. F1 on synthetic data: the paper does not say if it is orientation or adjacency F1. Both are reported. Fig 8 of the paper uses orientation F1.
6. LL in Table 1 is the last logged training log p(x|A) of each run.


## Known problems in the released code and how they were handled

- `-te` crashes in the likelihood step (`Rhino.log_prob` gets a numpy array). The flag `-el` skips that step. The ATE RMSE does not need it.
- The final evaluation ignores the diagonal unless the flag `-ede` is given. Netsim counts self-connections, so it uses `-ede`.
- Five early jobs failed because two workers created an MLflow experiment at the same moment. They were run again. Their logs are in `failed_infra/`.


## Jobs that did not finish with status ok

| job_id | status |
|---|---|
| rhino_lag3__SF_SF_lag_2_dim_20_NoHistDep_0.5_mlp_spline_product_con_2_inthist_3_seed_0 | timeout |
| dream3_ecoli2_rhino_paper__s0 | timeout |
| dream3_ecoli2_rhino_paper__s1 | timeout |
| dream3_ecoli2_rhino_paper__s4 | not_run_budget |
| dream3_yeast2_rhino_g_paper__s0 | timeout |
| dream3_yeast2_rhino_g_paper__s1 | timeout |
| dream3_yeast2_rhino_g_paper__s4 | not_run_budget |
| dream3_yeast2_rhino_paper__s0 | timeout |
| dream3_yeast2_rhino_paper__s1 | timeout |
| dream3_yeast2_rhino_paper__s4 | not_run_budget |
