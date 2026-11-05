"""Table 1 (lag ablation), Fig 2 (treatment effects) and Fig 8 (AUROC / F1 / validation likelihood during training).

  rhino_env\\venv\\Scripts\\python.exe -I scripts\\analyze_extra.py lag     # Table 1
  rhino_env\\venv\\Scripts\\python.exe -I scripts\\analyze_extra.py te      # Fig 2
  rhino_env\\venv\\Scripts\\python.exe -I scripts\\analyze_extra.py fig8    # Fig 8 (needs the 60-step Netsim runs)
Outputs go to analysis_out/.
LL in Table 1 = last logged training log p(x|A) of the run (logs/<job>.log). ASSUMPTION: the paper does not say how its LL is computed.
"""
import glob
import hashlib
import json
import math
import os
import re
import sys

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis_out")
os.makedirs(OUT, exist_ok=True)
SURF, INK, INK2, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj, run = np.empty_like(p), 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(p) - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def style(ax):
    ax.set_facecolor(SURF)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=8)


def last_ll(jid):
    path = os.path.join(ROOT, "logs", jid + ".log")
    last = np.nan
    if os.path.isfile(path):
        for line in open(path, errors="ignore"):
            m = re.search(r"log p\(x\|A\): (-?\d+\.?\d*)", line)
            if m:
                last = float(m.group(1))
    return last


def lag_table():
    rows = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
        r = json.load(open(f))
        if r.get("method") not in ("rhino", "rhino_lag1", "rhino_lag3") or r.get("status") != "ok" or r.get("seed", "") == "":
            continue
        m = r["metrics"]
        rows.append(dict(method=r["method"], dim=int(r["dim"]), inst=int(r["inst"]), dataset=r["dataset"],
                         F1_inst=m.get("orientation_fscore_inst", np.nan), F1_lag=m.get("orientation_fscore_lag", np.nan),
                         F1_temporal=m.get("orientation_fscore_overall_temporal", np.nan), LL=last_ll(r["job_id"])))
    df = pd.DataFrame(rows)
    names = {"rhino_lag1": "L=1", "rhino": "L=2", "rhino_lag3": "L=3"}
    out, tests = [], []
    for dim in sorted(df.dim.unique()):
        for m in ["rhino_lag1", "rhino", "rhino_lag3"]:
            d = df[(df.dim == dim) & (df.method == m)]
            if d.empty:
                continue
            cell = dict(dim=dim, lag=names[m], n=len(d))
            for k in ("F1_inst", "F1_lag", "F1_temporal", "LL"):
                x = (d[d.inst == 1] if k == "F1_inst" else d)[k].dropna()
                cell[k] = f"{x.mean():.2f} +- {x.std(ddof=1):.2f}"
                cell[k + "_mean"] = x.mean()
            out.append(cell)
        wide = {k: df[df.dim == dim].pivot_table(index="dataset", columns="method", values=k) for k in ("F1_temporal", "LL")}
        for k, w in wide.items():
            res = []
            for other in ("rhino_lag1", "rhino_lag3"):
                if other in w and "rhino" in w:
                    pair = w[["rhino", other]].dropna()
                    diff = pair["rhino"] - pair[other]
                    if len(diff) >= 3 and (diff != 0).any():
                        h = stats.t.ppf(0.975, len(diff) - 1) * diff.std(ddof=1) / math.sqrt(len(diff))
                        res.append(dict(dim=dim, metric=k, comparison=f"L=2 minus {names[other]}", n=len(diff), mean_diff=diff.mean(),
                                        ci_lo=diff.mean() - h, ci_hi=diff.mean() + h, p_wilcoxon=stats.wilcoxon(diff).pvalue))
            for r, a in zip(res, holm([r["p_wilcoxon"] for r in res]) if res else []):
                r["p_holm"] = a
            tests += res
    pd.DataFrame(out).to_csv(os.path.join(OUT, "table1_lag_ablation.csv"), index=False)
    pd.DataFrame(tests).to_csv(os.path.join(OUT, "table1_lag_paired_tests.csv"), index=False)
    print(pd.DataFrame(out)[["dim", "lag", "n", "F1_inst", "F1_lag", "F1_temporal", "LL"]].to_string(index=False))
    print(pd.DataFrame(tests).round(4).to_string(index=False) if tests else "no paired tests yet")


