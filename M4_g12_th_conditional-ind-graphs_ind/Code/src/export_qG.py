"""Export Rhino edge-probability estimates from finished runs, next to the true graphs.

Why this exists
---------------
Rhino keeps a distribution q(G) over temporal graphs. At the end of a run the official evaluation code
(causica/experiment/steps/eval_step.py) draws 100 graphs from q(G), rounds them and saves them as
<run folder>/**/adj_matrices.npy with shape [S, lag+1, N, N]. The mean over the S samples is a Monte Carlo
estimate of the marginal edge probability p_e = q(edge e = 1). We use these p_e as the "forecast" that
the calibration study checks. Nothing is retrained here.

Resolution: with S = 100 samples p_e is a multiple of 0.01 and its Monte Carlo standard error is at most 0.05.
This is stated as a limitation in the report.

What it does
------------
1. Reads results/<job_id>.json written by worker.py (status must be "ok").
2. Finds runs/<job_id>/**/adj_matrices.npy and the true graph adj_matrix.npy of the dataset.
3. Writes one small file per job: <out>/<job_id>.npz with
     probs  float32 [L+1, N, N]   estimated edge probabilities
     truth  uint8   [L+1, N, N]   true graph (same index convention as the evaluation code)
     mask   uint8   [L+1, N, N]   1 = edge is evaluated (instantaneous diagonal is excluded)
     n_samples, meta (json string)
   Netsim and DREAM3 have an aggregated 2-D truth. Then probs and truth are 2-D [N, N] and the edge is
   "any lag", the same rule the official evaluation uses.
4. Lists jobs that have no saved samples in <out>/_missing.csv, in the format of the job list, so that
   they can be re-run with worker.py (job ids get the prefix qg__ so M3 results are never overwritten).

Run (workstation, M3 python environment):
  python export_qG.py --root D:\\rhino_work --jobs jobs.csv --out qG_export --methods rhino rhino_g rhino_s
Only numpy and the standard library are needed.
"""
import argparse
import csv
import glob
import json
import os

import numpy as np


_TRUTH_CACHE = {}


def find_truth(root, dataset):
    """Look in the usual data folders first, then (slow) anywhere below root except runs/ and mlruns/."""
    if dataset in _TRUTH_CACHE:
        return _TRUTH_CACHE[dataset]
    found = None
    for base in ("causica/data", "data", "datasets", "causica/data/datasets"):
        p = os.path.join(root, base, dataset, "adj_matrix.npy")
        if os.path.isfile(p):
            found = p
            break
    if found is None:
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in ("runs", "mlruns", ".git", "logs", "results")]
            if os.path.basename(dp) == dataset and "adj_matrix.npy" in fn:
                found = os.path.join(dp, "adj_matrix.npy")
                break
    _TRUTH_CACHE[dataset] = found
    return found


def newest(paths):
    return max(paths, key=os.path.getmtime) if paths else None


def eval_mask(shape3d):
    m = np.ones(shape3d, dtype=np.uint8)
    for i in range(shape3d[1]):
        m[0, i, i] = 0  # an instantaneous self loop is impossible
    return m


