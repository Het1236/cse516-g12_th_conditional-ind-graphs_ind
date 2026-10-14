import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import numpy as np
import pandas as pd

PAPER = {
    "AUPR": {"SGLCV": {10: (0.112, 0.013), 25: (0.132, 0.012), 50: (0.219, 0.085)},
             "uGLAD": {10: (0.159, 0.029), 25: (0.174, 0.018), 50: (0.223, 0.062)}},
    "AUC": {"SGLCV": {10: (0.505, 0.007), 25: (0.532, 0.031), 50: (0.617, 0.083)},
            "uGLAD": {10: (0.572, 0.027), 25: (0.595, 0.044), 50: (0.651, 0.021)}},
}
SIZES = [10, 25, 50]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    a = ap.parse_args()
    df = pd.read_csv(os.path.join(a.results, "table1_raw.csv"))
    global SIZES
    SIZES = [m for m in SIZES if m in set(df.M.unique())]
    n_graphs = df[df.method == "uGLAD"].groupby("M")["graph"].nunique().to_dict()

    rows = []
    for metric in ("AUPR", "AUC"):
        for m in ("SGLCV", "uGLAD"):
            for s in SIZES:
                x = df[(df.method == m) & (df.M == s)][metric]
                pm, ps = PAPER[metric][m][s]
                rows.append({"metric": metric, "method": m, "M": s, "paper mean": pm, "paper std": ps,
                             "mine mean": round(x.mean(), 3), "mine std": round(x.std(), 3), "graphs": len(x),
                             "difference (mine - paper)": round(x.mean() - pm, 3)})
    comp = pd.DataFrame(rows)
    comp.to_csv(os.path.join(a.results, "table1_comparison.csv"), index=False)

    prow = []
    for metric in ("AUPR", "AUC"):
        for s in SIZES:
            u = df[(df.method == "uGLAD") & (df.M == s)].set_index("graph")[metric]
            g = df[(df.method == "SGLCV") & (df.M == s)].set_index("graph")[metric]
            j = pd.concat([u, g], axis=1, keys=["u", "g"]).dropna()
            d = j["u"] - j["g"]
            prow.append({"metric": metric, "M": s, "graphs": len(j), "mean (uGLAD - SGLCV)": round(d.mean(), 3),
                         "std": round(d.std(), 3), "uGLAD higher on": int((d > 0).sum()), "ties": int((d == 0).sum()),
                         "paired t statistic": round(float(d.mean() / (d.std() / np.sqrt(len(d)))), 2) if len(d) > 1 and d.std() > 0 else float("nan")})
    paired = pd.DataFrame(prow)
    paired.to_csv(os.path.join(a.results, "table1_paired.csv"), index=False)

    extra = []
    for s in SIZES:
        for m in ("SGLCV", "uGLAD"):
            x = df[(df.method == m) & (df.M == s)]
            extra.append({"method": m, "M": s, "mean predicted edges": round(x.n_pred_edges.mean(), 1),
                          "empty graphs": int((x.n_pred_edges == 0).sum()), "median seconds": round(x.seconds.median(), 1)})
    extra = pd.DataFrame(extra)

    md = ["# Reproduction of Table 1 of the uGLAD paper", "",
          f"Graphs per M: {n_graphs}. D = 25, edge probability 0.1, edge values U(-1, 1). "
          "uGLAD is the authors' public code in CV mode (250 epochs, learning rate 0.002, 3 folds). "
          "SGLCV is scikit-learn GraphicalLassoCV with default settings.", "",
          "## Paper against my run", "", comp.to_markdown(index=False), "",
          "## Paired comparison on the same datasets", "", paired.to_markdown(index=False), "",
          "## Predicted edges, empty graphs and run time", "", extra.to_markdown(index=False), ""]
    with open(os.path.join(a.results, "table1_comparison.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for ax, metric in zip(axes, ("AUPR", "AUC")):
        for m, color in (("SGLCV", "black"), ("uGLAD", "#7D1916")):
            mine = [df[(df.method == m) & (df.M == s)][metric].agg(["mean", "std"]).values for s in SIZES]
            ax.errorbar(SIZES, [v[0] for v in mine], yerr=[v[1] for v in mine], color=color, marker="o", capsize=3,
                        label=f"{m} (this run)")
            ax.errorbar(SIZES, [PAPER[metric][m][s][0] for s in SIZES], yerr=[PAPER[metric][m][s][1] for s in SIZES],
                        color=color, marker="x", ls="--", capsize=3, alpha=0.55, label=f"{m} (paper)")
        ax.set_xscale("log")
        ax.set_xticks(SIZES)
        ax.set_xticklabels([str(s) for s in SIZES])
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel("number of samples M")
        ax.set_ylabel(metric)
        ax.grid(alpha=0.25)
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(a.results, "fig_table1_reproduction.png"), dpi=200)
    print(comp.to_string(index=False))
    print(paired.to_string(index=False))
    print(extra.to_string(index=False))


if __name__ == "__main__":
    main()
