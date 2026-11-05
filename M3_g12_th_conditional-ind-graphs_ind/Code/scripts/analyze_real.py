"""Tables and figures for DREAM3 (paper Table 2) and Netsim (paper Table 3) from results/*.json.

AUROC of the summary graph: mean, standard error (as in the paper), standard deviation, n and a 95 % t-interval.
Baselines that the paper quotes from Khanna and Tan (2019) are NOT re-run. They are shown as quoted values.
Run:  rhino_env\\venv\\Scripts\\python.exe -I scripts\\analyze_real.py
Outputs (analysis_out/): real_netsim_auroc.csv, real_dream3_auroc.csv, fig_netsim_auroc.png, fig_dream3_auroc.png
"""
import glob
import json
import math
import os
from collections import defaultdict

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats as sps

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis_out")
os.makedirs(OUT, exist_ok=True)
NETS = ["ecoli1", "ecoli2", "yeast1", "yeast2", "yeast3"]
NET_LABEL = {"ecoli1": "E. coli 1", "ecoli2": "E. coli 2", "yeast1": "Yeast 1", "yeast2": "Yeast 2", "yeast3": "Yeast 3"}

# Values printed in the paper (Tables 2 and 3). "quoted" = copied by the authors from Khanna and Tan (2019).
QUOTED_NETSIM = {"cMLP": 0.93, "cLSTM": 0.83, "TCDF": 0.91, "SRU": 0.80, "eSRU": 0.88}
QUOTED_DREAM3 = {"cMLP": [0.644, 0.568, 0.585, 0.506, 0.528], "cLSTM": [0.629, 0.609, 0.579, 0.519, 0.555],
                 "TCDF": [0.614, 0.647, 0.581, 0.556, 0.557], "SRU": [0.657, 0.666, 0.617, 0.575, 0.55],
                 "eSRU": [0.66, 0.629, 0.627, 0.557, 0.55]}
PAPER_NETSIM = {"dynotears": 0.90, "pcmci_plus": 0.83, "varlingam": 0.84, "rhino_g": 0.974, "rhino_noinst": 0.93, "rhino": 0.99}
PAPER_DREAM3 = {"dynotears": [0.590, 0.547, 0.527, 0.526, 0.510], "pcmci_plus": [0.530, 0.519, 0.530, 0.510, 0.512],
                "rhino_g": [0.673, 0.665, 0.659, 0.598, 0.588], "rhino": [0.685, 0.680, 0.664, 0.585, 0.567]}
LABEL = {"dynotears": "DYNOTEARS", "pcmci_plus": "PCMCI+", "varlingam": "VAR-LiNGAM", "rhino_g": "Rhino+g", "rhino_noinst": "Rhino+NoInst",
         "rhino": "Rhino"}
COLOR = {"rhino": "#2a78d6", "rhino_g": "#eb6834", "dynotears": "#eda100", "varlingam": "#e87ba4", "pcmci_plus": "#008300",
         "rhino_noinst": "#6250d6"}
SURF, INK, INK2, GRID, AXIS, QCOL = "#fcfcfb", "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7", "#898781"


def stats(v):
    n = len(v)
    m = float(np.mean(v))
    if n < 2:
        return m, float("nan"), float("nan"), n, float("nan"), float("nan")
    sd = float(np.std(v, ddof=1))
    se = sd / math.sqrt(n)
    h = sps.t.ppf(0.975, n - 1) * se
    return m, se, sd, n, m - h, m + h


def collect(prefix):
    g = defaultdict(list)
    bad = []
    for f in glob.glob(os.path.join(ROOT, "results", prefix + "*.json")):
        r = json.load(open(f))
        if r["status"] != "ok":
            bad.append((r["job_id"], r["status"]))
            continue
        a = r.get("metrics", {}).get("auroc_agg")
        if a is not None:
            g[(r["method"], r["dataset"])].append(a)
    return g, bad


def split_method(m):
    """netsim_rhino_g_paper -> ('rhino_g', 'paper'); dream3_dynotears -> ('dynotears', 'baseline')"""
    body = m.split("_", 1)[1]
    for suf in ("_paper", "_shipped"):
        if body.endswith(suf):
            return body[: -len(suf)], suf[1:]
    return body, "baseline"


def dot_axis(ax, rows, xlim):
    """rows: list of dict(label, ours, ours_ci, released, paper, quoted)."""
    y = np.arange(len(rows))[::-1]
    for yi, r in zip(y, rows):
        col = COLOR.get(r.get("key"), QCOL)
        if r.get("quoted") is not None:
            ax.plot(r["quoted"], yi, "s", color=QCOL, markersize=6, zorder=3)
        if r.get("ours") is not None:
            lo, hi = r.get("ours_ci", (np.nan, np.nan))
            if not np.isnan(lo):
                ax.plot([lo, hi], [yi, yi], color=col, linewidth=2, zorder=2)
            ax.plot(r["ours"], yi, "o", color=col, markersize=7, markeredgecolor=SURF, markeredgewidth=1, zorder=3)
        if r.get("released") is not None:
            ax.plot(r["released"], yi + 0.22, "^", color=col, markersize=6, markeredgecolor=SURF, markeredgewidth=0.8, zorder=3)
        if r.get("paper") is not None:
            ax.plot(r["paper"], yi - 0.22, "D", markerfacecolor=SURF, markeredgecolor=INK, markersize=6, markeredgewidth=1.2, zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] for r in rows], fontsize=8, color=INK2)
    ax.set_xlim(*xlim)
    ax.set_facecolor(SURF)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=8)


