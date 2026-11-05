"""Build the job list (jobs.csv) for the synthetic experiments of the Rhino paper (Section 6.1, Appendix F).

Grid (paper, F.1): dims {5,10,20,40} x graph type {ER,SF} x instantaneous {yes,no} x history-dependent noise
{yes,no} x seeds {0..4} = 160 datasets. Edge counts: 4N instantaneous and 2N lagged, i.e. connection_factor 2.

ASSUMPTION to confirm: the paper shows one "Type" per dataset, so instantaneous and lagged graphs use the same
family here (ER_ER or SF_SF). The released generator also allows mixed pairs, which are NOT in this grid.

Run from rhino_work/ :
  python scripts/make_manifest.py --methods rhino rhino_g rhino_s dynotears varlingam pcmci_plus --out jobs.csv
Use --dims, --seeds and --methods to build smaller or larger lists.
"""
import argparse
import csv
import itertools
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# method -> (causica --model_type, config path relative to rhino_work, or "" for the shipped default config)
METHODS = {
    "rhino": ("rhino", "configs_m3/rhino.json"),
    "rhino_shipped": ("rhino", "configs_m3/rhino_shipped.json"),
    "rhino_g": ("rhino", "configs_m3/rhino_g.json"),
    "rhino_s": ("rhino", "configs_m3/rhino_s.json"),
    "rhino_lag1": ("rhino", "configs_m3/rhino_lag1.json"),
    "rhino_lag3": ("rhino", "configs_m3/rhino_lag3.json"),
    "dynotears": ("dynotears", ""),
    "varlingam": ("varlingam", ""),
    "pcmci_plus": ("pcmci_plus", ""),
}


def dataset_name(dim, gtype, inst, hist, seed, con=2, lag=2):
    flag = "HistDep" if hist else "NoHistDep"
    mid = "" if inst else "NoInst_"
    first = gtype if inst else "ER"   # the authors' generator labels the unused instantaneous graph "ER"
    return f"{first}_{gtype}_lag_{lag}_dim_{dim}_{flag}_0.5_mlp_spline_product_{mid}con_{con}_inthist_3_seed_{seed}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", type=int, nargs="+", default=[5, 10, 20, 40])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--methods", nargs="+", default=["rhino", "rhino_g", "rhino_s", "dynotears", "varlingam", "pcmci_plus"])
    ap.add_argument("--include_pcmci_dim40", action="store_true",
                    help="PCMCI+ on 40 nodes exceeded the authors' one-week limit; excluded unless asked.")
    ap.add_argument("--out", default="jobs.csv")
    a = ap.parse_args()

    rows = []
    for dim, gtype, inst, hist, seed in itertools.product(a.dims, ["ER", "SF"], [True, False], [True, False], a.seeds):
        ds = dataset_name(dim, gtype, inst, hist, seed)
        for m in a.methods:
            if m == "pcmci_plus" and dim >= 40 and not a.include_pcmci_dim40:
                continue
            mt, cfg = METHODS[m]
            rows.append(dict(job_id=f"{m}__{ds}", method=m, model_type=mt, config=cfg, dataset=ds, dim=dim,
                             gtype=gtype, inst=int(inst), hist=int(hist), seed=seed))
    rows.sort(key=lambda r: (r["dim"], r["seed"], r["method"]))   # cheap and early-seed jobs first
    with open(os.path.join(ROOT, a.out), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "jobs,", len({r["dataset"] for r in rows}), "datasets ->", a.out)


if __name__ == "__main__":
    main()
