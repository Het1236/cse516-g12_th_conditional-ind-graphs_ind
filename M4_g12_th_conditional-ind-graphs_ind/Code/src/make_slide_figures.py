"""Figures for the M4 slides: base-paper numbers (typed from the Rhino paper, ICLR 2023) and schematics.
Schematics are marked as such in the slides. They contain no result of this project.
Run:  python make_slide_figures.py   ->  Results/figures/slide_*.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.normpath(os.path.join(HERE, "..", "..", "Results", "figures"))
MAROON, BLUE, RED, GREEN, GREY = "#801B19", "#333333", "#801B19", "#555555", "#8A8A8A"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 13,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 1.0})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=200, facecolor="white")
    plt.close(fig)
    print("saved", name)


# 1. history-dependent noise (simulated illustration)
rng = np.random.default_rng(0)
x = rng.uniform(-2, 2, 700)
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.7), sharey=True)
ax[0].scatter(x, rng.normal(0, 0.45, x.size), s=7, color=GREY, alpha=0.7)
ax[0].set_title("Noise does not depend on the past", fontsize=14)
ax[1].scatter(x, rng.normal(0, 1, x.size) * (0.12 + 0.5 * np.abs(x)), s=7, color=MAROON, alpha=0.7)
ax[1].set_title("Noise depends on the past (Rhino)", fontsize=14, color=MAROON)
for a in ax:
    a.set_xlabel("past value of the parent")
    a.axhline(0, color="black", lw=0.8)
ax[0].set_ylabel("noise of the variable")
save(fig, "slide_noise.png")

# 2. lag ablation, paper Table 1 (temporal F1)
dims = ["5", "10", "20", "40"]
f1 = {"L=1": [0.34, 0.28, 0.25, 0.20], "L=2 (true lag)": [0.59, 0.49, 0.39, 0.37], "L=3": [0.56, 0.45, 0.37, 0.32]}
fig, ax = plt.subplots(figsize=(6.4, 4.0))
w = 0.26
for k, (lab, col) in enumerate(zip(f1, ["#BDBDBD", MAROON, "#555555"])):
    ax.bar(np.arange(4) + (k - 1) * w, f1[lab], w, label=lab, color=col)
ax.set_xticks(range(4))
ax.set_xticklabels(dims)
ax.set_xlabel("number of nodes")
ax.set_ylabel("temporal F1")
ax.set_ylim(0, 0.7)
ax.legend(frameon=False, fontsize=11)
save(fig, "slide_lag.png")

# 3. DREAM3, paper Table 2 (AUROC)
nets = ["E.Coli 1", "E.Coli 2", "Yeast 1", "Yeast 2", "Yeast 3"]
d3 = {"eSRU": [0.66, 0.629, 0.627, 0.557, 0.55], "DYNOTEARS": [0.59, 0.547, 0.527, 0.526, 0.51],
      "PCMCI+": [0.53, 0.519, 0.53, 0.51, 0.512], "Rhino+g": [0.673, 0.665, 0.659, 0.598, 0.588], "Rhino": [0.685, 0.68, 0.664, 0.585, 0.567]}
fig, ax = plt.subplots(figsize=(9.6, 4.0))
w = 0.16
for k, (lab, col) in enumerate(zip(d3, ["#8A8A8A", "#B8B8B8", "#D5D5D5", "#C98E8B", MAROON])):
    ax.bar(np.arange(5) + (k - 2) * w, d3[lab], w, label=lab, color=col)
ax.axhline(0.5, color="black", lw=0.8, ls="--", label="chance")
ax.set_xticks(range(5))
ax.set_xticklabels(nets)
ax.set_ylim(0.45, 0.72)
ax.set_ylabel("AUROC (summary graph)")
ax.legend(frameon=False, ncol=6, fontsize=10.5, loc="upper right")
save(fig, "slide_dream3.png")

# 4. Netsim, paper Table 3 (AUROC)
ns = [("Rhino", 0.99), ("Rhino+g", 0.974), ("cMLP", 0.93), ("Rhino, no instantaneous", 0.93), ("TCDF", 0.91), ("DYNOTEARS", 0.90),
      ("eSRU", 0.88), ("VAR-LiNGAM", 0.84), ("cLSTM", 0.83), ("PCMCI+", 0.83), ("SRU", 0.80)]
fig, ax = plt.subplots(figsize=(8.2, 4.4))
names, vals = zip(*ns[::-1])
cols = [MAROON if n.startswith("Rhino") else GREY for n in names]
ax.barh(names, vals, color=cols)
for i, v in enumerate(vals):
    ax.text(v + 0.004, i, f"{v:.3f}".rstrip("0"), va="center", fontsize=11)
ax.set_xlim(0.5, 1.03)
ax.set_xlabel("AUROC (summary graph)")
save(fig, "slide_netsim.png")

# 5. schematic reliability diagram
p = np.linspace(0.001, 0.999, 300)
lo = np.log(p / (1 - p))
fig, ax = plt.subplots(figsize=(5.2, 4.6))
ax.plot([0, 1], [0, 1], "k--", lw=1.4, label="calibrated")
ax.plot(p, 1 / (1 + np.exp(-lo / 4)), color=MAROON, lw=2.6, label="overconfident")
ax.set_xlabel("probability the model states")
ax.set_ylabel("how often the edge is real")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.legend(frameon=False, loc="upper left")
ax.annotate("says 0.99,\nreal far less often", xy=(0.97, 0.69), xytext=(0.5, 0.2), arrowprops=dict(arrowstyle="->", color=MAROON), color=MAROON, fontsize=12)
save(fig, "slide_reliability_schematic.png")

# 6. schematic Bayesian FDR
idx = np.arange(1, 41)
ps = 1 / (1 + np.exp((idx - 22) / 5.5))
ps = np.clip(ps, 0.03, 0.99)
run = np.cumsum(1 - ps) / idx
alpha = 0.2
k = int(np.max(np.where(run <= alpha)[0])) + 1
fig, ax = plt.subplots(figsize=(8.6, 4.2))
ax.bar(idx, ps, color=[MAROON if i < k else "#CFCFCF" for i in range(40)], width=0.8)
ax.plot(idx, run, color=BLUE, lw=2.6, label="promised error of the top-k list")
ax.axhline(alpha, color="black", ls="--", lw=1.2, label="budget alpha")
ax.axvline(k + 0.5, color=MAROON, ls=":", lw=1.6)
ax.text(k + 1.2, 0.93, "keep the first k", color=MAROON, fontsize=12)
ax.set_xlabel("edge entries sorted by probability p")
ax.set_ylabel("p (bars), promised error (line)")
ax.set_ylim(0, 1.05)
ax.legend(frameon=False, loc="center right", fontsize=11, bbox_to_anchor=(1.0, 0.62))
print("k =", k)
save(fig, "slide_bfdr.png")

# 7. schematic target: realised FDP against budget
a = np.linspace(0, 0.5, 50)
fig, ax = plt.subplots(figsize=(5.4, 4.6))
ax.fill_between(a, a, 0.5, color=RED, alpha=0.13)
ax.plot(a, a, "k-", lw=2.2)
ax.text(0.31, 0.19, "promise kept", rotation=0, fontsize=12)
ax.text(0.04, 0.38, "more wrong\nthan promised", color=RED, fontsize=13)
ax.set_xlabel("budget alpha (promised)")
ax.set_ylabel("realised false discovery proportion")
ax.set_xlim(0, 0.5)
ax.set_ylim(0, 0.5)
save(fig, "slide_target.png")
