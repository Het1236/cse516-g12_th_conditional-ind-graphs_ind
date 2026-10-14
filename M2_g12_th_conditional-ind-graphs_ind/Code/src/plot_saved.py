import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd


def draw(ax, true_adj, pred_adj, title):
    d = true_adj.shape[0]
    g = nx.Graph()
    g.add_nodes_from(range(d))
    pos = nx.circular_layout(g)
    for i in range(d):
        for j in range(i + 1, d):
            t, p = bool(true_adj[i, j]), bool(pred_adj[i, j])
            if t and p:
                nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color="black", width=1.6)
            elif p:
                nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color="#7D1916", width=0.6, style="dashed", alpha=0.6)
            elif t:
                nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color="#999999", width=1.2, style="dotted")
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color="white", edgecolors="#7D1916", node_size=90)
    ax.set_title(title, fontsize=9)
    ax.axis("off")


def graph_plot(folder, m, k):
    d = np.load(os.path.join(folder, "matrices", f"M{m}_g{k}.npz"))
    tr = np.abs(d["theta_true"]) > 0
    np.fill_diagonal(tr, False)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.6))
    draw(axes[0], tr, tr, f"True graph ({int(tr.sum() // 2)} edges)")
    for ax, name in zip(axes[1:], ("SGLCV", "uGLAD")):
        pr = np.abs(d["prec_" + name]) > 1e-10
        np.fill_diagonal(pr, False)
        tp, fp, fn = int((pr & tr).sum() // 2), int((pr & ~tr).sum() // 2), int((~pr & tr).sum() // 2)
        draw(ax, tr, pr, f"{name}: {tp} correct, {fp} extra, {fn} missed")
    fig.text(0.5, 0.02, f"M = {m}, graph {k}.  black = correct, dashed maroon = extra, dotted gray = missed", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    out = os.path.join(folder, f"graphs_M{m}_g{k}.png")
    fig.savefig(out, dpi=170)
    return out


def boxplot(folder):
    df = pd.read_csv(os.path.join(folder, "table1_raw.csv"))
    sizes = sorted(df.M.unique())
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for ax, metric in zip(axes, ("AUPR", "AUC")):
        for j, (m, color) in enumerate((("SGLCV", "black"), ("uGLAD", "#7D1916"))):
            data = [df[(df.method == m) & (df.M == s)][metric].values for s in sizes]
            pos = [i * 3 + j for i in range(len(sizes))]
            bp = ax.boxplot(data, positions=pos, widths=0.8, patch_artist=True)
            for b in bp["boxes"]:
                b.set_facecolor(color)
                b.set_alpha(0.35)
            ax.plot([], [], color=color, label=m)
        ax.set_xticks([i * 3 + 0.5 for i in range(len(sizes))])
        ax.set_xticklabels([f"M={s}" for s in sizes])
        ax.set_ylabel(metric)
        ax.grid(alpha=0.25)
    axes[0].legend()
    fig.tight_layout()
    out = os.path.join(folder, "boxplot_aupr_auc.png")
    fig.savefig(out, dpi=170)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--m", type=int)
    ap.add_argument("--graph", type=int)
    ap.add_argument("--boxplot", action="store_true")
    a = ap.parse_args()
    if a.m is not None and a.graph is not None:
        print(graph_plot(a.folder, a.m, a.graph))
    if a.boxplot:
        print(boxplot(a.folder))
