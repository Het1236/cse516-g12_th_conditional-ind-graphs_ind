# M1 — g12_th_conditional-ind-graphs_ind

**Course:** CSE 516 — Probabilistic Graphical Models
**Milestone:** M1 — Proposal and Scoping
**Student:** Het Patel (AU2440266)
**Track:** Theoretical AI (Individual research)
**Submission date:** 15 September 2026

## Project

This project studies conditional independence (CI) graph recovery using **uGLAD**, a deep
learning model from Microsoft Research that recovers sparse Gaussian graphical models by
unrolling the graphical lasso optimization into a small neural network, without needing
ground-truth graphs during training.

The base paper is:

> H. Shrivastava, U. Chajewska, R. Abraham, and X. Chen, "uGLAD: A Deep Learning Model to
> Recover Conditional Independence Graphs," Microsoft Research, presented at the NeurIPS 2022
> Workshop on New Frontiers in Graph Learning.

This is a Theoretical AI project. The goal is not to propose a new algorithm, but to study
uGLAD in depth: its representation, its learning method, and its inference behaviour, as posed
by the paper itself. Reading of uGLAD's direct predecessor (GLAD) and its two follow-up papers
(Neural Graphical Models, Neural Graph Revealers) is still in progress. Our own specific research
question, baseline comparison, and experimental design will be finalized once this reading is
complete, ahead of M2.

Full details (the problem as posed by the paper, PGM mapping, SOTA positioning, candidate
baselines and metrics, and the timeline) are in the report.

## Folder Structure

```
M1_g12_th_conditional-ind-graphs_ind/
├── README.md
├── Report/
│   └── M1_g12_th_conditional-ind-graphs_ind_Report.pdf
├── Video/
│   ├── M1_g12_th_conditional-ind-graphs_ind_Slides.pptx
│   └── M1_g12_th_conditional-ind-graphs_ind_Video_Link.txt
├── Code/
│   ├── README.md
│   └── src/            (empty at M1, kept with .gitkeep, filled from M2)
├── Data/
│   └── README.md
└── Results/
    └── README.md
```

## M1 Contents

| # | File | Location | Required |
|---|------|----------|----------|
| 1 | README.md | `M1_g12_th_conditional-ind-graphs_ind/` | Yes |
| 2 | M1_g12_th_conditional-ind-graphs_ind_Report.pdf | `Report/` | Yes |
| 3 | M1_g12_th_conditional-ind-graphs_ind_Video_Link.txt (and the slide deck) | `Video/` | Yes |
| 4 | Source files | `Code/src/` | None yet — see `Code/README.md` |
| 5 | README.md explaining how to run the code | `Code/` | Yes (placeholder) |
| 6 | README.md with the dataset link or download steps | `Data/` | Yes (placeholder) |
| 7 | Plots, tables, or draft graphical models | `Results/` | None yet — see `Results/README.md` |

No code, dataset, or results exist yet. This milestone is a proposal and scoping document, and
each of `Code/`, `Data/`, `Results/` carries its own README explaining what is planned and why
it is currently empty, so the folders stay present (and pushable to git) from M1 onward instead
of being added later.

## How to read this submission

1. Start with `Report/M1_g12_th_conditional-ind-graphs_ind_Report.pdf` for the full write-up.
2. The `Video/` folder holds the slide deck used to record the milestone walkthrough. The
   recorded video itself is not stored in this repository; its link is in
   `Video/M1_g12_th_conditional-ind-graphs_ind_Video_Link.txt`.
3. `Code/`, `Data/`, and `Results/` are placeholders for now — each README says what will land
   there starting at M2.

## Note on the video file

The recorded walkthrough video is hosted on Google Drive rather than committed to this
repository, since a multi-minute recording is too large for a git repo. Only the shareable
link is tracked, in `Video/M1_g12_th_conditional-ind-graphs_ind_Video_Link.txt`. A `.gitignore`
at the root of this folder excludes any video file placed in `Video/` so it never gets staged
by accident.

## Generative AI use

Research reading, drafting, and formatting for this milestone were assisted by AI tools for
literature discovery, writing clarity, and document/slide formatting. All technical claims,
citations, and the research plan were reviewed and are understood by the author.
