"""Calibration and error-controlled edge selection for Rhino's graph posterior q(G).

Input : the .npz files written by export_qG.py (edge probabilities p_e and true graph y_e per run).
Output: tables (CSV) and figures (PNG) used in the M4 report. Every number in the report comes from here.

Definitions (see report, Section "Problem formulation")
-------------------------------------------------------
Unit of analysis : an edge entry e = (lag k, source i, target j). p_e is the model's probability, y_e in {0,1}
                   the truth. The instantaneous diagonal is excluded (mask).
Selection        : a set S of entries. FDP(S) = |{e in S: y_e = 0}| / |S|  (0 if S is empty).
Promised FDR     : a_hat(S) = mean_{e in S} (1 - p_e)       (what the posterior says)
Overconfidence   : o(S)     = mean_{e in S} p_e - mean_{e in S} y_e
Identity         : FDP(S) = a_hat(S) + o(S)   (exact, pure algebra; checked in tests)
Bayesian FDR     : S_alpha = largest top-k set of entries sorted by p with a_hat <= alpha.
Temperature      : p' = sigmoid(logit(p_s) / tau), p_s is p with Laplace smoothing (count + 0.5)/(S + 1).
                   tau is fitted by minimising log-loss on *other* datasets (grouped K-fold). Ranking is unchanged.
"""
import argparse
import glob
import json
import os
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar
from sklearn.metrics import average_precision_score, roc_auc_score

ALPHAS = [0.01, 0.05, 0.10, 0.20, 0.30, 0.50]
EPS = 1e-6


# ----------------------------------------------------------------------------- loading
def load_export(export_dir, methods=None):
    runs = []
    for f in sorted(glob.glob(os.path.join(export_dir, "*.npz"))):
        z = np.load(f, allow_pickle=True)
        meta = json.loads(str(z["meta"]))
        if methods and meta["method"] not in methods:
            continue
        S = int(z["n_samples"])
        m = z["mask"].astype(bool).ravel()
        lagidx = np.zeros(z["probs"].shape, dtype=bool)
        if z["probs"].ndim == 3:
            lagidx[1:] = True
        lo = z["logodds"].astype(float).ravel()[m] if "logodds" in z.files else None
        runs.append(dict(meta=meta, S=S, p=z["probs"].astype(float).ravel()[m], y=z["truth"].astype(int).ravel()[m],
                         is_lag=lagidx.ravel()[m], lo=lo))
    return runs


# ----------------------------------------------------------------------------- probability helpers
EXACT_S = 100000  # n_samples >= this marks exact probabilities (export_exact_q.py writes 10**6)


def smooth(p, S):
    """Sampled p (a multiple of 1/S): Laplace smoothing so that the logit is finite.
    Exact p (S >= EXACT_S): only a tiny clip, so that saturation information is kept."""
    if S >= EXACT_S:
        return np.clip(p, 1e-12, 1 - 1e-12)
    return np.clip((p * S + 0.5) / (S + 1.0), EPS, 1 - EPS)


def run_logit(r):
    """Log-odds of a run. Exact exports carry the log-odds themselves (no float saturation)."""
    if r.get("lo") is not None:
        return np.clip(r["lo"], -40.0, 40.0)
    return logit(smooth(r["p"], r["S"]))


def apply_temp_run(r, tau):
    return sigmoid(run_logit(r) / tau)


def logit(p):
    return np.log(p) - np.log1p(-p)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def apply_temp(p, S, tau):
    return sigmoid(logit(smooth(p, S)) / tau)


def logloss(p, y):
    p = np.clip(p, EPS, 1 - EPS)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log1p(-p)))


def brier(p, y):
    return float(np.mean((p - y) ** 2))


