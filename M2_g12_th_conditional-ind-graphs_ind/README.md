# M2 - g12_th_conditional-ind-graphs_ind

**Course:** CSE 516 - Probabilistic Graphical Models
**Milestone:** M2 - Technical Foundation
**Student:** Het Patel (AU2440266)
**Track:** Theoretical AI (Individual research)
**Submission date:** 15 October 2026

## Project

This project studies conditional independence graph recovery with uGLAD, a model from Microsoft Research that unrolls the graphical lasso into a small neural network. The base paper is:

> H. Shrivastava, U. Chajewska, R. Abraham, and X. Chen, "uGLAD: A Deep Learning Model to Recover Conditional Independence Graphs," Microsoft Research, presented at the NeurIPS 2022 Workshop on New Frontiers in Graph Learning.

## Research question

How does the graph recovered by uGLAD change with the number of samples and with the training settings, compared with graphical lasso on exactly the same data? M2 answers the first half in the setting of the paper (Table 1) with the default training. Training settings, larger sample sizes and more baselines are for M3.

## What M2 contains

| Part | Where |
|---|---|
| The graphical model as code (variables, edges, factors) | `Code/src/ggm.py` |
| Learning (graphical lasso, uGLAD) | `Code/src/uglad_model.py`, `Code/src/baselines.py` |
| Inference (queries on the learned model) | `Code/src/ggm.py` |
| Baseline under the same conditions (graphical lasso) | `Code/src/baselines.py`, `Code/src/reproduce_table1.py` |
| Mathematical validation (23 checks) | `Code/src/validate.py`, `Results/validation/` |
| Initial KPI results and reproduction of the paper's Table 1 | `Results/reproduction/` and `Results/m2_figures/` |
| Demo for the video | `Code/src/demo.py` |

## Folder structure

```
M2_g12_th_conditional-ind-graphs_ind/
├── README.md
├── Report/
│   └── M2_g12_th_conditional-ind-graphs_ind_Report.pdf
├── Video/
│   ├── M2_g12_th_conditional-ind-graphs_ind_Slides.pptx
│   ├── M2_g12_th_conditional-ind-graphs_ind_Speaker_Notes.pdf
│   └── M2_g12_th_conditional-ind-graphs_ind_Video_Link.txt
├── Code/
│   ├── README.md          (setup, versions, seeds, run commands)
│   ├── requirements.txt
│   └── src/
├── Data/
│   └── README.md          (all data is synthetic, how it is generated)
└── Results/
    ├── README.md
    ├── reproduction/      (main experiment, saved matrices, audit of the setup)
    ├── m2_figures/        (the six figures and the numbers behind their captions)
    ├── validation/        (the 23 mathematical checks)
    └── demo/
```

## Contents checklist

| # | Item | Location | Status |
|---|------|----------|--------|
| 1 | README.md | this folder | Done |
| 2 | Report (PDF) | `Report/` | Done |
| 3 | Video link, slides and speaker notes | `Video/` | Link to be added after upload |
| 4 | Source code | `Code/src/` | Done |
| 5 | Code README with run steps | `Code/README.md` | Done |
| 6 | Data README | `Data/README.md` | Done |
| 7 | KPI tables, plots and logs | `Results/` | Done |

## Video

The recorded video is not stored in this repository. It is on Google Drive and the link is in `Video/M2_g12_th_conditional-ind-graphs_ind_Video_Link.txt`.

## Quick start

```bash
cd Code
pip install -r requirements.txt
cd src
python demo.py
```

The full run commands and the seeds are in `Code/README.md`.

## Status

The results are preliminary. They use 20 graphs for each of three sample sizes and the default training settings of the authors' code.
