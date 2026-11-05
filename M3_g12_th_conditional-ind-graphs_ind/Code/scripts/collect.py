"""Merge results/*.json into results_all.csv (one row per job, every metric as a column) and print a status summary.

  python scripts/collect.py
"""
import glob
import json
import os
from collections import Counter

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
    r = json.load(open(f))
    m = r.pop("metrics", {}) or {}
    rows.append({**r, **{k: v for k, v in m.items() if isinstance(v, (int, float))}})
df = pd.DataFrame(rows)
df.to_csv(os.path.join(ROOT, "results_all.csv"), index=False)
print(len(df), "finished jobs")
if len(df):
    print(Counter(df["status"]))
    print(df.groupby(["method", "dim"])["wall_seconds"].agg(["count", "median", "max"]).round(0))