def legend(fig):
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", color=INK2, linestyle="-", markersize=7, label="Ours, paper settings (mean, 95 % interval)"),
         Line2D([], [], marker="^", color=INK2, linestyle="", markersize=6, label="Ours, released config (mean)"),
         Line2D([], [], marker="D", markerfacecolor=SURF, markeredgecolor=INK, color=INK, linestyle="", markersize=6, label="Value printed in the paper"),
         Line2D([], [], marker="s", color=QCOL, linestyle="", markersize=6, label="Quoted by the paper (Khanna and Tan 2019), not re-run")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, fontsize=8, labelcolor=INK2)


def netsim():
    g, bad = collect("netsim_")
    rows, table = [], []
    for name, v in QUOTED_NETSIM.items():
        rows.append(dict(label=name, quoted=v))
        table.append(dict(method=name, variant="quoted from Khanna and Tan (2019)", n=0, mean=v, paper_value=v))
    for key in ("dynotears", "pcmci_plus", "varlingam", "rhino_noinst", "rhino_g", "rhino"):
        row = dict(label=LABEL[key], key=key, paper=PAPER_NETSIM[key])
        for (m, ds), v in g.items():
            k, var = split_method(m)
            if k != key:
                continue
            mean, se, sd, n, lo, hi = stats(v)
            table.append(dict(method=LABEL[key], variant=var, n=n, mean=mean, se=se, sd=sd, ci_lo=lo, ci_hi=hi, paper_value=PAPER_NETSIM[key]))
            if var in ("paper", "baseline"):
                row["ours"], row["ours_ci"] = mean, (lo, hi)
            else:
                row["released"] = mean
        rows.append(row)
    pd.DataFrame(table).to_csv(os.path.join(OUT, "real_netsim_auroc.csv"), index=False)
    print("NETSIM AUROC\n", pd.DataFrame(table).round(3).to_string(index=False), "\nnon-ok:", bad)
    fig, ax = plt.subplots(figsize=(6.6, 4.6), facecolor=SURF)
    dot_axis(ax, rows, (0.7, 1.0))
    ax.set_xlabel("AUROC of the summary graph (Netsim Sim-3, self-connections counted)", color=INK2, fontsize=9)
    legend(fig)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(os.path.join(OUT, "fig_netsim_auroc.png"), dpi=200, facecolor=SURF, bbox_inches="tight")
    plt.close(fig)


def dream3():
    g, bad = collect("dream3_")
    table = []
    fig, axes = plt.subplots(1, 5, figsize=(15, 4.4), facecolor=SURF, sharey=True)
    for i, (ax, net) in enumerate(zip(axes, NETS)):
        rows = []
        for name, v in QUOTED_DREAM3.items():
            rows.append(dict(label=name, quoted=v[i]))
            table.append(dict(network=net, method=name, variant="quoted from Khanna and Tan (2019)", n=0, mean=v[i], paper_value=v[i]))
        for key in ("dynotears", "pcmci_plus", "rhino_g", "rhino"):
            row = dict(label=LABEL[key], key=key, paper=PAPER_DREAM3[key][i])
            for (m, ds), v in g.items():
                k, var = split_method(m)
                if k != key or ds != f"dream3_100_{net}":
                    continue
                mean, se, sd, n, lo, hi = stats(v)
                table.append(dict(network=net, method=LABEL[key], variant=var, n=n, mean=mean, se=se, sd=sd, ci_lo=lo, ci_hi=hi,
                                  paper_value=PAPER_DREAM3[key][i]))
                if var in ("paper", "baseline"):
                    row["ours"], row["ours_ci"] = mean, (lo, hi)
                else:
                    row["released"] = mean
            rows.append(row)
        dot_axis(ax, rows, (0.45, 0.75))
        ax.set_title(NET_LABEL[net], color=INK, fontsize=10, loc="left")
        ax.set_xlabel("AUROC", color=INK2, fontsize=9)
    pd.DataFrame(table).to_csv(os.path.join(OUT, "real_dream3_auroc.csv"), index=False)
    d = pd.DataFrame(table)
    print("DREAM3 AUROC\n", d[d.n > 0].round(3).to_string(index=False) if (d.n > 0).any() else "no DREAM3 results yet", "\nnon-ok:", bad)
    legend(fig)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(os.path.join(OUT, "fig_dream3_auroc.png"), dpi=200, facecolor=SURF, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    netsim()
    dream3()
