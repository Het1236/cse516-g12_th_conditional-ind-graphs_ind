"""Live terminal view of the run. Refreshes every few seconds. Read only, safe to start and stop at any time.

  python scripts\\watch.py                 # follows jobs.csv, refresh 30 s
  python scripts\\watch.py --jobs jobs_timing.csv --every 10 --last 25
  python scripts\\watch.py --once          # print one snapshot and exit
Press Ctrl+C to leave. The workers keep running.
"""
import argparse
import csv
import glob
import json
import math
import os
import statistics
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def f(x, nd=2):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    return f"{x:.{nd}f}"


def table(header, rows):
    cols = list(zip(*([header] + rows))) if rows else [[h] for h in header]
    w = [max(len(str(c)) for c in col) for col in cols]
    line = lambda r: " | ".join(str(c).rjust(w[i]) if i >= 4 else str(c).ljust(w[i]) for i, c in enumerate(r))
    out = [line(header), "-+-".join("-" * x for x in w)]
    out += [line(r) for r in rows]
    return "\n".join(out)


def snapshot(jobs_csv, last):
    jobs = list(csv.DictReader(open(os.path.join(ROOT, jobs_csv))))
    ids = {j["job_id"] for j in jobs}
    jid_method = {j["job_id"]: j["method"] for j in jobs}
    res = []
    for p in glob.glob(os.path.join(ROOT, "results", "*.json")):
        try:
            r = json.load(open(p))
        except Exception:
            continue
        if r.get("job_id") in ids:
            r["_t"] = os.path.getmtime(p)
            res.append(r)
    done = {r["job_id"] for r in res}
    now = time.time()
    running = []
    for c in glob.glob(os.path.join(ROOT, "results", "*.claim")):
        jid = os.path.basename(c)[:-6]
        if jid in ids and jid not in done:
            running.append((jid, (now - os.path.getmtime(c)) / 60))
    st = Counter(r.get("status") for r in res)
    out = []
    out.append(f"Rhino run  |  {time.strftime('%Y-%m-%d %H:%M:%S')}  |  list: {jobs_csv}")
    out.append(f"Finished {len(res)} / {len(ids)}   running {len(running)}   waiting {len(ids) - len(res) - len(running)}   "
               + "   ".join(f"{k}: {v}" for k, v in sorted(st.items(), key=lambda kv: str(kv[0]))))
    if res:
        t0 = min(r["_t"] - r.get("wall_seconds", 0) for r in res)
        out.append(f"First finished job started about {(now - t0) / 3600:.1f} h ago")

    tot = Counter(j["method"] for j in jobs)
    fin = Counter(r["method"] for r in res)
    run = Counter(jid_method.get(jid, "?") for jid, _ in running)
    out.append("\nPROGRESS PER METHOD (finished / total, running)")
    out.append(table(["method", "done", "total", "running"], [[m, fin.get(m, 0), tot[m], run.get(m, 0)] for m in sorted(tot)]))
    te_dir = os.path.join(ROOT, "results_te")
    if os.path.isdir(te_dir):
        n_te = len(glob.glob(os.path.join(te_dir, "*.json")))
        out.append(f"Treatment-effect evaluations (Fig 2): {n_te} done, {len(glob.glob(os.path.join(te_dir, '*.claim'))) - n_te} running")

    out.append("\nMEDIAN WALL TIME (minutes), measured on finished jobs")
    g = defaultdict(list)
    for r in res:
        if r.get("wall_seconds") is not None:
            g[(r["method"], int(r["dim"]))].append(r["wall_seconds"] / 60)
    rows = [[m, d, len(v), f(statistics.median(v), 1), f(max(v), 1)] for (m, d), v in sorted(g.items())]
    out.append(table(["method", "dim", "n", "median", "max"], rows))

    out.append(f"\nLATEST {last} FINISHED JOBS (newest first). Orientation F1 unless stated. AUROC = summary graph (Netsim, DREAM3 only)")
    rows = []
    for r in sorted(res, key=lambda r: -r["_t"])[:last]:
        m = r.get("metrics") or {}
        rows.append([r["method"], r["dim"], f"{r['gtype']}", f"inst={r['inst']} hist={r['hist']}", r.get("status", "?"),
                     f(r.get("wall_seconds", float('nan')) / 60, 1), f(m.get("orientation_fscore_inst")), f(m.get("orientation_fscore_lag")),
                     f(m.get("orientation_fscore_overall_temporal")), f(m.get("adjacency_fscore_overall_temporal")),
                     f(m.get("shd_overall_temporal"), 1), f(m.get("auroc_agg"), 3), r["job_id"].split("__")[-1] if "__s" in r["job_id"] else ""])
    out.append(table(["method", "dim", "graph", "setting", "status", "min", "F1 inst", "F1 lag", "F1 temp", "adjF1 temp", "SHD temp", "AUROC", "seed"], rows))

    out.append("\nRUNNING NOW (minutes since start)")
    rows = [[jid_method.get(jid, jid.split("__")[0]), (jid.split("__", 1)[1] if jid.split("__")[0].startswith("rhino") or jid.split("__")[0] in ("dynotears", "varlingam", "pcmci_plus") else jid)[:62], f(mins, 1)] for jid, mins in sorted(running, key=lambda x: -x[1])]
    out.append(table(["method", "dataset", "min"], rows))
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", default="jobs.csv")
    ap.add_argument("--every", type=int, default=30)
    ap.add_argument("--last", type=int, default=20)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    try:
        while True:
            s = snapshot(a.jobs, a.last)
            if not a.once:
                os.system("cls" if os.name == "nt" else "clear")
            print(s, flush=True)
            if a.once:
                break
            time.sleep(a.every)
    except KeyboardInterrupt:
        pass
