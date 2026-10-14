import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.patches import Ellipse

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(HERE, "..", "..", "Results", "reproduction", "table1_author_generator")
OUT = os.path.join(HERE, "..", "..", "Results", "m2_figures")
SIZES = [10, 25, 50]

PAPER = {"AUPR": {"SGLCV": [0.112, 0.132, 0.219], "uGLAD": [0.159, 0.174, 0.223]},
         "AUC": {"SGLCV": [0.505, 0.532, 0.617], "uGLAD": [0.572, 0.595, 0.651]}}
PAPER_STD = {"AUPR": {"SGLCV": [0.013, 0.012, 0.085], "uGLAD": [0.029, 0.018, 0.062]},
             "AUC": {"SGLCV": [0.007, 0.031, 0.083], "uGLAD": [0.027, 0.044, 0.021]}}

BLUE, RED, GREEN, GREY = "#1f2fa0", "#b01515", "#1a7a1a", "#555555"
K = 1.25
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "mathtext.fontset": "stix",
    "font.size": 8 * K, "axes.labelsize": 9 * K, "axes.linewidth": 0.8, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True, "xtick.major.size": 3, "ytick.major.size": 3, "legend.fontsize": 6.5 * K,
    "legend.frameon": True, "legend.fancybox": False, "legend.edgecolor": "black", "legend.framealpha": 1.0,
    "axes.grid": True, "grid.alpha": 0.35, "grid.linewidth": 0.5, "savefig.bbox": "tight",
})


def callout(ax, text, xy, xytext, ellipse=None):
    if ellipse is not None:
        ax.add_patch(Ellipse(xy, ellipse[0], ellipse[1], fill=False, lw=0.8, ec="black", zorder=5))
    ax.annotate(text, xy=xy, xycoords="data", xytext=xytext, textcoords="axes fraction", fontsize=7.88, ha="left", va="center",
                bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="black", lw=0.6),
                arrowprops=dict(arrowstyle="-|>", lw=0.6, color="black", shrinkA=0, shrinkB=2), zorder=6)


def better_arrow(ax, x, y0, y1, text="higher is better"):
    ax.annotate("", xy=(x, y1), xytext=(x, y0), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="red", ls=":", lw=1.1))
    ax.text(x - 0.035, (y0 + y1) / 2, text, rotation=90, color="red", fontsize=7.50, ha="center", va="center", transform=ax.transAxes)


def log_axis(ax):
    ax.set_xscale("log")
    ax.set_xticks(SIZES)
    ax.set_xticklabels([str(s) for s in SIZES])
    ax.minorticks_off()
    ax.set_xlim(7.5, 70)


def stats(df, method, metric):
    g = df[df.method == method].groupby("M")[metric]
    return np.array([g.mean()[s] for s in SIZES]), np.array([g.std()[s] for s in SIZES])


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=220)
    plt.close(fig)


