"""Consolidated tables and figures across all Rhino variants and data sets.
Reads the per-dataset files written by calib_fdr.py (Results/tables) and the exported probabilities.
Run after calib_fdr.py for every tag listed in TAGS.   python summary_tables.py [--export_dir DIR] [--suffix _exact]
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy import stats

import calib_fdr as cf

# tag -> (methods exported, label, group)
TAGS = {
    "synth_rhino": (["rhino"], "Rhino (paper settings)", "synthetic"),
    "synth_rhino_g": (["rhino_g"], "Rhino+g (Gaussian noise)", "synthetic"),
    "synth_rhino_s": (["rhino_s"], "Rhino+s (spline noise, no history)", "synthetic"),
    "synth_rhino_shipped": (["rhino_shipped"], "Rhino (released config)", "synthetic"),
    "shift_netsim_rhino_paper": (["netsim_rhino_paper"], "Netsim, paper steps", "real"),
    "shift_netsim_rhino_shipped": (["netsim_rhino_shipped"], "Netsim, released config (more steps)", "real"),
    "shift_dream3_rhino_paper": (["dream3_rhino_paper"], "DREAM3 (100 genes), Rhino", "real"),
    "shift_dream3_rhino_g_paper": (["dream3_rhino_g_paper"], "DREAM3 (100 genes), Rhino+g", "real"),
}


def ci(x):
    m, sd, lo, hi, n = cf.mean_sd_ci(x)
    return m, sd, lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export_dir", default="../../Results/qG_export")
    ap.add_argument("--tables", default="../../Results/tables")
    ap.add_argument("--figs", default="../../Results/figures")
    ap.add_argument("--suffix", default="", help="suffix of the tags, e.g. _exact")
    a = ap.parse_args()
    rows, curves = [], {}
    for tag, (methods, label, group) in TAGS.items():
        t = tag + a.suffix
        f_per = os.path.join(a.tables, f"per_dataset_{t}.csv")
        if not os.path.isfile(f_per):
            continue
        per = pd.read_csv(f_per)
        fdr = pd.read_csv(os.path.join(a.tables, f"per_dataset_fdr_{t}.csv"))
        pq = pd.read_csv(os.path.join(a.tables, f"table_probability_quality_{t}.csv")).set_index("variant")
        runs = cf.load_export(a.export_dir, methods)
        p = np.concatenate([r["p"] for r in runs])
        y = np.concatenate([r["y"] for r in runs])
        lo_m, hi_m = p < 1e-3, p > 1 - 1e-3
        rec = dict(tag=tag, label=label, group=group, n_runs=len(runs), n_entries=len(p),
                   frac_p_eq_0=float(lo_m.mean()), frac_p_eq_1=float(hi_m.mean()),
                   edge_rate_when_p_is_0=float(y[lo_m].mean()) if lo_m.any() else np.nan,
                   edge_rate_when_p_is_1=float(y[hi_m].mean()) if hi_m.any() else np.nan,
                   prevalence=float(y.mean()), mean_p=float(p.mean()),
                   auroc_mean=pq.loc["raw", "auroc_mean"], tau_mean=float(per[per.variant == "temperature"].tau.mean()))
        for v in ("cutoff_pooled", "cutoff_same_dim"):
            for al in (0.05, 0.10, 0.20):
                d = fdr[(fdr.variant == v) & (np.isclose(fdr.alpha, al))]
                m, sd, lo, hi = ci(d.fdp)
                rec[f"fdp_{v}_a{al}"], rec[f"fdp_{v}_a{al}_lo"], rec[f"fdp_{v}_a{al}_hi"] = m, lo, hi
                rec[f"power_{v}_a{al}"] = d.power.mean()
                rec[f"empty_{v}_a{al}"] = float((d.k == 0).mean())
        for v in ("raw", "temperature"):
            rec[f"ece_{v}"] = pq.loc[v, "ece_pooled"]
            rec[f"ece_{v}_lo"] = pq.loc[v, "ece_pooled_ci_lo"]
            rec[f"ece_{v}_hi"] = pq.loc[v, "ece_pooled_ci_hi"]
            rec[f"brier_{v}"] = pq.loc[v, "brier_pooled"]
            rec[f"logloss_{v}"] = pq.loc[v, "logloss_pooled"]
            for al in (0.05, 0.10):
                d = fdr[(fdr.variant == v) & (np.isclose(fdr.alpha, al))]
                m, sd, lo, hi = ci(d.fdp)
                rec[f"fdp_{v}_a{al}"] = m
                rec[f"fdp_{v}_a{al}_lo"], rec[f"fdp_{v}_a{al}_hi"] = lo, hi
                rec[f"power_{v}_a{al}"] = d.power.mean()
                rec[f"empty_{v}_a{al}"] = float((d.k == 0).mean())
        rows.append(rec)
        curves[tag] = (label, group, fdr)
    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(a.tables, f"table_summary_all{a.suffix}.csv"), index=False)
    print(summ[["label", "n_runs", "frac_p_eq_0", "frac_p_eq_1", "edge_rate_when_p_is_0", "edge_rate_when_p_is_1",
                "ece_raw", "ece_temperature", "fdp_raw_a0.1", "fdp_temperature_a0.1"]].round(3).to_string(index=False))

    # breakdown for the main method
    t = "synth_rhino" + a.suffix
    f_per = os.path.join(a.tables, f"per_dataset_{t}.csv")
    if os.path.isfile(f_per):
        per = pd.read_csv(f_per)
        fdr = pd.read_csv(os.path.join(a.tables, f"per_dataset_fdr_{t}.csv"))
        out = []
        for (dim, hist), g in per[per.variant == "raw"].groupby(["dim", "hist"]):
            ids = set(g.job_id)
            f = fdr[(fdr.variant == "raw") & np.isclose(fdr.alpha, 0.10) & fdr.job_id.isin(ids)]
            fc = fdr[(fdr.variant == "temperature") & np.isclose(fdr.alpha, 0.10) & fdr.job_id.isin(ids)]
            out.append(dict(dim=dim, history_dependent_noise=hist, n=len(g), auroc=g.auroc.mean(), brier=g.brier.mean(),
                            ece_per_dataset=g.ece.mean(), f1_thr05=g.f1_thr05.mean(), f1_oracle=g.f1_oracle.mean(),
                            fdp_at_alpha_0_1_raw=f.fdp.mean(), empty_temp_alpha_0_1=float((fc.k == 0).mean())))
        pd.DataFrame(out).to_csv(os.path.join(a.tables, f"table_breakdown_rhino{a.suffix}.csv"), index=False)

    # figure: realised vs nominal FDR for raw q(G)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    cols = ["#b03a2e", "#1f618d", "#117a65", "#7d6608", "#6c3483", "#ca6f1e"]
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.9))
    for k, grp in enumerate(("synthetic", "real")):
        ax[k].plot([0, 0.5], [0, 0.5], "k--", lw=1, label="ideal")
        for i, (tag, (label, g, fdr)) in enumerate([(t_, c) for t_, c in curves.items() if c[1] == grp]):
            d = fdr[fdr.variant == "raw"].groupby("alpha").fdp.agg(["mean", "std", "count"]).reset_index()
            h = stats.t.ppf(0.975, d["count"] - 1) * d["std"] / np.sqrt(d["count"])
            ax[k].errorbar(d.alpha, d["mean"], yerr=h, fmt="o-", ms=4, capsize=2, color=cols[i % len(cols)], label=label)
        ax[k].set_xlabel("nominal FDR budget alpha")
        ax[k].set_ylabel("realised false discovery proportion")
        ax[k].set_title("Synthetic data" if grp == "synthetic" else "Real data (aggregated graph)")
        ax[k].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(a.figs, f"fig_fdr_control_all_methods{a.suffix}.png"), dpi=200)
    plt.close(fig)

    # figure: false certainty
    fig, ax = plt.subplots(figsize=(8, 3.6))
    x = np.arange(len(summ))
    ax.bar(x - 0.2, summ.edge_rate_when_p_is_0, 0.4, color="#b03a2e", label="true edges among entries with p < 0.001")
    ax.bar(x + 0.2, 1 - summ.edge_rate_when_p_is_1, 0.4, color="#1f618d", label="non-edges among entries with p > 0.999")
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace(" (", "\n(") for s in summ.label], fontsize=6.5, rotation=0)
    ax.set_ylabel("fraction wrong although q(G) is certain")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(a.figs, f"fig_false_certainty{a.suffix}.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
