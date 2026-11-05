"""Figures for the M3 report. Everything is drawn from the exported result tables and raw files."""
import math, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Results"))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(R, "tables", "report_extra"); FIG = os.path.join(R, "figures", "report"); os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "mathtext.fontset": "stix",
                     "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10.5, "legend.fontsize": 9,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.dpi": 200, "figure.dpi": 100})
NAMES = {"rhino": "Rhino", "rhino_g": "Rhino+g", "rhino_s": "Rhino+s", "dynotears": "DYNOTEARS",
         "varlingam": "VAR-LiNGAM", "pcmci_plus": "PCMCI+"}
COL = {"rhino": "#1f5fbf", "rhino_g": "#d9541e", "rhino_s": "#1a9e6f", "dynotears": "#e69f00",
       "varlingam": "#cc79a7", "pcmci_plus": "#4d4d4d"}
MK = {"rhino": "o", "rhino_g": "s", "rhino_s": "^", "dynotears": "D", "varlingam": "v", "pcmci_plus": "P"}
ORDER = list(NAMES)
sm = pd.read_csv(os.path.join(R, "tables", "synth_summary_orientation.csv"))
fa = pd.read_csv(os.path.join(R, "tables", "synth_factors_orientation.csv"))
rt = pd.read_csv(os.path.join(R, "tables", "synth_runtime.csv"))


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".png"), bbox_inches="tight"); plt.close(fig)


def sub(ax, t):
    ax.set_title(t, fontsize=11)


# Fig 1: main result, three parts of the temporal graph
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3), sharey=True)
parts = [("F1_inst", "Instantaneous"), ("F1_lag", "Lagged"), ("F1_temporal", "Temporal (all)")]
w = 0.13
for ax, (met, title) in zip(axes, parts):
    for k, m in enumerate(ORDER):
        for j, dim in enumerate((5, 10, 20)):
            r = sm[(sm.dim == dim) & (sm.method == m) & (sm.metric == met)].iloc[0]
            ax.bar(j + (k - 2.5) * w, r["mean"], w * 0.92, color=COL[m], label=NAMES[m] if j == 0 else None,
                   yerr=[[max(r["mean"] - r.ci_lo, 0)], [max(r.ci_hi - r["mean"], 0)]], capsize=1.5,
                   error_kw=dict(lw=0.7, ecolor="#222"))
    ax.set_xticks(range(3)); ax.set_xticklabels(["5 nodes", "10 nodes", "20 nodes"]); sub(ax, title)
axes[0].set_ylabel("Orientation F1"); axes[0].set_ylim(0, 0.85)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.5, -0.07))
save(fig, "fig1_main")

# Fig 2: history dependence and instantaneous effects
fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.4), sharey=True)
for ax, fac, labs, title in ((axes[0], "hist", ("No history-dependent noise", "History-dependent noise"), "(a) history-dependent noise"),
                             (axes[1], "inst", ("No instantaneous effects", "Instantaneous effects"), "(b) instantaneous effects")):
    for k, m in enumerate(ORDER):
        xs, ys, lo, hi = [], [], [], []
        for j, dim in enumerate((5, 10, 20)):
            for lv in (0, 1):
                r = fa[(fa.dim == dim) & (fa.factor == fac) & (fa.level.astype(str) == str(lv)) & (fa.method == m)].iloc[0]
                xs.append(j * 3 + lv + (k - 2.5) * 0.14); ys.append(r["mean"]); lo.append(r["mean"] - r.ci_lo); hi.append(r.ci_hi - r["mean"])
        ax.bar(xs, ys, 0.13, color=COL[m], label=NAMES[m], yerr=[lo, hi], capsize=1.2, error_kw=dict(lw=0.6, ecolor="#222"))
    ax.set_xticks([0, 1, 3, 4, 6, 7]); ax.set_xticklabels(["no", "yes"] * 3)
    for j, dim in enumerate((5, 10, 20)):
        ax.text(j * 3 + 0.5, -0.17, f"{dim} nodes", ha="center", transform=ax.get_xaxis_transform())
    sub(ax, title)
axes[0].set_ylabel("Temporal orientation F1"); axes[0].set_ylim(0, 0.9)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.5, -0.2))
save(fig, "fig2_factors")

# Fig 3: accuracy against run time
fig, ax = plt.subplots(figsize=(5.6, 3.8))
for m in ORDER:
    xs, ys = [], []
    for dim in (5, 10, 20):
        xs.append(rt[(rt.dim == dim) & (rt.method == m)]["median"].iloc[0])
        ys.append(sm[(sm.dim == dim) & (sm.method == m) & (sm.metric == "F1_temporal")]["mean"].iloc[0])
    ax.plot(xs, ys, "-", color=COL[m], lw=1, alpha=0.7)
    ax.scatter(xs, ys, color=COL[m], marker=MK[m], s=[22, 40, 66], label=NAMES[m], zorder=3)
