"""Build the job list for DREAM3 and Netsim (paper Sections 6.2 and 6.3).

Paper protocol: Rhino and Rhino+g are averaged over 5 runs (model seeds). PCMCI+, DYNOTEARS and VAR-LiNGAM are deterministic
(paper reports +- 0 for PCMCI+ and VAR-LiNGAM), so one run each. Netsim counts self-connections in the evaluation (flag -ede).

  rhino_env\\venv\\Scripts\\python.exe scripts\\make_real_manifest.py --out jobs_real.csv
Run scripts\\make_real_configs.py first.
"""
import argparse
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETS = ["ecoli1", "ecoli2", "yeast1", "yeast2", "yeast3"]
FIELDS = ["job_id", "method", "model_type", "config", "dataset", "dim", "gtype", "inst", "hist", "seed", "model_seed", "extra"]


def row(jid, method, mtype, cfg, ds, dim, mseed="", extra=""):
    return dict(job_id=jid, method=method, model_type=mtype, config=cfg, dataset=ds, dim=dim, gtype="", inst="", hist="",
                seed="", model_seed=mseed, extra=extra)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="jobs_real.csv")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--variants", nargs="+", default=["paper", "shipped"])
    ap.add_argument("--only", choices=["dream3", "netsim"], default=None)
    a = ap.parse_args()
    rows = []
    if a.only in (None, "netsim"):
        ds = "netsim_sim3"
        for v in a.variants:
            for tag in ("rhino", "rhino_g", "rhino_noinst"):
                for s in a.seeds:
                    rows.append(row(f"netsim_{tag}_{v}__s{s}", f"netsim_{tag}_{v}", "rhino",
                                    f"configs_m3/real/netsim_{tag}_{v}.json", ds, 15, s, "-ede"))
        for tag, mt in (("dynotears", "dynotears"), ("pcmci_plus", "pcmci_plus"), ("varlingam", "varlingam")):
            rows.append(row(f"netsim_{tag}__s0", f"netsim_{tag}", mt, f"configs_m3/real/netsim_{tag}.json", ds, 15, 0, "-ede"))
    if a.only in (None, "dream3"):
        for net in NETS:
            ds = f"dream3_100_{net}"
            for v in a.variants:
                for tag in ("rhino", "rhino_g"):
                    for s in a.seeds:
                        rows.append(row(f"dream3_{net}_{tag}_{v}__s{s}", f"dream3_{tag}_{v}", "rhino",
                                        f"configs_m3/real/dream3_{net}_{tag}_{v}.json", ds, 100, s))
            rows.append(row(f"dream3_{net}_dynotears__s0", "dream3_dynotears", "dynotears",
                            f"configs_m3/real/dream3_{net}_dynotears.json", ds, 100, 0))
            rows.append(row(f"dream3_{net}_pcmci_plus__s0", "dream3_pcmci_plus", "pcmci_plus",
                            "configs_m3/real/dream3_pcmci_plus.json", ds, 100, 0))
    with open(os.path.join(ROOT, a.out), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "jobs ->", a.out)


if __name__ == "__main__":
    main()
