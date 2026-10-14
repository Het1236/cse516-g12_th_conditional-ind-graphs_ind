import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import glob
import re
import time
import traceback
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def run_one(job):
    from data import minmax_scale, true_edge_vector
    from metrics import score_metrics, upper
    from uglad_model import fit_uglad

    d = np.load(job["path"])
    x, theta = d["x"], d["theta_true"]
    y = true_edge_vector(theta)
    t0 = time.perf_counter()
    prec, info = fit_uglad(minmax_scale(x), mode="cv", epochs=job["epochs"], lr=job["lr"], n_steps=15, k_fold=3,
                           seed=job["seed"], offset=0.1, hidden=3)
    secs = time.perf_counter() - t0
    prec = (np.asarray(prec, dtype=float) + np.asarray(prec, dtype=float).T) / 2.0
    s = score_metrics(y, np.abs(upper(prec)))
    os.makedirs(job["mat_dir"], exist_ok=True)
    np.savez_compressed(os.path.join(job["mat_dir"], os.path.basename(job["path"])), prec_mine=prec)
    return {"method": "uGLAD-mine", "M": job["m"], "graph": job["k"], "seed": job["seed"], "AUPR": s["AUPR"], "AUC": s["AUC"],
            "n_pred_edges": int(np.sum(np.abs(upper(prec)) > 1e-10)), "n_true_edges": int(y.sum()), "seconds": secs,
            "epochs": job["epochs"], "lr": job["lr"], "n_parameters": info.get("n_parameters")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=250)
    ap.add_argument("--lr", type=float, default=0.002)
    ap.add_argument("--base_seed", type=int, default=2026)
    a = ap.parse_args()
    out = os.path.join(a.folder, "mine_raw.csv")
    mat_dir = os.path.join(a.folder, "mine_matrices")
    done = set()
    if os.path.exists(out):
        old = pd.read_csv(out)
        done = {(int(m), int(g)) for m, g in zip(old["M"], old["graph"])}
    jobs = []
    for p in sorted(glob.glob(os.path.join(a.folder, "matrices", "M*_g*.npz"))):
        m, k = map(int, re.match(r"M(\d+)_g(\d+)\.npz", os.path.basename(p)).groups())
        if (m, k) not in done:
            jobs.append({"path": p, "m": m, "k": k, "seed": a.base_seed + k, "epochs": a.epochs, "lr": a.lr, "mat_dir": mat_dir})
    print(f"{len(jobs)} datasets to run ({len(done)} done)", flush=True)
    t0 = time.perf_counter()
    n = 0
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(run_one, j): j for j in jobs}
        for f in as_completed(futs):
            try:
                row = f.result()
            except Exception:
                traceback.print_exc()
                continue
            pd.DataFrame([row]).to_csv(out, mode="a", header=not os.path.exists(out), index=False)
            n += 1
            print(f"[{n}/{len(jobs)}] M={row['M']} graph={row['graph']} {(time.perf_counter() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
