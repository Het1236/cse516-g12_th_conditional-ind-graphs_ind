import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import json
import time
import traceback
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def run_one(job):
    from data import make_dataset, true_edge_vector
    from metrics import score_metrics, upper
    from official import author_dataset, run_official_uglad
    from sklearn.covariance import GraphicalLassoCV

    m, k, a = job["m"], job["k"], job["args"]
    seed = a["base_seed"] + k
    if a["generator"] == "author":
        x, theta = author_dataset(25, 0.1, m, seed)
    else:
        x, theta = make_dataset(25, 0.1, m, seed)
    y = true_edge_vector(theta)
    rows = []

    t0 = time.perf_counter()
    prec = GraphicalLassoCV().fit(x).precision_
    rows.append(("SGLCV", prec, time.perf_counter() - t0))

    t0 = time.perf_counter()
    prec = np.asarray(run_official_uglad(x, seed, a["epochs"], a["lr"], 15, a["k_fold"]), dtype=float)
    rows.append(("uGLAD", prec, time.perf_counter() - t0))

    out = []
    mats = {"x": x, "theta_true": theta}
    for name, prec, secs in rows:
        prec = (prec + prec.T) / 2.0
        mats["prec_" + name] = prec
        s = score_metrics(y, np.abs(upper(prec)))
        out.append({"method": name, "M": m, "graph": k, "seed": seed, "AUPR": s["AUPR"], "AUC": s["AUC"],
                    "n_pred_edges": int(np.sum(np.abs(upper(prec)) > 1e-10)), "n_true_edges": int(y.sum()),
                    "seconds": secs, "epochs": a["epochs"], "lr": a["lr"], "k_fold": a["k_fold"],
                    "generator": a["generator"]})
    if a.get("matrix_dir"):
        os.makedirs(a["matrix_dir"], exist_ok=True)
        np.savez_compressed(os.path.join(a["matrix_dir"], f"M{m}_g{k}.npz"), **mats)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--graphs", type=int, default=20)
    ap.add_argument("--sizes", type=int, nargs="*", default=[10, 25, 50])
    ap.add_argument("--epochs", type=int, default=250)
    ap.add_argument("--lr", type=float, default=0.002)
    ap.add_argument("--k_fold", type=int, default=3)
    ap.add_argument("--base_seed", type=int, default=2026)
    ap.add_argument("--generator", choices=["author", "mine"], default="author")
    ap.add_argument("--matrix_dir", default=None, help="folder for one .npz per dataset (data, true and learned matrices)")
    ap.add_argument("--progress", default=None, help="JSON file that monitor_progress.py reads")
    ap.add_argument("--tag", default="table1")
    args = ap.parse_args()
    a = {"epochs": args.epochs, "lr": args.lr, "k_fold": args.k_fold, "base_seed": args.base_seed,
         "generator": args.generator, "matrix_dir": args.matrix_dir}

    done = set()
    if os.path.exists(args.out):
        old = pd.read_csv(args.out)
        done = {(int(m), int(g)) for m, g in zip(old["M"], old["graph"])}
    jobs = [{"m": m, "k": k, "args": a} for k in range(args.graphs) for m in args.sizes if (m, k) not in done]
    print(f"{len(jobs)} datasets to run ({len(done)} already done). {a}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    total_all = len(jobs) + len(done)
    prog = {"tag": args.tag, "out": os.path.abspath(args.out), "total": total_all, "done": len(done), "workers": args.workers,
            "epochs": args.epochs, "generator": args.generator, "started": time.time(), "finish_times": [],
            "updated": time.time(), "finished": False}

    def write_progress(last=None):
        prog["updated"] = time.time()
        prog["last"] = last
        if args.progress:
            tmp = args.progress + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(prog, fh)
            os.replace(tmp, args.progress)

    write_progress()
    t0 = time.perf_counter()
    finished = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, j): j for j in jobs}
        for fut in as_completed(futures):
            j = futures[fut]
            try:
                rows = fut.result()
            except Exception:
                traceback.print_exc()
                continue
            pd.DataFrame(rows).to_csv(args.out, mode="a", header=not os.path.exists(args.out), index=False)
            finished += 1
            prog["done"] += 1
            prog["finish_times"].append(time.time())
            write_progress({"M": j["m"], "graph": j["k"]})
            print(f"[{finished}/{len(jobs)}] M={j['m']} graph={j['k']} elapsed {(time.perf_counter() - t0) / 60:.1f} min", flush=True)
    prog["finished"] = True
    write_progress()


if __name__ == "__main__":
    main()