ax.set_xscale("log"); ax.set_xlabel("Median wall time per dataset (minutes, log scale)"); ax.set_ylabel("Mean temporal orientation F1")
ax.text(0.99, 0.02, "marker size grows with the dimension (5, 10, 20)", transform=ax.transAxes, ha="right", fontsize=8.5)
ax.legend(frameon=False, loc="upper left", ncol=2, fontsize=8.5)
save(fig, "fig3_tradeoff")

# Fig 4: lag ablation
t1 = pd.read_csv(os.path.join(R, "tables", "table1_lag_ablation.csv"))
syraw = pd.read_csv(os.path.join(R, "raw", "results_synthetic_all.csv")); syraw = syraw[syraw.status == "ok"]
fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.3))
dcol = {5: "#1f5fbf", 10: "#d9541e", 20: "#1a9e6f"}
for dim in (5, 10, 20):
    for ax, col, lab in ((axes[0], "orientation_fscore_overall_temporal", "Temporal orientation F1"), (axes[1], None, "Training log-likelihood")):
        ms, los, his = [], [], []
        for lag in (1, 2, 3):
            r = t1[(t1.dim == dim) & (t1.lag == f"L={lag}")].iloc[0]
            if col:
                mean = r["F1_temporal_mean"]; sd = float(str(r["F1_temporal"]).split("+-")[1])
            else:
                mean = r["LL_mean"]; sd = float(str(r["LL"]).split("+-")[1])
            n = int(r["n"]); h = stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
            ms.append(mean); los.append(h)
        ax.errorbar([1, 2, 3], ms, yerr=los, marker="o", color=dcol[dim], capsize=3, label=f"{dim} nodes")
for ax, lab, t in ((axes[0], "Temporal orientation F1", "(a) graph quality"), (axes[1], "Training log-likelihood per sample", "(b) fit to the data")):
    ax.set_xticks([1, 2, 3]); ax.set_xlabel("Lag of the model (true lag is 2)"); ax.set_ylabel(lab); sub(ax, t)
axes[0].legend(frameon=False)
save(fig, "fig4_lag")

# Fig 5: precision and recall
ea = pd.read_csv(os.path.join(OUT, "x_error.csv"))
fig, ax = plt.subplots(figsize=(5.6, 4.0))
for m in ORDER:
    for dim in (5, 10, 20):
        r = ea[(ea.dim == dim) & (ea.method == m)].iloc[0]
        ax.scatter(r.rec, r.prec, color=COL[m], marker=MK[m], s=[22, 40, 66][(5, 10, 20).index(dim)],
                   label=NAMES[m] if dim == 5 else None, zorder=3)
ax.set_xlabel("Recall of oriented edges (temporal graph)"); ax.set_ylabel("Precision of oriented edges")
ax.set_xlim(0, 0.8); ax.set_ylim(0, 1.0)
ax.text(0.99, 0.02, "marker size grows with the dimension (5, 10, 20)", transform=ax.transAxes, ha="right", fontsize=8.5)
ax.legend(frameon=False, loc="upper right", ncol=2, fontsize=8.5)
save(fig, "fig5_pr")

# Fig 6: treatment effect
te = pd.read_csv(os.path.join(R, "raw", "results_treatment_effect_all.csv")); te = te[te.status == "ok"]
m = te.merge(syraw[["method", "dataset", "orientation_fscore_overall_temporal", "hist"]], on=["method", "dataset"])
fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.4))
ax = axes[0]
for k, mm in enumerate(("rhino", "rhino_g", "rhino_s")):
    for j, dim in enumerate((5, 10, 20)):
        v = te[(te.method == mm) & (te.dim == dim)].ATE_RMSE.values
        b = ax.boxplot(v, positions=[j + (k - 1) * 0.26], widths=0.22, patch_artist=True, showfliers=False,
                       medianprops=dict(color="black"))
        b["boxes"][0].set_facecolor(COL[mm]); b["boxes"][0].set_alpha(0.85)
ax.set_xticks(range(3)); ax.set_xticklabels(["5 nodes", "10 nodes", "20 nodes"]); ax.set_ylabel("RMSE of the average treatment effect")
for mm in ("rhino", "rhino_g", "rhino_s"):
    ax.plot([], [], "s", color=COL[mm], label=NAMES[mm])
ax.legend(frameon=False); sub(ax, "(a) error by method")
ax = axes[1]
for hv, mk, lab in ((0, "o", "no history-dependent noise"), (1, "^", "history-dependent noise")):
    s = m[m["hist"] == hv]
    ax.scatter(s.orientation_fscore_overall_temporal, s.Normalised_ATE_RMSE, s=9, marker=mk, alpha=0.55, label=lab)
ax.set_xlabel("Temporal orientation F1 of the same model"); ax.set_ylabel("Normalised ATE RMSE"); ax.legend(frameon=False)
sub(ax, "(b) error against graph quality (360 models)")
save(fig, "fig6_te")

