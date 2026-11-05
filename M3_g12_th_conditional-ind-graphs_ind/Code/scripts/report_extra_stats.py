"""Extra statistics for the M3 report, computed only from the exported raw results of the workstation runs."""
import json, math, os
import numpy as np, pandas as pd
from scipy import stats

R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Results"))
OUT = os.path.join(R, "tables", "report_extra")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(2026)

sy = pd.read_csv(os.path.join(R, "raw", "results_synthetic_all.csv"))
sy = sy[sy.status == "ok"].copy()
F = "orientation_fscore_overall_temporal"
sy["F1T"] = sy[F]
sy["trueE"] = 2 * sy.dim + 4 * sy.dim * sy.inst          # lagged 2N, instantaneous 4N when enabled
P = sy.pivot_table(index=["dim", "dataset", "hist", "inst", "gtype", "seed"], columns="method", values="F1T").reset_index()


def holm(ps):
    ps = np.asarray(ps); o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for rank, i in enumerate(o):
        run = max(run, (m - rank) * ps[i]); adj[i] = min(1, run)
    return adj


def boot_ci(d, B=10000):
    d = np.asarray(d); idx = rng.integers(0, len(d), (B, len(d)))
    m = d[idx].mean(1); return np.percentile(m, [2.5, 97.5])


def paired(a, b, label, extra=None):
    d = (a - b).dropna()
    lo, hi = boot_ci(d.values)
    try:
        p = stats.wilcoxon(d, zero_method="wilcox").pvalue
    except ValueError:
        p = 1.0
    row = dict(comparison=label, n=len(d), mean_diff=d.mean(), boot_lo=lo, boot_hi=hi, wins=int((d > 0).sum()),
               losses=int((d < 0).sum()), p=p)
    if extra: row.update(extra)
    return row


# 1. Rhino vs the released-config sparsity penalty (lambda_s 9 vs 5), dims 5 and 10 only
rows = []
for dim in (5, 10):
    s = P[P.dim == dim]
    rows.append(paired(s["rhino"], s["rhino_shipped"], "Rhino (9) minus Rhino shipped (5)", dict(dim=dim)))
t1 = pd.DataFrame(rows); t1["p_holm"] = holm(t1.p); t1.to_csv(os.path.join(OUT, "x_lambda.csv"), index=False)

# 2. Rhino vs Rhino+g and Rhino+s by history dependence
rows = []
for dim in (5, 10, 20):
    for h in (0, 1):
        s = P[(P.dim == dim) & (P["hist"] == h)]
        for o in ("rhino_g", "rhino_s", "pcmci_plus", "dynotears"):
            rows.append(paired(s["rhino"], s[o], f"Rhino minus {o}", dict(dim=dim, hist=h)))
t2 = pd.DataFrame(rows); t2["p_holm"] = holm(t2.p); t2.to_csv(os.path.join(OUT, "x_hist.csv"), index=False)

# 3. same by instantaneous effects
rows = []
for dim in (5, 10, 20):
    for i in (0, 1):
        s = P[(P.dim == dim) & (P.inst == i)]
        for o in ("rhino_g", "pcmci_plus"):
            rows.append(paired(s["rhino"], s[o], f"Rhino minus {o}", dict(dim=dim, inst=i)))
t3 = pd.DataFrame(rows); t3["p_holm"] = holm(t3.p); t3.to_csv(os.path.join(OUT, "x_inst.csv"), index=False)

# 4. error analysis: precision, recall, predicted edge count (orientation, temporal graph)
ea = sy.groupby(["dim", "method"]).agg(prec=("orientation_precision_overall_temporal", "mean"),
                                       rec=("orientation_recall_overall_temporal", "mean"),
                                       nnz=("nnz_overall_temporal", "mean"), trueE=("trueE", "mean"),
                                       n=("F1T", "size")).reset_index()
ea["ratio"] = ea.nnz / ea.trueE
ea.to_csv(os.path.join(OUT, "x_error.csv"), index=False)
# adjacency F1 vs orientation F1 gap (wrong direction)
sy["gap"] = sy["adjacency_fscore_overall_temporal"] - sy["orientation_fscore_overall_temporal"]
gap = sy.groupby(["dim", "method"]).gap.mean().unstack().round(3); gap.to_csv(os.path.join(OUT, "x_gap.csv"))

