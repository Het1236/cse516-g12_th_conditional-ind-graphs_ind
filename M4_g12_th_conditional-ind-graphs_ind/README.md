# Milestone 4: final submission

**Title:** Can a Deep Temporal Causal Posterior Be Trusted? Error-Controlled Edge Selection for Rhino
**Student:** Het Patel (AU2440266), B.Tech CSE, Ahmedabad University.
**Course:** CSE 516, Probabilistic Graphical Models. **Track:** Theoretical AI. **Group:** `g12_th_conditional-ind-graphs_ind` (individual project).
**Deadline:** 12 November 2026, 11:59 PM.
**Base paper:** W. Gong, J. Jennings, C. Zhang, N. Pawlowski, *Rhino: Deep Causal Temporal Relationship Learning with History-dependent Noise*, ICLR 2023 (Microsoft Research), arXiv 2210.14706.

## The question

A causal discovery method that returns edge probabilities should let a user say how many reported edges are wrong. Rhino learns a posterior q(G) over temporal causal graphs.
The paper scores its probabilities through AUROC and F1 against a known graph. **Can the probabilities be used to select edges with a stated error budget?**

## What this milestone offers

A small idea, a plan and a first test. It is not a new causal discovery method, and the formulation is not claimed as a theory.

- **The idea:** treat Rhino's edge probabilities as a promise about the share of wrong edges, and check the promise. One identity is used: realised FDP = promised error + overconfidence on the selected set. Two standard facts (Bayesian FDR control under calibration, rank invariance) are in Appendix A of the report.
- **The plan:** read exact edge probabilities from the saved M3 weights, calibrate them with a temperature or a cutoff learned on other datasets, select edges under a budget. No model was retrained.
- **A first test** on **500 finished M3 runs** (440 synthetic, 10 Netsim, 50 DREAM3), with five expectations (H1 to H5). H5 was added after seeing H2 and is marked exploratory. The talk shows no results of our own. They are in the report.

## Main findings (all from `Results/tables`)

| Finding | Number |
|---|---|
| Rhino's posterior is saturated and wrongly certain | 9.4% of entries have p > 0.999 and 23.3% of those are not edges. 17.6% of the entries with p < 0.001 are true edges. |
| Raw posterior breaks its budget | Budget 0.01: realised FDP 0.306 [0.277, 0.335] (120 datasets) |
| Temperature scaling fixes the scores, not the control | ECE 0.200 to 0.039, log-loss 1.39 to 0.51. At budget 0.2: 0.314 realised against 0.195 promised. No edges selected at budget <= 0.05. |
| A learned cutoff gives approximate control for budgets 0.1 to 0.3 | Realised 0.062, 0.244, 0.311. Power only 0.026, 0.369, 0.499. |
| Label-free graph choice (expected F1) does not beat threshold 0.5 | F1 0.522 against 0.555. Oracle 0.642. |
| Accuracy and trust disagree across variants | Rhino has the best F1 (0.555). Rhino+s is the only variant near its promise (0.103 at budget 0.1) with F1 0.267. |
| Real data | Calibration does not transfer. DREAM3: 85.9% of edges selected at budget 0.1 are wrong. |

## Contents of this folder (what the course asks for)

| # | File | Location |
|---|---|---|
| 1 | This README | `README.md` |
| 2 | PDF report (16 pages, follows the talk, ICLR-style layout) and its LaTeX source | `Report/M4_g12_th_conditional-ind-graphs_ind_Report.pdf`, source in `Report/latex/` |
| 3 | Video link (the video itself is not in git) | `Video/M4_g12_th_conditional-ind-graphs_ind_Video_Link.txt` |
| 4 | Slides (30, PDF and pptx, in the format of the M1 slides). The deck explains Rhino from scratch, the gap, and our idea, why it is logical, why it matters, our plan, KPIs and expected gains. It shows no result of our own experiments (those are in the report) | `Presentation/` |
| 5 | Source code (export, analysis, report and slide builders, tests) | `Code/src/` |
| 6 | Code README: setup, commands, seeds, environment, workstation scripts | `Code/README.md` |
| 7 | Data README: sources, format of the exported probability files | `Data/README.md` |
| 8 | KPI tables, plots, statistical outputs, exported inputs | `Results/` (see `Results/README.md`) |

The Individual Google Form is submitted separately by the student.

## Reproduce everything

```bash
cd Code/src
pip install -r ../requirements.txt
python tests/test_calib_fdr.py
python run_all_analysis.py --exact && python run_all_analysis.py
python make_model_figure.py && python make_slide_figures.py && python build_report.py && python build_slides.py --pdf   # report needs pdflatex, slides need PowerPoint and Word
```
About 5 minutes. The inputs (`Results/qG_exact`, `Results/qG_export`) were produced from the M3 runs by the scripts in `Code/workstation/` (see `Code/README.md`).
The M3 runs themselves are in `../M3_g12_th_conditional-ind-graphs_ind` (their environment: Python 3.9, torch 1.12.1 CPU, causica v0.0.0, lab workstation).

## Honest limits (details in report Section 15)

- The learned cutoff controls the *average* FDP over datasets like the calibration data. There is no finite-sample guarantee and no per-dataset guarantee.
- It needs labelled graphs from similar data, and it does not transfer from synthetic data to DREAM3.
- One model seed per dataset. Up to 20 nodes. The link between training length and saturation is supported only indirectly (two settings, five runs each on Netsim).
- Edge selection does not enforce acyclicity of the instantaneous part.
- The search for related work was short. PRCD-MAP (arXiv 2605.01669) was read in summary only.
- No GPU was used. M3 and the analysis are CPU runs.

## Earlier milestones

M1 and M2 studied uGLAD. On 31 October 2026 the base paper changed to Rhino. M3 reproduced the Rhino experiments. M4 asks a new question on top of the M3 runs.