def build(samples, truth):
    """samples [S, ...] binary graphs from q(G); truth numpy. Returns probs, truth, mask."""
    s = samples.astype(np.float64)
    if truth.ndim == 3:
        probs = s.mean(0)  # [L+1, N, N]
        Lp, Lt = probs.shape[0], truth.shape[0]
        if Lp != Lt:  # pad the shorter one with zeros (same idea as make_temporal_adj_matrix_compatible)
            L = max(Lp, Lt)
            pp = np.zeros((L,) + probs.shape[1:])
            pp[:Lp] = probs
            tt = np.zeros((L,) + truth.shape[1:])
            tt[:Lt] = truth
            probs, truth = pp, tt
        return probs, truth, eval_mask(truth.shape)
    # aggregated truth: edge present if present at any lag, per sample, then averaged
    if s.ndim == 3:
        s = s[:, None]
    agg = (s.sum(1) > 0).astype(np.float64)  # [S, N, N]
    probs = agg.mean(0)
    return probs, truth, np.ones_like(truth, dtype=np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="folder that holds results/, runs/ and causica/")
    ap.add_argument("--jobs", nargs="+", default=["jobs.csv"],
                    help="job list(s), relative to root or absolute. Used only for the missing report.")
    ap.add_argument("--out", default="qG_export")
    ap.add_argument("--methods", nargs="+", default=["auto"],
                    help="values of the 'method' column, or 'auto' = every method whose name contains 'rhino'")
    ap.add_argument("--inventory", action="store_true", help="only count what is there, write nothing")
    a = ap.parse_args()

    recs = []
    for f in sorted(glob.glob(os.path.join(a.root, "results", "*.json"))):
        try:
            recs.append(json.load(open(f)))
        except Exception as e:  # a half written file must not stop the export
            print("cannot read", f, e)
    methods = sorted({r.get("method", "") for r in recs if "rhino" in r.get("method", "").lower()})         if a.methods == ["auto"] else a.methods
    print("methods:", methods)

    all_jobs = []
    for jf in a.jobs:
        p = os.path.join(a.root, jf)
        if os.path.isfile(p):
            all_jobs += list(csv.DictReader(open(p)))
    job_by_id = {j["job_id"]: j for j in all_jobs}

    if not a.inventory:
        os.makedirs(a.out, exist_ok=True)
    inv = {}
    done, missing = [], []
    for rec in recs:
        m = rec.get("method")
        if m not in methods:
            continue
        row = inv.setdefault(m, dict(results=0, ok=0, with_samples=0, with_truth=0))
        row["results"] += 1
        if rec.get("status") != "ok":
            continue
        row["ok"] += 1
        jid = rec["job_id"]
        npy = newest(glob.glob(os.path.join(a.root, "runs", jid, "**", "adj_matrices.npy"), recursive=True))
        tpath = find_truth(a.root, rec["dataset"])
        row["with_samples"] += npy is not None
        row["with_truth"] += tpath is not None
        if npy is None or tpath is None:
            missing.append((jid, "no adj_matrices.npy" if npy is None else "no adj_matrix.npy of dataset"))
            continue
        if a.inventory:
            continue
        samples = np.load(npy, allow_pickle=True)
        truth = np.load(tpath)
        probs, truth, mask = build(samples, truth)
        meta = {k: rec.get(k) for k in ("job_id", "method", "dataset", "dim", "gtype", "inst", "hist", "seed",
                                         "model_seed", "wall_seconds", "device")}
        meta["metrics_from_M3"] = {k: v for k, v in (rec.get("metrics") or {}).items()
                                   if k in ("auroc_agg", "orientation_fscore_overall_temporal",
                                            "adjacency_fscore_overall_temporal", "orientation_fscore_agg")}
        np.savez_compressed(os.path.join(a.out, jid + ".npz"), probs=probs.astype(np.float32),
                            truth=truth.astype(np.uint8), mask=mask, n_samples=np.array(samples.shape[0]),
                            meta=json.dumps(meta))
        done.append(jid)

    print()
    print("%-32s %8s %8s %13s %11s" % ("method", "results", "ok", "with_samples", "with_truth"))
    for m, r in sorted(inv.items()):
        print("%-32s %8d %8d %13d %11d" % (m, r["results"], r["ok"], r["with_samples"], r["with_truth"]))
    print()
    print(f"exported {len(done)} jobs;{len(missing)} finished jobs cannot be exported.")
    for m in missing[:10]:
        print("  cannot export:", m)
    if a.inventory:
        return
    cols = []
    for j in all_jobs:
        for k in j:
            if k not in cols:
                cols.append(k)
    with open(os.path.join(a.out, "_missing.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols or ["job_id"], restval="", extrasaction="ignore")
        w.writeheader()
        for jid, _ in missing:
            if jid in job_by_id:
                jj = dict(job_by_id[jid])
                jj["job_id"] = "qg__" + jid
                w.writerow(jj)
    print("Re-run list for the missing ones:", os.path.join(a.out, "_missing.csv"))


if __name__ == "__main__":
    main()
