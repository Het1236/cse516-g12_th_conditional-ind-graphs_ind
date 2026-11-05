"""Statistics and figures for the synthetic experiments (paper Section 6.1, Fig 1, 3, 4, 5; Appendix F.3).

Reads results/*.json (status ok) and writes tables (CSV) and figures (PNG) into analysis_out/.
  rhino_env\\venv\\Scripts\\python.exe -I scripts\\analyze_synth.py [--f1 orientation|adjacency]

Tables:  synth_summary_<f1>.csv    mean, sd, 95 % t-interval per dimension, method and metric
         synth_paired_<f1>.csv     paired comparison Rhino vs every other method (same dataset), Wilcoxon signed-rank, Holm-adjusted
         synth_factors_<f1>.csv    temporal F1 by graph type, instantaneous effects and history dependence
         synth_runtime.csv         wall time per method and dimension
Units: one row = one dataset (dimension x graph type x instantaneous x history x seed). 40 datasets per dimension.
"""
import argparse
import glob
import json
import math
import os

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis_out")
os.makedirs(OUT, exist_ok=True)

ORDER = ["rhino", "rhino_g", "rhino_s", "dynotears", "varlingam", "pcmci_plus"]
LABEL = {"rhino": "Rhino (L=2)", "rhino_g": "Rhino+g (L=2)", "rhino_s": "Rhino+s (L=2)", "dynotears": "DYNOTEARS",
         "varlingam": "VAR-LiNGAM", "pcmci_plus": "PCMCI+", "rhino_shipped": "Rhino, released lambda_s=5",
         "rhino_lag1": "Rhino (L=1)", "rhino_lag3": "Rhino (L=3)"}
# fixed categorical slots 1-6 of the reference palette (one colour per method in every figure)
COLOR = dict(zip(ORDER, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]))
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"


def load():
    rows = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
        r = json.load(open(f))
        if r.get("seed", "") in ("", None) or r.get("status") != "ok":
            continue
        m = r["metrics"]
        row = dict(method=r["method"], dim=int(r["dim"]), gtype=r["gtype"], inst=int(r["inst"]), hist=int(r["hist"]),
                   seed=int(r["seed"]), dataset=r["dataset"], wall_min=r["wall_seconds"] / 60)
        for k in ("orientation", "adjacency"):
            for part, key in (("inst", "inst"), ("lag", "lag"), ("temporal", "overall_temporal")):
                row[f"{k}_{part}"] = m.get(f"{k}_fscore_{key}", np.nan)
        row["shd_temporal"] = m.get("shd_overall_temporal", np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def ci95(v):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    n = len(v)
    if n < 2:
        return n, (v.mean() if n else np.nan), np.nan, np.nan, np.nan
    m, sd = v.mean(), v.std(ddof=1)
    h = stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
    return n, m, sd, m - h, m + h


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(p) - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def summary(df, f1):
    rows = []
    for dim in sorted(df.dim.unique()):
        for m in ORDER:
            d = df[(df.dim == dim) & (df.method == m)]
            if d.empty:
                continue
            for part in ("inst", "lag", "temporal"):
                x = d[d.inst == 1] if part == "inst" else d
                n, mean, sd, lo, hi = ci95(x[f"{f1}_{part}"])
                rows.append(dict(dim=dim, method=m, metric=f"F1_{part}", n=n, mean=mean, sd=sd, ci_lo=lo, ci_hi=hi))
            n, mean, sd, lo, hi = ci95(d["shd_temporal"])
            rows.append(dict(dim=dim, method=m, metric="SHD_temporal", n=n, mean=mean, sd=sd, ci_lo=lo, ci_hi=hi))
    return pd.DataFrame(rows)


def paired(df, f1, ref="rhino"):
    rows = []
    for dim in sorted(df.dim.unique()):
        for part in ("inst", "lag", "temporal"):
            col = f"{f1}_{part}"
            sub = df[(df.dim == dim) & ((df.inst == 1) if part == "inst" else True)]
            wide = sub.pivot_table(index="dataset", columns="method", values=col)
            if ref not in wide:
                continue
            res = []
            for m in [x for x in ORDER if x != ref and x in wide]:
                pair = wide[[ref, m]].dropna()
                diff = pair[ref] - pair[m]
                n = len(diff)
                if n < 3:
                    continue
                mean = diff.mean()
                h = stats.t.ppf(0.975, n - 1) * diff.std(ddof=1) / math.sqrt(n)
                try:
                    p = stats.wilcoxon(diff, zero_method="wilcox").pvalue if (diff != 0).any() else 1.0
                except ValueError:
                    p = 1.0
                res.append(dict(dim=dim, metric=f"F1_{part}", other=m, n=n, mean_diff=mean, ci_lo=mean - h, ci_hi=mean + h,
                                wins=int((diff > 0).sum()), ties=int((diff == 0).sum()), losses=int((diff < 0).sum()), p_wilcoxon=p))
            if res:
                adj = holm([r["p_wilcoxon"] for r in res])
                for r, a in zip(res, adj):
                    r["p_holm"] = a
                rows += res
    return pd.DataFrame(rows)


def factors(df, f1):
    rows = []
    for dim in sorted(df.dim.unique()):
        for fac, name in (("gtype", "graph"), ("inst", "inst"), ("hist", "hist")):
            for lvl in sorted(df[fac].unique()):
                for m in ORDER:
                    d = df[(df.dim == dim) & (df.method == m) & (df[fac] == lvl)]
                    if d.empty:
                        continue
                    n, mean, sd, lo, hi = ci95(d[f"{f1}_temporal"])
                    rows.append(dict(dim=dim, factor=name, level=lvl, method=m, n=n, mean=mean, sd=sd, ci_lo=lo, ci_hi=hi))
    return pd.DataFrame(rows)


def style(ax):
    ax.set_facecolor(SURF)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=8)


