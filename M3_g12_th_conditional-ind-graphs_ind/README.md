# Milestone 3: results and comparison with the base paper

Student: Het Patel (AU2440266), B.Tech CSE, Ahmedabad University.
Course: CSE 516, Probabilistic Graphical Models. Track: Theoretical AI. Group: `g12_th_conditional-ind-graphs_ind` (individual project).

Base paper: Gong, Jennings, Zhang and Pawlowski. *Rhino: Deep Causal Temporal Relationship Learning with History-dependent Noise.* ICLR 2023 (arXiv 2210.14706).
Goal of this milestone: reproduce the experiments of the paper with the authors' released code and report what was and what was not reproduced.

## Folder map

| Folder | Content |
|---|---|
| `Report/` | The Milestone 3 PDF report (and its editable `.docx`). `Report/README.md` maps each figure and table to the paper. |
| `Code/` | Scripts, model configs, job lists and the workstation guide. `Code/README.md` explains how to run everything. |
| `Data/` | How the data were generated or downloaded, preprocessing rules and checksums. The data itself is not stored. |
| `Results/` | Figures (`figures/`), tables (`tables/`), the raw per-job results (`raw/`) and `STATUS.md`. |

## What was run

- Synthetic data: the authors' generator, 5, 10 and 20 nodes, 40 datasets per dimension (graph type, instantaneous effects, history-dependent noise, 5 seeds).
  Methods: Rhino, Rhino+g, Rhino+s, DYNOTEARS, VAR-LiNGAM, PCMCI+.
- Lag ablation (paper Table 1) with lag 1, 2 and 3.
- Treatment effect error (paper Fig 2) from the trained models.
- DREAM3 (size 100, five networks) and Netsim (Sim-3), AUROC of the summary graph (paper Tables 2 and 3), and the AUROC, F1 and likelihood curves (paper Fig 8).
- Two training settings for Rhino on the real data: the hyperparameters printed in the paper and the configs released with the code. They differ in the number of augmented Lagrangian steps.

`Results/STATUS.md` states which parts are complete, which are partial, and what was not run.
All numbers below are produced by `Code/scripts/` from the job results. Nothing is typed in by hand.

## Main results at the time of export

### Synthetic data: temporal orientation F1 (mean +- s.d. over 40 datasets per dimension)

| method | 5 nodes | 10 nodes | 20 nodes |
|---|---|---|---|
| Rhino (L=2) | 0.67 +- 0.14 | 0.55 +- 0.14 | 0.44 +- 0.19 |
| Rhino+g (L=2) | 0.53 +- 0.11 | 0.46 +- 0.08 | 0.37 +- 0.06 |
| Rhino+s (L=2) | 0.35 +- 0.26 | 0.31 +- 0.22 | 0.20 +- 0.18 |
| DYNOTEARS | 0.47 +- 0.09 | 0.37 +- 0.10 | 0.31 +- 0.12 |
| VAR-LiNGAM | 0.04 +- 0.07 | 0.04 +- 0.06 | 0.03 +- 0.04 |
| PCMCI+ | 0.54 +- 0.13 | 0.48 +- 0.12 | 0.39 +- 0.12 |

### Netsim: AUROC of the summary graph (mean and standard error over runs)

| method | variant | n | mean | se | paper_value |
|---|---|---|---|---|---|
| cMLP | quoted from Khanna and Tan (2019) | 0 | 0.930 |  | 0.930 |
| cLSTM | quoted from Khanna and Tan (2019) | 0 | 0.830 |  | 0.830 |
| TCDF | quoted from Khanna and Tan (2019) | 0 | 0.910 |  | 0.910 |
| SRU | quoted from Khanna and Tan (2019) | 0 | 0.800 |  | 0.800 |
| eSRU | quoted from Khanna and Tan (2019) | 0 | 0.880 |  | 0.880 |
| DYNOTEARS | baseline | 1 | 0.896 |  | 0.900 |
| PCMCI+ | baseline | 1 | 0.830 |  | 0.830 |
| VAR-LiNGAM | baseline | 1 | 0.836 |  | 0.840 |
| Rhino+NoInst | paper | 5 | 0.912 | 0.009 | 0.930 |
| Rhino+NoInst | shipped | 5 | 0.857 | 0.008 | 0.930 |
| Rhino+g | paper | 5 | 0.972 | 0.004 | 0.974 |
| Rhino+g | shipped | 5 | 0.905 | 0.013 | 0.974 |
| Rhino | paper | 5 | 0.987 | 0.002 | 0.990 |
| Rhino | shipped | 5 | 0.931 | 0.013 | 0.990 |

Variant `paper` = hyperparameters printed in the paper. Variant `shipped` = config released with the code (different number of augmented Lagrangian steps). `quoted` rows are copied by the paper from Khanna and Tan (2019) and were not re-run. `paper_value` is the number printed in the paper.

### DREAM3 (size 100): AUROC of the summary graph (mean and standard error over runs)

| method | variant | ecoli1 | ecoli2 | yeast1 | yeast2 | yeast3 |
|---|---|---|---|---|---|---|
| DYNOTEARS | baseline | 0.569 | 0.547 | 0.523 | 0.530 | 0.507 |
| PCMCI+ | baseline | 0.540 | 0.532 | 0.522 | 0.505 | 0.515 |
| Rhino | paper | 0.657 +- 0.010 | 0.656 +- 0.012 | 0.634 +- 0.012 | 0.553 +- 0.000 | 0.554 +- 0.008 |
| Rhino+g | paper | 0.643 +- 0.006 | 0.645 +- 0.007 | 0.629 +- 0.006 | 0.585 +- 0.002 | 0.565 +- 0.004 |

Variant `paper` = hyperparameters printed in the paper. Variant `shipped` = config released with the code (different number of augmented Lagrangian steps). `quoted` rows are copied by the paper from Khanna and Tan (2019) and were not re-run. `paper_value` is the number printed in the paper.

## Reading the tables

- Synthetic F1: one row of data is one dataset. The mean is over the 40 datasets of a dimension. The paper does not say if its F1 is orientation or adjacency F1, so both are in `Results/tables/`.
- Paired tests compare Rhino with every other method on the same datasets (Wilcoxon signed-rank test with Holm correction). See `synth_paired_*.csv`.
- Real data: Rhino and Rhino+g are averaged over 5 runs with different model seeds. The paper reports the standard error, so the tables do the same.
  The 95 % interval in the CSV files uses the t distribution with 4 degrees of freedom.
- DYNOTEARS, PCMCI+ and VAR-LiNGAM are deterministic here, so they have one run each.

## Honest limits

- No result of 40 nodes. The paper has them. They were too expensive on the machine used here.
- The numbers of cMLP, cLSTM, TCDF, SRU and eSRU are the ones quoted by the paper. They were not re-run.
- DREAM3: Rhino on Ecoli 2 and Yeast 2, and Rhino+g on Yeast 2, have only 2 runs (seeds 2 and 3), not 5. The other cells have 5 runs. With 2 runs the standard error is not reliable. The exact n is in `Results/tables/real_dream3_auroc.csv`.
- DREAM3 with the released configs was not completed. Only the paper settings are reported for DREAM3.
- Differences from the paper that are not explained by the text are listed in `Results/STATUS.md` (assumptions and code problems).