def reliability(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    rows = []
    for b in range(bins):
        sel = idx == b
        if sel.any():
            rows.append((b, sel.sum(), p[sel].mean(), y[sel].mean()))
    return pd.DataFrame(rows, columns=["bin", "n", "conf", "acc"])


def ece(p, y, bins=10):
    r = reliability(p, y, bins)
    return float((r["n"] * (r["conf"] - r["acc"]).abs()).sum() / r["n"].sum())


def fit_tau(runs, idxs):
    """Pooled log-loss minimiser over the chosen runs."""
    Y = [runs[i]["y"] for i in idxs]
    z = np.concatenate([run_logit(runs[i]) for i in idxs])
    y = np.concatenate(Y)

    def nll(lt):
        return logloss(sigmoid(z / np.exp(lt)), y)

    r = minimize_scalar(nll, bounds=(-4, 4), method="bounded")
    return float(np.exp(r.x))


# ----------------------------------------------------------------------------- selection rules
def bfdr_select(p, alpha):
    """Largest top-k set with mean(1 - p) <= alpha. Returns a boolean mask."""
    order = np.argsort(-p, kind="stable")
    cum = np.cumsum(1 - p[order]) / np.arange(1, len(p) + 1)
    ok = np.where(cum <= alpha)[0]
    sel = np.zeros(len(p), dtype=bool)
    if len(ok):
        sel[order[: ok.max() + 1]] = True
    return sel


def expected_f1_select(p):
    """Top-k set that maximises the plug-in expected F1 = 2 sum_top p / (k + sum_all p)."""
    order = np.argsort(-p, kind="stable")
    cum = np.cumsum(p[order])
    k = np.arange(1, len(p) + 1)
    ef1 = 2 * cum / (k + p.sum())
    sel = np.zeros(len(p), dtype=bool)
    sel[order[: int(np.argmax(ef1)) + 1]] = True
    return sel


def sel_metrics(sel, p, y):
    k = int(sel.sum())
    tp = int((y[sel] == 1).sum())
    pos = int(y.sum())
    fdp = 0.0 if k == 0 else (k - tp) / k
    prec = tp / k if k else 0.0
    rec = tp / pos if pos else np.nan
    f1 = 2 * tp / (k + pos) if (k + pos) else 0.0
    promised = float((1 - p[sel]).mean()) if k else 0.0
    return dict(k=k, tp=tp, fdp=fdp, power=rec, precision=prec, f1=f1, promised=promised)


def cutoff_for_alpha(scores, y, alpha, min_k=10):
    """Selection calibration. On calibration data (pooled scores and truth) find the lowest score cutoff such that the
    selected entries (score >= cutoff) have a false discovery proportion <= alpha. Cutoffs are placed only between
    distinct score values (ties stay together). Returns +inf if no cutoff reaches the budget with at least min_k entries."""
    order = np.argsort(-scores, kind="stable")
    ss, yy = scores[order], y[order]
    fp = np.cumsum(1 - yy)
    k = np.arange(1, len(ss) + 1)
    group_end = np.r_[ss[1:] != ss[:-1], True]
    ok = np.where(group_end & (fp / k <= alpha) & (k >= min_k))[0]
    return ss[ok.max()] if len(ok) else np.inf


def oracle_f1(p, y):
    """Best F1 over all thresholds, uses the truth (upper bound, not usable in practice)."""
    order = np.argsort(-p, kind="stable")
    tp = np.cumsum(y[order])
    k = np.arange(1, len(p) + 1)
    return float(np.max(2 * tp / (k + y.sum()))) if y.sum() else np.nan


# ----------------------------------------------------------------------------- statistics helpers
def mean_sd_ci(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n == 0:
        return np.nan, np.nan, np.nan, np.nan, 0
    m = x.mean()
    sd = x.std(ddof=1) if n > 1 else 0.0
    h = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 1 else np.nan
    return m, sd, m - h, m + h, n


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


def wilcoxon(a, b):
    d = np.asarray(a) - np.asarray(b)
    d = d[~np.isnan(d)]
    if len(d) < 6 or np.allclose(d, 0):
        return np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(stats.wilcoxon(d).pvalue)


def boot_ece_ci(runs, probs, B=1000, seed=0):
    """Bootstrap over datasets of the pooled ECE."""
    rng = np.random.default_rng(seed)
    n = len(runs)
    vals = []
    for _ in range(B):
        ii = rng.integers(0, n, n)
        p = np.concatenate([probs[i] for i in ii])
        y = np.concatenate([runs[i]["y"] for i in ii])
        vals.append(ece(p, y))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


# ----------------------------------------------------------------------------- main analysis
def grouped_folds(n, k, seed=0):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    return [perm[i::k] for i in range(k)]


def analyse(runs, folds, out_tables, out_figs, tag, fit_runs=None):
    """If fit_runs is given, tau is fitted on those runs and applied to all of `runs` (distribution shift).
    Otherwise tau is fitted by grouped K-fold over `runs` (each run is calibrated with a tau it did not help to fit)."""
    n = len(runs)
    taus = np.zeros(n)
    if fit_runs is not None:
        allr = fit_runs + runs
        tau = fit_tau(allr, range(len(fit_runs)))
        taus[:] = tau
    else:
        fs = grouped_folds(n, min(folds, n))
        for te in fs:
            tr = [i for i in range(n) if i not in set(te)]
            tau = fit_tau(runs, tr)
            taus[te] = tau

    variants = {"raw": [r["p"] for r in runs],
                "temperature": [apply_temp_run(r, taus[i]) for i, r in enumerate(runs)]}
    rows_cal, rows_fdr, rows_thr, per_ds = [], [], [], []

    for v, P in variants.items():
        for i, r in enumerate(runs):
            p, y, m = P[i], r["y"], r["meta"]
            base = dict(variant=v, job_id=m["job_id"], method=m["method"], dataset=m["dataset"], dim=m.get("dim"),
                        hist=m.get("hist"), inst=m.get("inst"), gtype=m.get("gtype"), tau=taus[i])
            row = dict(base, brier=brier(p, y), logloss=logloss(p, y), ece=ece(p, y),
                       auroc=roc_auc_score(y, p) if 0 < y.sum() < len(y) else np.nan,
                       auprc=average_precision_score(y, p) if y.sum() else np.nan,
                       n_edges_true=int(y.sum()), mean_p=float(p.mean()), prevalence=float(y.mean()))
            sel = p >= 0.5
            thr = sel_metrics(sel, p, y)
            row.update({"f1_thr05": thr["f1"], "fdp_thr05": thr["fdp"], "promised_thr05": thr["promised"]})
            ef = sel_metrics(expected_f1_select(p), p, y)
            row.update({"f1_expF1": ef["f1"], "fdp_expF1": ef["fdp"], "k_expF1": ef["k"]})
            row["f1_oracle"] = oracle_f1(p, y)
            per_ds.append(row)
            for a in ALPHAS:
                sm = sel_metrics(bfdr_select(p, a), p, y)
                rows_fdr.append(dict(base, alpha=a, **sm))
    # ---- selection calibration: cutoff learned on other datasets (grouped CV, or the synthetic runs in shift mode)
    if fit_runs is not None:
        train_for = {i: list(fit_runs) for i in range(n)}
        fold_of = {i: -1 for i in range(n)}
    else:
        train_for, fold_of = {}, {}
        for fi, te in enumerate(fs):
            tes = set(te)
            trn = [runs[j] for j in range(n) if j not in tes]
            for i in te:
                train_for[i], fold_of[i] = trn, fi
    cut_cache = {}
    for i, r in enumerate(runs):
        m = r["meta"]
        sc = run_logit(r)
        for name, strat in (("cutoff_pooled", False), ("cutoff_same_dim", True)):
            tr = train_for[i]
            if strat:
                tr = [t for t in tr if t["meta"].get("dim") == m.get("dim")] or tr  # no run of this size: pooled
            for a in ALPHAS:
                ck = (name, fold_of[i], m.get("dim") if strat else None, a)
                if ck not in cut_cache:
                    cut_cache[ck] = cutoff_for_alpha(np.concatenate([run_logit(t) for t in tr]),
                                                     np.concatenate([t["y"] for t in tr]), a)
                sm = sel_metrics(sc >= cut_cache[ck], r["p"], r["y"])
                sm["promised"] = np.nan  # the promise of a cutoff rule is alpha itself
                rows_fdr.append(dict(variant=name, job_id=m["job_id"], method=m["method"], dataset=m["dataset"],
                                     dim=m.get("dim"), hist=m.get("hist"), inst=m.get("inst"), gtype=m.get("gtype"),
                                     tau=taus[i], alpha=a, **sm))
    all_variants = list(variants) + ["cutoff_pooled", "cutoff_same_dim"]
    per = pd.DataFrame(per_ds)
    fdr = pd.DataFrame(rows_fdr)
    per.to_csv(os.path.join(out_tables, f"per_dataset_{tag}.csv"), index=False)
    fdr.to_csv(os.path.join(out_tables, f"per_dataset_fdr_{tag}.csv"), index=False)

    # ---- table 1: probability quality
    t1 = []
    for v in variants:
        d = per[per.variant == v]
        pr = variants[v]
        lo, hi = boot_ece_ci(runs, pr)
        pooled_p, pooled_y = np.concatenate(pr), np.concatenate([r["y"] for r in runs])
        rec = dict(variant=v, n_datasets=len(d), ece_pooled=ece(pooled_p, pooled_y), ece_pooled_ci_lo=lo,
                   ece_pooled_ci_hi=hi, brier_pooled=brier(pooled_p, pooled_y), logloss_pooled=logloss(pooled_p, pooled_y))
        for c in ("brier", "logloss", "auroc", "auprc"):
            m_, sd, l, h, nn = mean_sd_ci(d[c])
            rec.update({f"{c}_mean": m_, f"{c}_sd": sd, f"{c}_ci_lo": l, f"{c}_ci_hi": h})
        t1.append(rec)
    pd.DataFrame(t1).to_csv(os.path.join(out_tables, f"table_probability_quality_{tag}.csv"), index=False)

    # ---- table 2: FDR control
    t2 = []
    for v in all_variants:
        for a in ALPHAS:
            d = fdr[(fdr.variant == v) & (fdr.alpha == a)]
            rec = dict(variant=v, alpha=a, n_datasets=len(d), frac_empty=float((d.k == 0).mean()), mean_k=float(d.k.mean()))
            for c in ("fdp", "power", "promised", "f1"):
                m_, sd, l, h, _ = mean_sd_ci(d[c])
                rec.update({f"{c}_mean": m_, f"{c}_sd": sd, f"{c}_ci_lo": l, f"{c}_ci_hi": h})
            rec["gap_realised_minus_alpha"] = rec["fdp_mean"] - a
            t2.append(rec)
    t2 = pd.DataFrame(t2)
    t2.to_csv(os.path.join(out_tables, f"table_fdr_control_{tag}.csv"), index=False)

    # ---- table 3: graph choice rules
    t3 = []
    for v in variants:
        d = per[per.variant == v]
        for c, name in (("f1_thr05", "threshold 0.5"), ("f1_expF1", "expected-F1 rule"), ("f1_oracle", "oracle threshold (uses truth)")):
            m_, sd, l, h, _ = mean_sd_ci(d[c])
            t3.append(dict(variant=v, rule=name, f1_mean=m_, f1_sd=sd, f1_ci_lo=l, f1_ci_hi=h))
    pd.DataFrame(t3).to_csv(os.path.join(out_tables, f"table_graph_rules_{tag}.csv"), index=False)

    # ---- table 4: paired tests (same datasets, raw vs temperature)
    raw = per[per.variant == "raw"].set_index("job_id")
    cal = per[per.variant == "temperature"].set_index("job_id")
    tests = []
    for c, nm in (("brier", "Brier"), ("logloss", "log-loss"), ("ece", "ECE (per dataset)"),
                  ("f1_expF1", "F1, expected-F1 rule"), ("f1_thr05", "F1, threshold 0.5")):
        diff = (cal[c] - raw[c]).values
        m_, sd, l, h, nn = mean_sd_ci(diff)
        tests.append(dict(quantity=nm, mean_diff_cal_minus_raw=m_, ci_lo=l, ci_hi=h, n=nn,
                          wins_cal=int((diff < 0).sum() if c in ("brier", "logloss", "ece") else (diff > 0).sum()),
                          wins_raw=int((diff > 0).sum() if c in ("brier", "logloss", "ece") else (diff < 0).sum()),
                          p_wilcoxon=wilcoxon(cal[c].values, raw[c].values)))
    for a in (0.05, 0.10, 0.20):
        x = fdr[(fdr.alpha == a)]
        ra = x[x.variant == "raw"].set_index("job_id")["fdp"]
        ca = x[x.variant == "temperature"].set_index("job_id")["fdp"]
        diff = (ca - a).abs().values - (ra - a).abs().values
        m_, sd, l, h, nn = mean_sd_ci(diff)
        tests.append(dict(quantity=f"|FDP - alpha|, alpha={a}", mean_diff_cal_minus_raw=m_, ci_lo=l, ci_hi=h, n=nn,
                          wins_cal=int((diff < 0).sum()), wins_raw=int((diff > 0).sum()),
                          p_wilcoxon=wilcoxon((ca - a).abs().values, (ra - a).abs().values)))
    tt = pd.DataFrame(tests)
    tt["p_holm"] = holm(tt["p_wilcoxon"].fillna(1.0).values)
    tt.to_csv(os.path.join(out_tables, f"table_paired_tests_{tag}.csv"), index=False)

    make_figures(runs, variants, t2, per, taus, out_figs, tag)
    return dict(per=per, fdr=fdr, t2=t2, taus=taus)


def make_figures(runs, variants, t2, per, taus, out_figs, tag):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    col = {"raw": "#b03a2e", "temperature": "#1f618d", "cutoff_pooled": "#117a65", "cutoff_same_dim": "#7d6608"}
    lab = {"raw": "raw q(G), Bayesian FDR", "temperature": "temperature-scaled, Bayesian FDR",
           "cutoff_pooled": "cutoff learned on other datasets", "cutoff_same_dim": "cutoff learned on same-size datasets"}

    # reliability diagram
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.8), gridspec_kw={"width_ratios": [1.2, 1]})
    y = np.concatenate([r["y"] for r in runs])
    ax[0].plot([0, 1], [0, 1], "k--", lw=1, label="perfect")
    for v, P in variants.items():
        rel = reliability(np.concatenate(P), y, 10)
        ax[0].plot(rel["conf"], rel["acc"], "o-", color=col[v], label=lab[v])
    ax[0].set_xlabel("mean predicted edge probability in bin")
    ax[0].set_ylabel("observed fraction of true edges")
    ax[0].legend(frameon=False, fontsize=8)
    ax[0].set_title("Reliability diagram (pooled)")
    for v, P in variants.items():
        ax[1].hist(np.concatenate(P), bins=20, range=(0, 1), alpha=0.55, color=col[v], label=lab[v])
    ax[1].set_yscale("log")
    ax[1].set_xlabel("edge probability")
    ax[1].set_ylabel("number of edge entries")
    ax[1].set_title("Distribution of probabilities")
    fig.tight_layout()
    fig.savefig(os.path.join(out_figs, f"fig_reliability_{tag}.png"), dpi=200)
    plt.close(fig)

    # FDR control curve and power
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.8))
    ax[0].plot([0, 0.5], [0, 0.5], "k--", lw=1, label="ideal (realised = nominal)")
    for v in [x for x in col if x in set(t2.variant)]:
        d = t2[t2.variant == v]
        ax[0].errorbar(d.alpha, d.fdp_mean, yerr=[d.fdp_mean - d.fdp_ci_lo, d.fdp_ci_hi - d.fdp_mean], fmt="o-",
                       color=col[v], capsize=3, label=lab[v])
        ax[1].errorbar(d.alpha, d.power_mean, yerr=[d.power_mean - d.power_ci_lo, d.power_ci_hi - d.power_mean],
                       fmt="o-", color=col[v], capsize=3, label=lab[v])
    ax[0].set_xlabel("nominal FDR budget alpha")
    ax[0].set_ylabel("realised false discovery proportion")
    ax[0].set_title("FDR control (mean, 95% CI over datasets)")
    ax[0].legend(frameon=False, fontsize=8)
    ax[1].set_xlabel("nominal FDR budget alpha")
    ax[1].set_ylabel("power (recall of true edges)")
    ax[1].set_title("Price of control")
    fig.tight_layout()
    fig.savefig(os.path.join(out_figs, f"fig_fdr_control_{tag}.png"), dpi=200)
    plt.close(fig)

    # per-dataset ECE raw vs calibrated and tau
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
    r = per[per.variant == "raw"].set_index("job_id")
    c = per[per.variant == "temperature"].set_index("job_id")
    ax[0].scatter(r["brier"], c.loc[r.index, "brier"], s=14, color="#1f618d")
    lim = [0, max(r["brier"].max(), c["brier"].max()) * 1.05]
    ax[0].plot(lim, lim, "k--", lw=1)
    ax[0].set_xlabel("Brier, raw")
    ax[0].set_ylabel("Brier, temperature-scaled")
    ax[0].set_title("Each point is one dataset")
    ax[1].hist(taus, bins=15, color="#7d6608")
    ax[1].set_xlabel("fitted temperature tau (tau > 1: raw q(G) was overconfident)")
    ax[1].set_ylabel("number of datasets")
    fig.tight_layout()
    fig.savefig(os.path.join(out_figs, f"fig_brier_and_tau_{tag}.png"), dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export_dir", required=True)
    ap.add_argument("--out_tables", default="../../Results/tables")
    ap.add_argument("--out_figs", default="../../Results/figures")
    ap.add_argument("--methods", nargs="+", default=None, help="evaluate these methods")
    ap.add_argument("--fit_methods", nargs="+", default=None,
                    help="if given, tau is fitted on these methods and applied to --methods (distribution shift)")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--tag", default="synthetic")
    a = ap.parse_args()
    os.makedirs(a.out_tables, exist_ok=True)
    os.makedirs(a.out_figs, exist_ok=True)
    runs = load_export(a.export_dir, a.methods)
    fit_runs = load_export(a.export_dir, a.fit_methods) if a.fit_methods else None
    print(f"{len(runs)} runs to evaluate" + (f", tau fitted on {len(fit_runs)} runs" if fit_runs else ""))
    res = analyse(runs, a.folds, a.out_tables, a.out_figs, a.tag, fit_runs)
    print(res["t2"][["variant", "alpha", "promised_mean", "fdp_mean", "power_mean", "frac_empty"]].to_string(index=False))


if __name__ == "__main__":
    main()
