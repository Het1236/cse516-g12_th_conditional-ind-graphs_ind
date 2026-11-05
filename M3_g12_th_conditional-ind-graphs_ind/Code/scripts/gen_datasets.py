"""Generate every dataset named in jobs.csv with the authors' generator, in parallel, skipping existing ones.

Run from rhino_work/ with the venv python:  python scripts/gen_datasets.py --jobs jobs.csv --procs 8
"""
import argparse
import csv
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAUSICA = os.path.join(ROOT, "causica")


def gen(row):
    path = os.path.join(CAUSICA, "data", row["dataset"])
    if os.path.isfile(os.path.join(path, "adj_matrix.npy")) and os.path.isfile(os.path.join(path, "train.csv")):
        return row["dataset"], "exists"
    inst = "none" if row["inst"] == "0" else row["gtype"]
    cmd = [sys.executable, os.path.join(ROOT, "scripts", "gen_one.py"), "--dim", row["dim"], "--inst", inst,
           "--lagtype", row["gtype"], "--hist", row["hist"], "--con", "2", "--seed", row["seed"],
           "--save_dir", os.path.join(CAUSICA, "data")]
    env = dict(os.environ, PYTHONPATH=CAUSICA, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    r = subprocess.run(cmd, cwd=CAUSICA, env=env, capture_output=True, text=True)
    ok = r.returncode == 0 and os.path.isfile(os.path.join(path, "train.csv"))
    return row["dataset"], "ok" if ok else "FAILED: " + r.stderr[-300:]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", default="jobs.csv")
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    seen, rows = set(), []
    for r in csv.DictReader(open(os.path.join(ROOT, a.jobs))):
        if r["dataset"] not in seen:
            seen.add(r["dataset"])
            rows.append(r)
    with ThreadPoolExecutor(a.procs) as ex:
        for i, (name, status) in enumerate(ex.map(gen, rows), 1):
            print(f"[{i}/{len(rows)}] {name}: {status}", flush=True)