def main():
    raw = pd.read_csv(os.path.join(FOLDER, "table1_raw.csv"))
    mine = pd.read_csv(os.path.join(FOLDER, "mine_raw.csv")) if os.path.exists(os.path.join(FOLDER, "mine_raw.csv")) else None
    kp = pd.read_csv(os.path.join(FOLDER, "kpis_raw.csv")) if os.path.exists(os.path.join(FOLDER, "kpis_raw.csv")) else None
    allr = pd.concat([raw, mine], ignore_index=True) if mine is not None else raw
    n_graphs = int(raw[raw.method == "uGLAD"].groupby("M").graph.nunique().min())
    density = float(raw.n_true_edges.mean() / 300.0)
    cap, num = {}, {"graphs": n_graphs, "chance_AUPR": density, "mean_true_edges": float(raw.n_true_edges.mean())}

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
    spec = [("SGLCV", "SGLCV (this run)", BLUE, "s", "--", 0.94), ("uGLAD", "uGLAD, authors' code (this run)", RED, "^", "-.", 1.0)]
    if mine is not None:
        spec.append(("uGLAD-mine", "uGLAD, my implementation (this run)", GREEN, "*", ":", 1.065))
    for ax, metric in zip(axes, ("AUPR", "AUC")):
        for key, label, col, mk, ls, off in spec:
            m, s = stats(allr, key, metric)
            ax.errorbar(np.array(SIZES) * off, m, yerr=s, color=col, marker=mk, ls=ls, lw=1.0, ms=5.5 if mk != "*" else 8, capsize=2, elinewidth=0.6, label=label, zorder=4)
        for key, col, mk, lab in (("SGLCV", BLUE, "s", "Paper: SGLCV"), ("uGLAD", RED, "^", "Paper: uGLAD")):
            ax.plot(SIZES, PAPER[metric][key], color=col, marker=mk, mfc="white", ms=5, lw=0.7, ls=(0, (1, 2)), alpha=0.8, label=lab, zorder=3)
        ax.axhline(density if metric == "AUPR" else 0.5, color="black", lw=0.8, zorder=2)
        ax.set_xlabel("Number of samples  ($M$)")
        ax.set_ylabel("AUPR" if metric == "AUPR" else "AUC")
        log_axis(ax)
        ax.set_title("(a) precision-recall area" if metric == "AUPR" else "(b) ROC area", fontsize=10.62)
    axes[0].set_ylim(0.02, 0.36)
    axes[1].set_ylim(0.43, 0.72)
    axes[0].text(66, density - 0.006, "random ranking", fontsize=7.88, va="top", ha="right")
    axes[1].text(66, 0.497, "random ranking", fontsize=7.88, va="top", ha="right")
    better_arrow(axes[0], 0.965, 0.55, 0.88)
    better_arrow(axes[1], 0.965, 0.55, 0.88)
    emp = raw[raw.method == "uGLAD"].assign(empty=lambda d: d.n_pred_edges == 0).groupby("M").empty.sum()
    um, _ = stats(raw, "uGLAD", "AUPR")
    callout(axes[0], f"uGLAD returns an empty graph on\n{int(emp[25])}/{n_graphs} graphs at M=25 and {int(emp[50])}/{n_graphs} at M=50",
            (25 * 1.0, um[1]), (0.05, 0.80), ellipse=(0.14, 0.03))
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.24), fontsize=8.12)
    save(fig, "fig1_aupr_auc")
    ms = {k: stats(allr, k, "AUPR") for k in ("SGLCV", "uGLAD")}
    pa = raw[raw.method == "uGLAD"].set_index(["M", "graph"]).AUPR - raw[raw.method == "SGLCV"].set_index(["M", "graph"]).AUPR
    pt = {s: (pa.xs(s, level="M").mean(), pa.xs(s, level="M").mean() / (pa.xs(s, level="M").std() / np.sqrt(n_graphs))) for s in SIZES}
    every = ("SGLCV", "uGLAD") + (("uGLAD-mine",) if mine is not None else ())
    for metric in ("AUPR", "AUC"):
        num[metric + "_mean"] = {k: stats(allr, k, metric)[0].round(3).tolist() for k in every}
        num[metric + "_std"] = {k: stats(allr, k, metric)[1].round(3).tolist() for k in every}
    num["paired_AUPR_uGLAD_minus_SGLCV"] = {str(s): [round(float(pt[s][0]), 3), round(float(pt[s][1]), 2)] for s in SIZES}
    num["empty_uGLAD"] = {str(s): int(emp[s]) for s in SIZES}
    emp_s = raw[raw.method == "SGLCV"].assign(empty=lambda d: d.n_pred_edges == 0).groupby("M").empty.sum()
    num["empty_SGLCV"] = {str(s): int(emp_s[s]) for s in SIZES}
    gap_sg = np.abs(ms["SGLCV"][0] - np.array(PAPER["AUPR"]["SGLCV"])).max()
    gap_ug = ms["uGLAD"][0] - np.array(PAPER["AUPR"]["uGLAD"])
    cap["fig1"] = (f"Fig. 1: Edge recovery against the number of samples, mean and one standard deviation over {n_graphs} graphs (D = 25, p = 0.1), with the "
                   f"values printed in the uGLAD paper as dotted hollow markers. The SGLCV curve reproduces the published one: the largest AUPR difference is "
                   f"{gap_sg:.3f}, inside one standard deviation at every M. uGLAD run with the authors' code at its default settings does not: it is "
                   f"{np.abs(gap_ug).min():.3f} to {np.abs(gap_ug).max():.3f} below the published AUPR and, over the same graphs, differs from SGLCV by "
                   f"{pt[10][0]:+.3f}, {pt[25][0]:+.3f} and {pt[50][0]:+.3f} AUPR at M = 10, 25 and 50 (paired t = {pt[10][1]:.1f}, {pt[25][1]:.1f}, {pt[50][1]:.1f}).")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
    ax = axes[0]
    a = raw[raw.method == "SGLCV"].set_index(["M", "graph"]).AUPR
    b = raw[raw.method == "uGLAD"].set_index(["M", "graph"]).AUPR
    ax.fill_between([0, 0.6], [0, 0.6], [0.6, 0.6], color="#e8e8e8", zorder=0)
    ax.plot([0, 0.6], [0, 0.6], color="black", ls="--", lw=0.9, zorder=1)
    above = {}
    for s, col, mk in zip(SIZES, (BLUE, RED, GREEN), ("o", "^", "*")):
        x_, y_ = a.xs(s, level="M").values, b.xs(s, level="M").values
        ax.scatter(x_, y_, color=col, marker=mk, s=22 if mk != "*" else 38, label=f"$M$ = {s}", zorder=3, edgecolor="white", linewidth=0.3)
        above[s] = int((y_ > x_).sum())
    ax.set_xlim(0.03, 0.5)
    ax.set_ylim(0.03, 0.5)
    ax.set_xlabel("SGLCV  AUPR")
    ax.set_ylabel("uGLAD  AUPR  (authors' code)")
    ax.set_title("(a) one point per graph", fontsize=10.62)
    ax.text(0.06, 0.45, "shaded: uGLAD better", fontsize=8.12, va="center")
    ax.legend(loc="lower right")
    num["uGLAD_above_diagonal"] = {str(s): above[s] for s in SIZES}
    ax = axes[1]
    rng = np.random.default_rng(0)
    for key, col, mk, off in (("SGLCV", BLUE, "s", -0.045), ("uGLAD", RED, "^", 0.045)):
        for i, s in enumerate(SIZES):
            v = raw[(raw.method == key) & (raw.M == s)].n_pred_edges.values.astype(float)
            ax.scatter(i + off + rng.uniform(-0.03, 0.03, len(v)), v, color=col, marker=mk, s=12, alpha=0.7, zorder=3, linewidth=0)
            ax.hlines(v.mean(), i + off - 0.07, i + off + 0.07, color="black", lw=1.4, zorder=4)
        ax.scatter([], [], color=col, marker=mk, s=14, label=key)
    ax.axhline(raw.n_true_edges.mean(), color=GREEN, ls="--", lw=1.0, label="true graph (average)")
    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_ylim(-0.3, 2500)
    ax.set_yticks([0, 1, 10, 100])
    ax.set_yticklabels(["0", "1", "10", "100"])
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{s}" for s in SIZES])
    ax.set_xlim(-0.5, 2.5)
    ax.set_xlabel("Number of samples  ($M$)")
    ax.set_ylabel("Predicted edges")
    ax.set_title("(b) number of edges in the learned graph", fontsize=10.62)
    ax.legend(loc="upper right")
    ax.text(0.02, 0.95, "black bar = mean", transform=ax.transAxes, fontsize=7.88, va="top")
    save(fig, "fig2_paired_edges")
    cap["fig2"] = (f"Fig. 2: (a) AUPR of uGLAD against AUPR of SGLCV on the same graph, so a point above the dashed line is a graph where uGLAD wins; uGLAD is above the line on "
                   f"{above[10]}, {above[25]} and {above[50]} of {n_graphs} graphs at M = 10, 25 and 50. (b) Number of edges in the learned graph, one marker per graph "
                   f"(vertical axis linear up to 1, logarithmic above). uGLAD returns an empty graph {num['empty_uGLAD']['25']} and {num['empty_uGLAD']['50']} times out of {n_graphs} "
                   f"at M = 25 and 50, and about {raw[(raw.method == 'uGLAD') & (raw.M == 10)].n_pred_edges.mean():.0f} edges on average at M = 10, where the true graph has about "
                   f"{raw.n_true_edges.mean():.0f}.")

    mm, kk = 50, 0
    d = np.load(os.path.join(FOLDER, "matrices", f"M{mm}_g{kk}.npz"))
    tr = np.abs(d["theta_true"]) > 0
    np.fill_diagonal(tr, False)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7))

    def draw(ax, true_adj, pred_adj, title):
        n = true_adj.shape[0]
        g = nx.Graph()
        g.add_nodes_from(range(n))
        pos = nx.circular_layout(g)
        for i in range(n):
            for j in range(i + 1, n):
                t, p = bool(true_adj[i, j]), bool(pred_adj[i, j])
                if t and p:
                    nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color="black", width=1.5)
                elif p:
                    nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color=RED, width=0.7, style="dashed")
                elif t:
                    nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color="#9a9a9a", width=0.9, style="dotted")
        nx.draw_networkx_nodes(g, pos, ax=ax, node_color="white", edgecolors=RED, node_size=34, linewidths=0.8)
        ax.set_title(title, fontsize=9.38)
        ax.axis("off")
        ax.grid(False)

    draw(axes[0], tr, tr, f"True graph ({int(tr.sum() // 2)} edges)")
    cnt = {}
    for ax, name in zip(axes[1:], ("SGLCV", "uGLAD")):
        pr = np.abs(d["prec_" + name]) > 1e-10
        np.fill_diagonal(pr, False)
        tp, fp, fn = int((pr & tr).sum() // 2), int((pr & ~tr).sum() // 2), int((~pr & tr).sum() // 2)
        cnt[name] = (tp, fp, fn)
        draw(ax, tr, pr, f"{name}: {tp} correct, {fp} extra, {fn} missed".replace(": ", ":" + chr(10)))
    fig.text(0.5, 0.0, "solid black: correct edge     dashed red: extra edge     dotted gray: missed edge", ha="center", fontsize=8.75)
    save(fig, "fig3_example_graphs")
    num["example"] = {"M": mm, "graph": kk, **{k: list(v) for k, v in cnt.items()}}
    cap["fig3"] = (f"Fig. 3: One recovered graph. It is the first of the {n_graphs} graphs at the largest M (M = {mm}, graph index {kk}); the rule was fixed before looking, so it is not a picked example. The true graph has "
                   f"{int(tr.sum() // 2)} edges. SGLCV finds {cnt['SGLCV'][0]} of them and adds {cnt['SGLCV'][1]}; uGLAD finds {cnt['uGLAD'][0]} and adds {cnt['uGLAD'][1]}.")

    if kp is not None:
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
        specs = [("True model", "True model (best possible)", GREEN, "x", "-", 0.92), ("SGLCV", "SGLCV", BLUE, "s", "--", 0.97),
                 ("uGLAD", "uGLAD, authors' code", RED, "^", "-.", 1.03)]
        if "uGLAD-mine" in set(kp.method):
            specs.append(("uGLAD-mine", "uGLAD, my implementation", "#7a3fa0", "D", ":", 1.08))
        for ax, metric, ttl in zip(axes, ("NLL", "RMSE"), ("(a) held-out negative log likelihood", "(b) conditional prediction error")):
            for key, label, col, mk, ls, off in specs:
                g = kp[kp.method == key].groupby("M")[metric]
                ax.errorbar(np.array(SIZES) * off, [g.mean()[s] for s in SIZES], yerr=[g.std()[s] for s in SIZES], color=col, marker=mk, ls=ls, lw=1.0,
                            ms=5, capsize=2, elinewidth=0.6, label=label, zorder=4)
            ax.set_xlabel("Number of samples  ($M$)")
            ax.set_ylabel("NLL per test sample" if metric == "NLL" else "RMSE of the conditional mean")
            ax.set_title(ttl, fontsize=10.62)
            log_axis(ax)
            better_arrow(ax, 0.965, 0.88, 0.55, "lower is better")
        h, lab = axes[0].get_legend_handles_labels()
        fig.subplots_adjust(wspace=0.36)
        fig.legend(h, lab, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.24), fontsize=8.12)
        save(fig, "fig4_learning_inference")
        t = kp.groupby(["method", "M"])[["NLL", "RMSE"]].mean()
        num["NLL"] = {k: [round(float(t.loc[(k, s), "NLL"]), 2) for s in SIZES] for k in sorted(set(kp.method))}
        num["RMSE"] = {k: [round(float(t.loc[(k, s), "RMSE"]), 3) for s in SIZES] for k in sorted(set(kp.method))}
        cap["fig4"] = (f"Fig. 4: Learning and inference KPIs on {kp.groupby('M').graph.nunique().min()} test graphs per M, mean and one standard deviation, "
                       f"1000 fresh test samples per graph, all methods compared in the raw units of the data. (a) Held-out negative log likelihood; the green curve is the "
                       f"true model, so no method can go below it. (b) Error of the exact conditional mean of each variable given all the others. "
                       f"At M = 50 the gap to the true model is {num['NLL']['SGLCV'][2] - num['NLL']['True model'][2]:.1f} nats for SGLCV and "
                       f"{num['NLL']['uGLAD'][2] - num['NLL']['True model'][2]:.1f} for uGLAD, but the prediction error differs by only "
                       f"{num['RMSE']['SGLCV'][2] - num['RMSE']['True model'][2]:.3f} and {num['RMSE']['uGLAD'][2] - num['RMSE']['True model'][2]:.3f}.")

    if mine is not None:
        j = raw[raw.method == "uGLAD"].merge(mine, on=["M", "graph"], suffixes=("_off", "_mine"))
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
        rr = {}
        for ax, metric, lim in zip(axes, ("AUPR", "AUC"), ((0.03, 0.42), (0.40, 0.75))):
            ax.plot(lim, lim, color="black", ls="--", lw=0.9, label="equal", zorder=1)
            for s, col, mk in zip(SIZES, (BLUE, RED, GREEN), ("o", "^", "*")):
                q = j[j.M == s]
                ax.scatter(q[metric + "_off"], q[metric + "_mine"], color=col, marker=mk, s=22 if mk != "*" else 38, label=f"$M$ = {s}", zorder=3,
                           edgecolor="white", linewidth=0.3)
            r = np.corrcoef(j[metric + "_off"], j[metric + "_mine"])[0, 1]
            dd = (j[metric + "_mine"] - j[metric + "_off"]).abs()
            rr[metric] = (float(r), float(dd.mean()), float(dd.max()))
            ax.set_xlim(lim)
            ax.set_ylim(lim)
            ax.set_xlabel(f"{metric}, authors' code")
            ax.set_ylabel(f"{metric}, my implementation")
            ax.set_title(f"({'a' if metric == 'AUPR' else 'b'}) {metric}", fontsize=10.62)
            ax.text(0.04, 0.93, f"$r$ = {r:.2f}\nmean |diff| = {dd.mean():.3f}\nmax |diff| = {dd.max():.3f}", transform=ax.transAxes, fontsize=8.12, va="top",
                    bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="black", lw=0.6))
        axes[0].legend(loc="lower right")
        save(fig, "fig5_implementation_check")
        num["implementation_check"] = {k: list(v) for k, v in rr.items()}
        num["implementation_check"]["datasets"] = int(len(j))
        cap["fig5"] = (f"Fig. 5: My implementation against the authors' code on the same {len(j)} datasets with the same seeds. Each marker is one dataset. "
                       f"The two programs rank the node pairs alike: the correlation of AUPR is {rr['AUPR'][0]:.2f} and the mean absolute difference is {rr['AUPR'][1]:.3f} "
                       f"(largest {rr['AUPR'][2]:.3f}). They are close but not identical, because the matrix square root is computed differently.")

    import torch
    from data import make_dataset
    from uglad_model import classical_am, soft_threshold_np
    from validate import _independent_minimizer, _relaxed_objective

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
    ax = axes[0]
    x8, _ = make_dataset(8, 0.3, 300, seed=5)
    x8 = (x8 - x8.mean(axis=0)) / x8.std(axis=0)
    s8 = np.cov(x8, rowvar=False, bias=True) + 0.01 * np.eye(8)
    rho = 0.1
    worst = -np.inf
    for lam, col, mk, ls in ((0.5, BLUE, "s", "--"), (2.0, RED, "^", "-."), (8.0, GREEN, "o", ":")):
        th, zs = classical_am(s8, rho, lam, 400)
        f = np.array([_relaxed_objective(t, z, s8, rho, lam) for t, z in zip(th, zs)])
        ref = _independent_minimizer(s8, rho, lam)
        fref = _relaxed_objective(ref, soft_threshold_np(ref, rho / lam), s8, rho, lam)
        gap = np.maximum((f - fref) / abs(fref), 1e-16)
        worst = max(worst, float(np.diff(f).max()))
        it = np.arange(1, len(gap) + 1)
        ax.semilogy(it, gap, color=col, ls=ls, lw=1.0, label=f"Analytical steps, $\\lambda$ = {lam:g}")
        mark = np.unique(np.round(np.geomspace(1, len(gap), 12)).astype(int)) - 1
        ax.semilogy(it[mark], gap[mark], color=col, marker=mk, ls="none", ms=4.5)
    ax.set_xscale("log")
    ax.set_ylim(1e-16, 3)
    ax.set_xlabel("Iteration of the alternating steps")
    ax.set_ylabel("Relative gap to the L-BFGS minimum")
    ax.set_title("(a) the $\\Theta$ and $Z$ steps", fontsize=10.62)
    ax.legend(loc="lower left")
    callout(ax, f"never increases:\nlargest single-step\nrise {worst:.0e}", (30, 1e-6), (0.52, 0.8))
    num["am_largest_increase"] = worst
    ax = axes[1]
    x25, th25 = make_dataset(25, 0.1, 400000, seed=21)
    xc = x25 - x25.mean(axis=0)
    coef_formula, coef_mc = [], []
    for i in range(25):
        others = [k for k in range(25) if k != i]
        beta = np.linalg.lstsq(xc[:, others], xc[:, i], rcond=None)[0]
        coef_mc.extend(beta.tolist())
        coef_formula.extend((-th25[i, others] / th25[i, i]).tolist())
    cf, cm = np.array(coef_formula), np.array(coef_mc)
    lim = (cf.min() - 0.05, cf.max() + 0.05)
    ax.plot(lim, lim, color="black", ls="--", lw=0.9, label="equal", zorder=1)
    ax.scatter(cf, cm, color=RED, marker="^", s=7, alpha=0.6, linewidth=0, label=f"Simulation, {len(cf)} coefficients", zorder=3)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Closed form  $-\\Theta_{ij}/\\Theta_{ii}$")
    ax.set_ylabel("Regression on 400000 samples")
    ax.set_title("(b) inference: conditional mean", fontsize=10.62)
    ax.legend(loc="upper left")
    mx = float(np.abs(cf - cm).max())
    ax.text(0.97, 0.05, f"max error {mx:.4f}", transform=ax.transAxes, fontsize=8.12, ha="right",
            bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="black", lw=0.6))
    num["conditional_mean_max_error"] = mx
    save(fig, "fig6_mathematics")
    cap["fig6"] = (f"Fig. 6: The mathematics checked against independent references. (a) The alternating steps used inside uGLAD, run with three coupling weights on a D = 8 problem: the "
                   f"objective never rises (largest single-step increase {worst:.0e}) and reaches the minimum found by a generic optimizer (L-BFGS). (b) The closed-form coefficient "
                   f"$-\\Theta_{{ij}}/\\Theta_{{ii}}$ of the conditional mean against the coefficient fitted by regression on 400000 simulated samples; the largest difference over "
                   f"{len(cf)} coefficients is {mx:.4f}.")

    json.dump(cap, open(os.path.join(OUT, "captions.json"), "w"), indent=1)
    json.dump(num, open(os.path.join(OUT, "numbers.json"), "w"), indent=1)
    print("done", sorted(cap))


if __name__ == "__main__":
    main()
