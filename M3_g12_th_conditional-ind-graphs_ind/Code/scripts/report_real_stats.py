"""Real-data statistics from the raw per-job results: AUROC, orientation F1 and SHD (paper Tables 2, 3, 6, 7, 8) and Welch tests."""
import math, os
import numpy as np, pandas as pd
from scipy import stats

R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Results"))
OUT = os.path.join(R, "tables", "report_extra")
d = pd.read_csv(os.path.join(R, "raw", "results_real_all.csv"))
d = d[d.status == "ok"].copy()
d["task"] = np.where(d.method.str.startswith("dream3"), "dream3", "netsim")
d["variant"] = d.method.str.replace("dream3_", "", regex=False).str.replace("netsim_", "", regex=False)
d["net"] = d.dataset.str.replace("dream3_100_", "", regex=False)
rows = []
for (task, var, net), g in d.groupby(["task", "variant", "net"]):
    n = len(g)
    r = dict(task=task, variant=var, net=net, n=n)
    for k, c in (("auroc", "auroc_agg"), ("of1", "orientation_fscore_agg"), ("shd", "shd_agg")):
        r[k] = g[c].mean(); r[k + "_se"] = g[c].std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    r["wall_h"] = g.wall_seconds.median() / 3600
    rows.append(r)
t = pd.DataFrame(rows); t.to_csv(os.path.join(OUT, "x_real_all.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(t.round(3).to_string())

# Welch tests (5 runs each) on AUROC
def welch(a, b):
    a = np.asarray(a); b = np.asarray(b)
    t_, p = stats.ttest_ind(a, b, equal_var=False)
    return a.mean() - b.mean(), p, len(a), len(b)

res = []
ns = d[(d.task == "netsim")]
def vals(var): return ns[ns.variant == var].auroc_agg.values
for a, b in (("rhino_paper", "rhino_g_paper"), ("rhino_paper", "rhino_noinst_paper"), ("rhino_paper", "rhino_shipped"),
             ("rhino_g_paper", "rhino_g_shipped"), ("rhino_noinst_paper", "rhino_noinst_shipped")):
    diff, p, na, nb = welch(vals(a), vals(b)); res.append(dict(task="netsim", a=a, b=b, net="-", diff=diff, p=p, na=na, nb=nb))
dr = d[d.task == "dream3"]
for net in ("ecoli1", "ecoli2", "yeast1", "yeast2", "yeast3"):
    g = dr[dr.net == net]
    a = g[g.variant == "rhino_paper"].auroc_agg.values; b = g[g.variant == "rhino_g_paper"].auroc_agg.values
    if len(a) > 1 and len(b) > 1:
        diff, p, na, nb = welch(a, b); res.append(dict(task="dream3", a="rhino_paper", b="rhino_g_paper", net=net, diff=diff, p=p, na=na, nb=nb))
w = pd.DataFrame(res); w["p_holm_dream3"] = np.nan
m = w.task == "dream3"
ps = w.loc[m, "p"].values; o = np.argsort(ps); adj = np.empty(len(ps)); run = 0
for rank, i in enumerate(o):
    run = max(run, (len(ps) - rank) * ps[i]); adj[i] = min(1, run)
w.loc[m, "p_holm_dream3"] = adj
w.to_csv(os.path.join(OUT, "x_real_welch.csv"), index=False)
print(w.round(4).to_string())