# Fig 7: DREAM3 and Netsim AUROC
d3 = pd.read_csv(os.path.join(R, "tables", "real_dream3_auroc.csv")); ns = pd.read_csv(os.path.join(R, "tables", "real_netsim_auroc.csv"))
meths = ["cMLP", "cLSTM", "TCDF", "SRU", "eSRU", "DYNOTEARS", "PCMCI+", "Rhino+g", "Rhino"]
mcol = {"Rhino": "#1f5fbf", "Rhino+g": "#d9541e", "DYNOTEARS": "#e69f00", "PCMCI+": "#4d4d4d"}
nets = [("ecoli1", "E. coli 1"), ("ecoli2", "E. coli 2"), ("yeast1", "Yeast 1"), ("yeast2", "Yeast 2"), ("yeast3", "Yeast 3")]
fig, axes = plt.subplots(1, 5, figsize=(11.2, 3.4))
for ax, (net, title) in zip(axes, nets):
    for y, mm in enumerate(meths):
        r = d3[(d3.network == net) & (d3.method == mm)].iloc[0]
        c = mcol.get(mm, "#8a8a8a")
        if r["variant"].startswith("quoted"):
            ax.scatter(r["mean"], y, marker="s", color=c, s=26, zorder=3)
        else:
            if not math.isnan(r.ci_lo):
                ax.plot([r.ci_lo, r.ci_hi], [y, y], color=c, lw=2)
            ax.scatter(r["mean"], y, marker="o", color=c, s=30, zorder=3)
            ax.scatter(r.paper_value, y, marker="D", facecolor="none", edgecolor="black", s=34, zorder=4)
    ax.set_xlim(0.45, 0.75); ax.set_yticks(range(len(meths))); ax.set_yticklabels(meths if net == "ecoli1" else [])
    ax.tick_params(axis="y", labelleft=(net == "ecoli1"))
    ax.set_ylim(-0.7, len(meths) - 0.3)
    ax.set_xlabel("AUROC"); sub(ax, title)
    ax.set_xticks([0.5, 0.6, 0.7])
ax = axes[0]
ax.scatter([], [], marker="o", color="#555", label="this run, paper settings (mean, 95% interval)")
ax.scatter([], [], marker="D", facecolor="none", edgecolor="black", label="value printed in the paper")
ax.scatter([], [], marker="s", color="#8a8a8a", label="quoted by the paper, not re-run")
fig.legend(*ax.get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.1))
save(fig, "fig7_dream3")

order = ["cMLP", "cLSTM", "TCDF", "SRU", "eSRU", "DYNOTEARS", "PCMCI+", "VAR-LiNGAM", "Rhino+NoInst", "Rhino+g", "Rhino"]
ncol = {"Rhino": "#1f5fbf", "Rhino+g": "#d9541e", "Rhino+NoInst": "#7a4fd1", "DYNOTEARS": "#e69f00", "PCMCI+": "#4d4d4d", "VAR-LiNGAM": "#cc79a7"}
fig, ax = plt.subplots(figsize=(6.2, 3.8))
for y, mm in enumerate(order):
    rows = ns[ns.method == mm]
    for _, r in rows.iterrows():
        c = ncol.get(mm, "#8a8a8a")
        if r["variant"].startswith("quoted"):
            ax.scatter(r["mean"], y, marker="s", color=c, s=26, zorder=3)
        elif r["variant"] == "shipped":
            ax.scatter(r["mean"], y, marker="^", color=c, s=34, zorder=3)
        else:
            if not math.isnan(r.ci_lo):
                ax.plot([r.ci_lo, r.ci_hi], [y, y], color=c, lw=2)
            ax.scatter(r["mean"], y, marker="o", color=c, s=30, zorder=3)
            ax.scatter(r.paper_value, y, marker="D", facecolor="none", edgecolor="black", s=34, zorder=4)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.set_xlim(0.78, 1.0); ax.set_xlabel("AUROC of the summary graph (Netsim Sim-3)")
ax.scatter([], [], marker="o", color="#555", label="this run, paper settings"); ax.scatter([], [], marker="^", color="#555", label="this run, released config")
ax.scatter([], [], marker="D", facecolor="none", edgecolor="black", label="value in the paper"); ax.scatter([], [], marker="s", color="#8a8a8a", label="quoted, not re-run")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8.5)
save(fig, "fig8_netsim")

# Fig 9: Netsim training curves (own redraw of the exported means, three settings)
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2))
for k, (nm, lab, c) in enumerate((("rhino_shipped", "Rhino", "#1f5fbf"), ("rhino_g_shipped", "Rhino+g", "#d9541e"),
                                  ("rhino_noinst_shipped", "Rhino+NoInst", "#7a4fd1"))):
    d = pd.read_csv(os.path.join(R, "tables", f"fig8_netsim_{nm}.csv"))
    axes[0].plot(d.step, d.auroc, color=c, label=lab); axes[1].plot(d.step, d.orientation_f1, color=c, label=lab)
    axes[2].plot(d.step, d.val_ll, color=c, label=lab)
for ax, t, y in zip(axes, ("(a) AUROC", "(b) orientation F1", "(c) validation log-likelihood"), ("AUROC", "Orientation F1", "Validation log-likelihood")):
    ax.set_xlabel("Augmented Lagrangian step"); ax.set_ylabel(y); sub(ax, t)
axes[0].legend(frameon=False)
save(fig, "fig9_curves")
print("figures:", sorted(os.listdir(FIG)))