def grouped_bars(ax, groups, series_means, series_lo, series_hi, methods, ylabel=None, title=None):
    k = len(methods)
    w = 0.8 / k
    x = np.arange(len(groups))
    for i, m in enumerate(methods):
        mu, lo, hi = series_means[m], series_lo[m], series_hi[m]
        xs = x - 0.4 + w * (i + 0.5)
        ax.bar(xs, mu, width=w, color=COLOR[m], edgecolor=SURF, linewidth=1.0, label=LABEL[m], zorder=2)
        ok = ~np.isnan(lo)
        ax.errorbar(xs[ok], np.asarray(mu)[ok], yerr=[np.asarray(mu)[ok] - np.asarray(lo)[ok], np.asarray(hi)[ok] - np.asarray(mu)[ok]],
                    fmt="none", ecolor=INK2, elinewidth=0.8, capsize=1.5, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylim(0, 1.0)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK2, fontsize=9)
    if title:
        ax.set_title(title, color=INK, fontsize=10, loc="left")
    style(ax)


def fig_main(df, f1, tag):
    dims = sorted(df.dim.unique())
    fig, axes = plt.subplots(1, len(dims), figsize=(4.2 * len(dims), 3.6), facecolor=SURF, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, dim in zip(axes, dims):
        mu, lo, hi = {}, {}, {}
        for m in ORDER:
            a, b, c = [], [], []
            for part in ("inst", "lag", "temporal"):
                d = df[(df.dim == dim) & (df.method == m)]
                d = d[d.inst == 1] if part == "inst" else d
                n, mean, sd, l, h = ci95(d[f"{f1}_{part}"])
                a.append(mean), b.append(l), c.append(h)
            mu[m], lo[m], hi[m] = a, b, c
        grouped_bars(ax, ["Inst.", "Lag", "Temporal"], mu, lo, hi, ORDER, "F1" if dim == dims[0] else None, f"Dim = {dim}")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, frameon=False, fontsize=8, labelcolor=INK2)
    fig.suptitle(f"{f1.capitalize()} F1 on synthetic data, mean and 95 % interval over datasets", color=INK, fontsize=10, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(os.path.join(OUT, f"fig_synth_main_{tag}.png"), dpi=200, facecolor=SURF)
    plt.close(fig)


def fig_factor(df, f1, factor, labels, fname, title):
    dims = sorted(df.dim.unique())
    levels = sorted(df[factor].unique())
    fig, axes = plt.subplots(1, len(dims), figsize=(4.2 * len(dims), 3.6), facecolor=SURF, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, dim in zip(axes, dims):
        mu, lo, hi = {}, {}, {}
        for m in ORDER:
            a, b, c = [], [], []
            for lvl in levels:
                n, mean, sd, l, h = ci95(df[(df.dim == dim) & (df.method == m) & (df[factor] == lvl)][f"{f1}_temporal"])
                a.append(mean), b.append(l), c.append(h)
            mu[m], lo[m], hi[m] = a, b, c
        grouped_bars(ax, [labels[l] for l in levels], mu, lo, hi, ORDER, "Temporal F1" if dim == dims[0] else None, f"Dim = {dim}")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, frameon=False, fontsize=8, labelcolor=INK2)
    fig.suptitle(title, color=INK, fontsize=10, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(os.path.join(OUT, fname), dpi=200, facecolor=SURF)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--f1", choices=["orientation", "adjacency"], default="orientation")
    a = ap.parse_args()
    df = load()
    df = df[df.method.isin(ORDER) & df.dim.isin([5, 10, 20])]
    print(len(df), "results;", df.groupby(["dim", "method"]).size().unstack().to_string())
    tag = a.f1
    summary(df, tag).to_csv(os.path.join(OUT, f"synth_summary_{tag}.csv"), index=False)
    paired(df, tag).to_csv(os.path.join(OUT, f"synth_paired_{tag}.csv"), index=False)
    factors(df, tag).to_csv(os.path.join(OUT, f"synth_factors_{tag}.csv"), index=False)
    rt = df.groupby(["dim", "method"]).wall_min.agg(["count", "median", "mean", "max"]).reset_index()
    rt.to_csv(os.path.join(OUT, "synth_runtime.csv"), index=False)
    fig_main(df, tag, tag)
    fig_factor(df, tag, "gtype", {"ER": "ER", "SF": "SF"}, f"fig_synth_graphtype_{tag}.png", f"Temporal {tag} F1 by graph type")
    fig_factor(df, tag, "hist", {0: "No hist.-dep.", 1: "Hist.-dep."}, f"fig_synth_history_{tag}.png", f"Temporal {tag} F1 by history dependence of the noise")
    fig_factor(df, tag, "inst", {0: "No inst.", 1: "Inst. effects"}, f"fig_synth_inst_{tag}.png", f"Temporal {tag} F1 by instantaneous effects")
    print("written to", OUT)


if __name__ == "__main__":
    main()