def te_fig():
    rows = []
    for f in glob.glob(os.path.join(ROOT, "results_te", "*.json")):
        r = json.load(open(f))
        if r.get("status") != "ok":
            continue
        a = r["te"]["all interventions"]
        rows.append(dict(method=r["method"], dim=int(r["dim"]), dataset=r["dataset"], ate=a["ATE RMSE"], ml_ate=a["ML ATE RMSE"]))
    df = pd.DataFrame(rows)
    if df.empty:
        print("no treatment-effect results yet")
        return
    df.to_csv(os.path.join(OUT, "te_per_dataset.csv"), index=False)
    summ = []
    for (dim, m), d in df.groupby(["dim", "method"]):
        for col, name in (("ate", "E[ATE]"), ("ml_ate", "ML ATE")):
            x = d[col]
            h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / math.sqrt(len(x)) if len(x) > 1 else np.nan
            summ.append(dict(dim=dim, method=m, estimator=name, n=len(x), mean_rmse=x.mean(), sd=x.std(ddof=1), median=x.median(),
                             ci_lo=x.mean() - h, ci_hi=x.mean() + h))
    pd.DataFrame(summ).to_csv(os.path.join(OUT, "te_summary.csv"), index=False)
    print(pd.DataFrame(summ).round(3).to_string(index=False))
    dims = sorted(df.dim.unique())
    cols = {"rhino": BLUE, "rhino_g": ORANGE, "rhino_s": AQUA}
    lab = {"rhino": "Rhino (L=2)", "rhino_g": "Rhino+g (L=2)", "rhino_s": "Rhino+s (L=2)"}
    fig, axes = plt.subplots(1, len(dims), figsize=(4.2 * len(dims), 3.6), facecolor=SURF, sharey=False)
    axes = np.atleast_1d(axes)
    for ax, dim in zip(axes, dims):
        pos, k = 0, 0
        for est, col in (("E[ATE]", "ate"), ("ML ATE", "ml_ate")):
            for m in cols:
                x = df[(df.dim == dim) & (df.method == m)][col]
                if x.empty:
                    continue
                bp = ax.boxplot(x, positions=[pos], widths=0.7, patch_artist=True, showfliers=True, manage_ticks=False,
                                medianprops=dict(color=INK, linewidth=1), whiskerprops=dict(color=INK2, linewidth=0.8),
                                capprops=dict(color=INK2, linewidth=0.8), flierprops=dict(marker="o", markersize=2, markeredgecolor=INK2))
                bp["boxes"][0].set(facecolor=cols[m], edgecolor=SURF, linewidth=1)
                if est == "E[ATE]" or True:
                    pass
                pos += 1
            pos += 1
        ax.set_xticks([1, 5])
        ax.set_xticklabels(["E[ATE]", "ML ATE"])
        ax.set_title(f"Dim = {dim}", color=INK, fontsize=10, loc="left")
        if dim == dims[0]:
            ax.set_ylabel("RMSE of the average treatment effect", color=INK2, fontsize=9)
        style(ax)
    handles = [plt.Rectangle((0, 0), 1, 1, color=cols[m]) for m in cols]
    fig.legend(handles, [lab[m] for m in cols], loc="lower center", ncol=3, frameon=False, fontsize=8, labelcolor=INK2)
    fig.suptitle("Treatment effect error on synthetic data (lower is better), one box = datasets of one dimension", color=INK, fontsize=10, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.savefig(os.path.join(OUT, "fig2_treatment_effect_rmse.png"), dpi=200, facecolor=SURF)
    plt.close(fig)


def fig8(prefix="netsim_rhino_shipped"):
    curves = {"auroc_agg": [], "orientation_fscore_agg": [], "val_likelihood": []}
    for f in glob.glob(os.path.join(ROOT, "results", prefix + "__s*.json")):
        r = json.load(open(f))
        if r["status"] != "ok":
            continue
        h = hashlib.md5(r["job_id"].encode()).hexdigest()[:10]
        hits = glob.glob(os.path.join(ROOT, "runs", h, "*", "models", "*", "metrics.json"))
        if not hits:
            continue
        m = json.load(open(hits[0]))
        for k in curves:
            curves[k].append([x if x is not None else np.nan for x in m[k]])
    n = min((len(v) for v in curves["auroc_agg"]), default=0)
    if n == 0:
        print("no finished runs for", prefix)
        return
    arr = {k: np.array([v[:n] for v in vs], float) for k, vs in curves.items()}
    steps = np.arange(n)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.2, 5.2), facecolor=SURF, sharex=True, gridspec_kw=dict(height_ratios=[3, 2]))
    for k, col, lab in (("auroc_agg", BLUE, "AUROC"), ("orientation_fscore_agg", ORANGE, "Orientation F1")):
        mu, sd = np.nanmean(arr[k], 0), np.nanstd(arr[k], 0, ddof=1) if len(arr[k]) > 1 else np.zeros(n)
        a1.plot(steps, mu, color=col, linewidth=2, label=lab)
        a1.fill_between(steps, mu - sd, mu + sd, color=col, alpha=0.15, linewidth=0)
    a1.set_ylim(0, 1.0)
    a1.set_ylabel("Score", color=INK2, fontsize=9)
    a1.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="lower right")
    mu, sd = np.nanmean(arr["val_likelihood"], 0), np.nanstd(arr["val_likelihood"], 0, ddof=1) if len(arr["val_likelihood"]) > 1 else np.zeros(n)
    a2.plot(steps, mu, color=INK2, linewidth=2)
    a2.fill_between(steps, mu - sd, mu + sd, color=INK2, alpha=0.15, linewidth=0)
    a2.set_ylabel("Validation log-likelihood", color=INK2, fontsize=9)
    a2.set_xlabel("Augmented Lagrangian step", color=INK2, fontsize=9)
    style(a1), style(a2)
    fig.suptitle(f"Netsim, {len(arr['auroc_agg'])} seeds, mean and 1 s.d.", color=INK, fontsize=10, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(OUT, f"fig8_{prefix}.png"), dpi=200, facecolor=SURF)
    plt.close(fig)
    pd.DataFrame({"step": steps, "auroc": np.nanmean(arr["auroc_agg"], 0), "orientation_f1": np.nanmean(arr["orientation_fscore_agg"], 0),
                  "val_ll": np.nanmean(arr["val_likelihood"], 0)}).to_csv(os.path.join(OUT, f"fig8_{prefix}.csv"), index=False)
    print("fig8:", prefix, "seeds", len(arr["auroc_agg"]), "steps", n)


if __name__ == "__main__":
    if sys.argv[1] == "fig8":
        for pre in (sys.argv[2:] or ["netsim_rhino_shipped"]):
            fig8(pre)
    else:
        {"lag": lag_table, "te": te_fig}[sys.argv[1]]()
