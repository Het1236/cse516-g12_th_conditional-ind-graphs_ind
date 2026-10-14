import argparse
import glob
import os
import re

import numpy as np
import pandas as pd

from data import sample_gaussian
from metrics import conditional_prediction_rmse, heldout_nll, is_positive_definite


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True)
    ap.add_argument("--base_seed", type=int, default=2026)
    ap.add_argument("--n_test", type=int, default=1000)
    a = ap.parse_args()
    rows = []
    for p in sorted(glob.glob(os.path.join(a.folder, "matrices", "M*_g*.npz"))):
        m, k = map(int, re.match(r"M(\d+)_g(\d+)\.npz", os.path.basename(p)).groups())
        d = np.load(p)
        x, theta = d["x"], d["theta_true"]
        span = x.max(axis=0) - x.min(axis=0)
        scale = 1.0 / np.outer(span, span)
        rng = np.random.default_rng(a.base_seed + k + 10 ** 6)
        xt = sample_gaussian(theta, a.n_test, rng) - x.mean(axis=0)
        precs = {"True model": theta, "SGLCV": d["prec_SGLCV"], "uGLAD": d["prec_uGLAD"] * scale}
        mp = os.path.join(a.folder, "mine_matrices", os.path.basename(p))
        if os.path.exists(mp):
            precs["uGLAD-mine"] = np.load(mp)["prec_mine"] * scale
        for name, prec in precs.items():
            prec = (prec + prec.T) / 2.0
            rows.append({"method": name, "M": m, "graph": k, "NLL": heldout_nll(prec, xt),
                         "RMSE": conditional_prediction_rmse(prec, xt), "pos_def": bool(is_positive_definite(prec))})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(a.folder, "kpis_raw.csv"), index=False)
    summ = df.groupby(["method", "M"])[["NLL", "RMSE"]].agg(["mean", "std"]).round(3)
    summ.to_csv(os.path.join(a.folder, "kpis_summary.csv"))
    with open(os.path.join(a.folder, "kpis_summary.md"), "w", encoding="utf-8") as f:
        f.write(summ.to_markdown())
    print(df.groupby(["method", "M"])[["NLL", "RMSE"]].mean().round(3).unstack(0).to_string())
    print("not positive definite:", df[~df.pos_def].groupby(["method", "M"]).size().to_dict())


if __name__ == "__main__":
    main()
