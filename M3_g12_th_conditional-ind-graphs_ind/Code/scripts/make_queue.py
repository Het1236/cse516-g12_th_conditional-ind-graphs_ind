"""Merge the job lists into one priority-ordered queue (jobs_queue.csv). Workers take the first unclaimed job.

Order: Netsim -> DREAM3 with paper settings (by seed, so partial runs give complete seed sets) -> synthetic lag ablation (Table 1)
       -> synthetic rhino_shipped (lambda_s = 5) -> DREAM3 released configs, seeds 0-1 first (most expensive, sensitivity only).
Run after make_real_manifest.py and make_manifest.py (jobs_lag.csv, jobs_shipped_synth.csv).
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ["job_id", "method", "model_type", "config", "dataset", "dim", "gtype", "inst", "hist", "seed", "model_seed", "extra"]


def read(name):
    return list(csv.DictReader(open(os.path.join(ROOT, name))))


def by_seed(rows):
    return sorted(rows, key=lambda r: (int(r["model_seed"] or 0), r["job_id"]))


real = read("jobs_real.csv")
netsim = [r for r in real if r["job_id"].startswith("netsim")]
d3 = [r for r in real if r["job_id"].startswith("dream3")]
d3_paper = by_seed([r for r in d3 if "_shipped" not in r["job_id"]])
d3_ship = by_seed([r for r in d3 if "_shipped" in r["job_id"]])
queue = netsim + d3_paper + read("jobs_lag.csv") + read("jobs_shipped_synth.csv") + d3_ship
seen = set()
with open(os.path.join(ROOT, "jobs_queue.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, restval="")
    w.writeheader()
    for r in queue:
        assert r["job_id"] not in seen, r["job_id"]
        seen.add(r["job_id"])
        w.writerow(r)
print(len(queue), "jobs")
