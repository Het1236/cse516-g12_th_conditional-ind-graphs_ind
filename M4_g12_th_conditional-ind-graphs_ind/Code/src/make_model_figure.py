"""Draws the graphical-model figure of the report (matplotlib only). Output: Results/figures/fig_model.png"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Results", "figures", "fig_model.png")


def node(ax, x, y, label, color="#ffffff"):
    ax.add_patch(Circle((x, y), 0.34, fc=color, ec="black", lw=1.2, zorder=3))
    ax.text(x, y, label, ha="center", va="center", fontsize=9, zorder=4)


def arrow(ax, a, b, color="black", rad=0.0, style="-|>", lw=1.3, ls="-", trim=True):
    import math
    if trim and rad == 0.0 and abs(a[0] - b[0]) + abs(a[1] - b[1]) > 0.8:
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy)
        a = (a[0] + 0.36 * dx / d, a[1] + 0.36 * dy / d)
        b = (b[0] - 0.36 * dx / d, b[1] - 0.36 * dy / d)
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=14, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2, zorder=2))


fig, ax = plt.subplots(figsize=(10.0, 3.3))
ax.set_xlim(0, 13.4)
ax.set_ylim(-0.2, 4.2)
ax.axis("off")
ax.set_aspect("equal")

# left: temporal graph for three variables
xs = {"t-2": 1.0, "t-1": 3.0, "t": 5.0}
ys = {1: 3.2, 2: 2.0, 3: 0.8}
for k, x in xs.items():
    ax.text(x, 3.95, f"time {k}", ha="center", fontsize=9, fontweight="bold")
    for i, y in ys.items():
        node(ax, x, y, f"X{i}")
for i in ys:
    arrow(ax, (xs["t-2"], ys[i]), (xs["t-1"], ys[i]), "#1f618d")
    arrow(ax, (xs["t-1"], ys[i]), (xs["t"], ys[i]), "#1f618d")
arrow(ax, (xs["t-2"], ys[1]), (xs["t-1"], ys[2]), "#1f618d")
arrow(ax, (xs["t-1"], ys[3]), (xs["t"], ys[2]), "#1f618d")
arrow(ax, (xs["t"] + 0.34, ys[1] - 0.1), (xs["t"] + 0.34, ys[2] + 0.1), "#b03a2e", rad=-0.55, lw=1.8)
arrow(ax, (xs["t"] + 0.34, ys[2] - 0.1), (xs["t"] + 0.34, ys[3] + 0.1), "#b03a2e", rad=-0.55, lw=1.8)
ax.text(3.0, -0.15, "blue: lagged edges (any pair, cycles through time allowed)\nred: instantaneous edges (must form a DAG)",
        ha="center", fontsize=7.5)

# middle: posterior
ax.add_patch(FancyBboxPatch((6.2, 1.0), 2.4, 2.4, boxstyle="round,pad=0.05", fc="#fdf2e9", ec="#ca6f1e", lw=1.3))
ax.text(7.4, 3.0, "Rhino posterior q(G)", ha="center", fontsize=9, fontweight="bold")
ax.text(7.4, 2.35, "one probability per edge entry\np_e = q(edge e exists)", ha="center", fontsize=8)
ax.text(7.4, 1.5, "instantaneous: 3-way categorical\nlagged: independent Bernoulli", ha="center", fontsize=7.5)
arrow(ax, (5.75, 2.0), (6.15, 2.0), "black", trim=False)

# right: selection
ax.add_patch(FancyBboxPatch((9.4, 2.35), 3.5, 1.3, boxstyle="round,pad=0.05", fc="#eaf2f8", ec="#1f618d", lw=1.3))
ax.text(11.15, 3.3, "selection rule S", ha="center", fontsize=9, fontweight="bold")
ax.text(11.15, 2.75, "keep the top-k entries while\npromised error mean(1 - p_e) <= alpha", ha="center", fontsize=7.5)
ax.add_patch(FancyBboxPatch((9.4, 0.35), 3.5, 1.3, boxstyle="round,pad=0.05", fc="#eafaf1", ec="#117a65", lw=1.3))
ax.text(11.15, 1.3, "what we measure", ha="center", fontsize=9, fontweight="bold")
ax.text(11.15, 0.75, "realised false discovery proportion\nvs promised, and power", ha="center", fontsize=7.5)
arrow(ax, (8.65, 2.5), (9.35, 2.9), "black", trim=False)
arrow(ax, (11.15, 2.3), (11.15, 1.7), "black", trim=False)
fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=220)
print("wrote", OUT)
