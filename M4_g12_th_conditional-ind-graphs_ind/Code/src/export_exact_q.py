"""Export the EXACT edge probabilities of Rhino's q(G) from the saved model weights (no training, no causica import).

Why: export_qG.py estimates p_e from 100 sampled graphs. That gives a resolution of 0.01 and many ties at 0 and 1.
The exact p_e is a function of the learned logits stored in model.pt, next to adj_matrices.npy:
  * instantaneous part (causica VarDistA_temporal "temporal_three"): for every node pair (i > j) a 3-way categorical
    over {edge j->i, edge i->j, no edge} = softmax(logits[:, pair]).  Index 0 fills the lower triangle, index 1 the
    upper triangle, index 2 is "no edge" (causica/models/deci/variational_distributions.py, ThreeWayGraphDist).
  * lagged part: independent Bernoulli per (lag, i, j), p = softmax(logits_lag, dim 0)[1].
For a 2-D (aggregated) truth (Netsim, DREAM3) the edge i,j exists if it exists at any lag. The lags are independent
under q, so P(any lag) = 1 - prod_l (1 - p_l)  (exact under q).

Built-in check: the Monte Carlo mean of the saved samples must agree with the exact value up to sampling noise
(standard error <= 0.05 for 100 samples). The script reports the largest and mean difference per job in exact_check.csv.
If the mapping were wrong (for example transposed), the difference would be large.

Run (workstation, M3 python env, needs torch only to read model.pt):
  python export_exact_q.py --root D:\\rhino_work --jobs jobs.csv jobs_real.csv --out qG_exact --methods auto
"""
import argparse
import csv
import glob
import json
import os

import numpy as np

from export_qG import build, eval_mask, find_truth, newest  # same folder


def softmax(x, axis=0):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def exact_temporal_probs(logits, logits_lag):
    """logits: [3, N(N-1)/2], logits_lag: [2, lag, N, N] (float64 numpy). Returns probs, logodds of shape [lag+1, N, N]."""
    n = logits_lag.shape[-1]
    lag = logits_lag.shape[1]
    lower = np.tril_indices(n, -1)
    p = softmax(logits, 0)
    # log-odds of each category against the other two (stable)
    lo = np.empty_like(logits)
    for k in range(3):
        others = [j for j in range(3) if j != k]
        lo[k] = logits[k] - np.logaddexp(logits[others[0]], logits[others[1]])
    probs = np.zeros((lag + 1, n, n))
    logodds = np.full((lag + 1, n, n), -np.inf)
    probs[0][lower[0], lower[1]] = p[0]
    probs[0][lower[1], lower[0]] = p[1]
    logodds[0][lower[0], lower[1]] = lo[0]
    logodds[0][lower[1], lower[0]] = lo[1]
    pl = softmax(logits_lag, 0)[1]
    probs[1:] = pl
    logodds[1:] = logits_lag[1] - logits_lag[0]
    return probs, logodds


def main():
    import torch  # only needed to read model.pt

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--jobs", nargs="+", default=["jobs.csv"])
    ap.add_argument("--out", default="qG_exact")
    ap.add_argument("--methods", nargs="+", default=["auto"])
    ap.add_argument("--max_jobs", type=int, default=10 ** 9)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    recs = []
    for f in sorted(glob.glob(os.path.join(a.root, "results", "*.json"))):
        try:
            recs.append(json.load(open(f)))
        except Exception as e:
            print("cannot read", f, e)
    methods = sorted({r.get("method", "") for r in recs if "rhino" in r.get("method", "").lower()}) \
        if a.methods == ["auto"] else a.methods
    print("methods:", methods)

    rows, n_done, n_fail = [], 0, 0
    for rec in recs:
        if rec.get("method") not in methods or rec.get("status") != "ok":
            continue
        if n_done >= a.max_jobs:
            break
        jid = rec["job_id"]
        npy = newest(glob.glob(os.path.join(a.root, "runs", jid, "**", "adj_matrices.npy"), recursive=True))
        tpath = find_truth(a.root, rec["dataset"])
        mdl = os.path.join(os.path.dirname(npy), "model.pt") if npy else None
        if not (npy and tpath and os.path.isfile(mdl)):
            print("skip", jid, "(missing adj_matrices.npy, truth or model.pt)")
            n_fail += 1
            continue
        try:
            sd = torch.load(mdl, map_location="cpu")
            kl = [k for k in sd if k.endswith("var_dist_A.logits")]
            kg = [k for k in sd if k.endswith("var_dist_A.logits_lag")]
            if len(kl) != 1 or len(kg) != 1:
                raise KeyError("logits keys not found: " + str([k for k in sd if "logit" in k]))
            logits = sd[kl[0]].double().numpy()
            logits_lag = sd[kg[0]].double().numpy()
            probs3, lo3 = exact_temporal_probs(logits, logits_lag)
        except Exception as e:
            print("FAILED", jid, repr(e))
            n_fail += 1
            continue

        truth = np.load(tpath)
        samples = np.load(npy, allow_pickle=True)
        mc, truth_b, mask = build(samples, truth)
        if truth.ndim == 3:
            ex, t_out, lo = probs3, truth_b, lo3
            if ex.shape != mc.shape:  # lag of truth differs: pad like build() does
                L = max(ex.shape[0], mc.shape[0])
                pad = np.zeros((L,) + ex.shape[1:])
                pad[: ex.shape[0]] = ex
                ex = pad
                lo = np.concatenate([lo, np.full((L - lo.shape[0],) + lo.shape[1:], -np.inf)], 0)
            logodds = lo
        else:
            ex = 1.0 - np.prod(1.0 - probs3, axis=0)
            t_out, logodds = truth_b, None
        d = np.abs(ex - mc)
        m = mask.astype(bool)
        rows.append(dict(job_id=jid, method=rec["method"], max_abs_diff=float(d[m].max()), mean_abs_diff=float(d[m].mean()),
                         frac_exact_gt_0999=float((ex[m] > 0.999).mean()), frac_exact_lt_0001=float((ex[m] < 0.001).mean())))
        meta = {k: rec.get(k) for k in ("job_id", "method", "dataset", "dim", "gtype", "inst", "hist", "seed", "model_seed",
                                         "wall_seconds", "device")}
        meta["exact"] = True
        kw = dict(probs=ex.astype(np.float64), truth=t_out.astype(np.uint8), mask=mask, n_samples=np.array(10 ** 6),
                  meta=json.dumps(meta))
        if logodds is not None:
            kw["logodds"] = logodds
        np.savez_compressed(os.path.join(a.out, jid + ".npz"), **kw)
        n_done += 1
        if n_done % 50 == 0:
            print("done", n_done)

    with open(os.path.join(a.out, "exact_check.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["job_id"])
        w.writeheader()
        w.writerows(rows)
    if rows:
        md = np.array([r["max_abs_diff"] for r in rows])
        me = np.array([r["mean_abs_diff"] for r in rows])
        print(f"\nexported {n_done} jobs, failed {n_fail}. exact vs 100-sample mean: "
              f"mean abs diff {me.mean():.4f} (largest per job {me.max():.4f}); max abs diff {md.max():.3f} "
              f"(expected up to about 0.15 from sampling noise only)")


if __name__ == "__main__":
    main()