# 5. Treatment effect
te = pd.read_csv(os.path.join(R, "raw", "results_treatment_effect_all.csv"))
te = te[te.status == "ok"]
tp = te.pivot_table(index=["dim", "dataset"], columns="method", values="ATE_RMSE").reset_index()
rows = []
for dim in (5, 10, 20):
    s = tp[tp.dim == dim]
    for a, b in (("rhino", "rhino_s"), ("rhino", "rhino_g"), ("rhino_g", "rhino_s")):
        rows.append(paired(s[a], s[b], f"{a} minus {b} (ATE RMSE)", dict(dim=dim)))
t5 = pd.DataFrame(rows); t5["p_holm"] = holm(t5.p); t5.to_csv(os.path.join(OUT, "x_te_paired.csv"), index=False)
m = te.merge(sy[["method", "dataset", "F1T", "hist", "inst"]], on=["method", "dataset"])
rows = []
for meth in ("rhino", "rhino_g", "rhino_s", "all"):
    for dim in (5, 10, 20, "all"):
        s_ = m.copy()
        if meth != "all": s_ = s_[s_.method == meth]
        if dim != "all": s_ = s_[s_.dim == dim]
        for col in ("ATE_RMSE", "Normalised_ATE_RMSE"):
            rho, p = stats.spearmanr(s_.F1T, s_[col])
            rows.append(dict(method=meth, dim=dim, target=col, strata="none", n=len(s_), spearman=rho, p=p))
# within strata of (hist, inst): removes the effect of dataset type, then averages the rank correlations
for col in ("ATE_RMSE", "Normalised_ATE_RMSE"):
    rs, ws = [], []
    for (meth, dim, h, i), g in m.groupby(["method", "dim", "hist", "inst"]):
        if len(g) >= 5 and g.F1T.nunique() > 1:
            rs.append(stats.spearmanr(g.F1T, g[col])[0]); ws.append(len(g))
    rows.append(dict(method="all", dim="all", target=col, strata="method x dim x hist x inst", n=sum(ws),
                     spearman=float(np.average(rs, weights=ws)), p=float("nan")))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "x_te_corr.csv"), index=False)

# 6. Rhino vs PCMCI+ at 20 nodes with a bootstrap interval on temporal F1
s = P[P.dim == 20]
b20 = paired(s["rhino"], s["pcmci_plus"], "Rhino minus PCMCI+, 20 nodes")
pd.DataFrame([b20]).to_csv(os.path.join(OUT, "x_boot20.csv"), index=False)

# 7. Fig 8 summary numbers
f8 = {}
for k in ("rhino_shipped", "rhino_g_shipped", "rhino_noinst_shipped"):
    d = pd.read_csv(os.path.join(R, "tables", f"fig8_netsim_{k}.csv"))
    f8[k] = dict(steps=len(d), auroc_peak=d.auroc.max(), auroc_peak_step=int(d.auroc.idxmax()), auroc_final=d.auroc.iloc[-1],
                 f1_first=d.orientation_f1.iloc[0], f1_final=d.orientation_f1.iloc[-1], f1_max=d.orientation_f1.max(),
                 ll_first=d.val_ll.iloc[0], ll_final=d.val_ll.iloc[-1], ll_best=d.val_ll.max(), ll_best_step=int(d.val_ll.idxmax()))
pd.DataFrame(f8).T.to_csv(os.path.join(OUT, "x_fig8.csv"))

pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
for n, t in (("lambda", t1), ("hist", t2), ("inst", t3), ("error", ea), ("gap", gap), ("te paired", t5), ("boot20", pd.DataFrame([b20])),
             ("fig8", pd.DataFrame(f8).T)):
    print("=====", n); print(t.round(3).to_string())
print("===== te corr"); print(pd.read_csv(os.path.join(OUT, "x_te_corr.csv")).round(3).to_string())
