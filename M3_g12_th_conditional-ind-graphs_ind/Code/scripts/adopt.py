"""Finish jobs whose training process outlived its worker.

Why this exists: worker.py kills a job after --timeout_h (10 h in the main queue). Some DREAM3 paper-setting jobs need more
(measured: about 9.6 to 10.5 min per aug-Lag step with 80 steps for Ecoli2 Rhino and Yeast2 Rhino, 125 steps for Yeast2 Rhino+g).
For these jobs the worker process was stopped on purpose and the training process was left running.
This script waits for each training process, then writes results/<job_id>.json in the same format as worker.py.
When a job ends it starts one new worker (same command as run_full.ps1) so that the CPU slot is not lost.

  python scripts\adopt.py --jobs jobs_queue.csv --pid dream3_ecoli2_rhino_paper__s2=29864 --pid ...
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

import psutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def finish(job, pid, threads, k):
    jid = job["job_id"]
    out_dir = os.path.join(ROOT, "runs", hashlib.md5(jid.encode()).hexdigest()[:10])
    claim = os.path.join(ROOT, "results", jid + ".claim")
    t0 = os.path.getmtime(claim)
    try:
        psutil.Process(pid).wait()
    except psutil.NoSuchProcess:
        pass
    wall = time.time() - t0
    hits = glob.glob(os.path.join(out_dir, "**", "target_results_causality.json"), recursive=True)
    res, status = {}, "ok"
    if hits:
        res = json.load(open(hits[0])).get("test_data", {})
    else:
        status = "no_metrics_file"
    rec = dict(job, status=status, wall_seconds=round(wall, 1), threads=threads, device="cpu", metrics=res, note="adopted after worker was stopped")
    json.dump(rec, open(os.path.join(ROOT, "results", jid + ".json"), "w"), indent=1)
    print(f"{time.strftime('%H:%M:%S')} {jid} -> {status} in {wall / 60:.1f} min", flush=True)
    py = os.path.join(ROOT, "rhino_env", "venv", "Scripts", "python.exe")
    cmd = [py, "-u", "scripts\\worker.py", "--jobs", a.jobs, "--threads", str(threads), "--timeout_h", "10"]
    flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(cmd, cwd=ROOT, creationflags=flags, stdout=open(os.path.join(ROOT, "logs", f"full_worker_adopt_{k}.out"), "w"),
                     stderr=subprocess.STDOUT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", default="jobs_queue.csv")
    ap.add_argument("--pid", action="append", required=True, help="job_id=PID of the process that runs training")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    rows = {j["job_id"]: j for j in csv.DictReader(open(os.path.join(ROOT, a.jobs)))}
    todo = [(rows[x.split("=")[0]], int(x.split("=")[1])) for x in a.pid]
    import threading
    ts = [threading.Thread(target=finish, args=(j, p, a.threads, i)) for i, (j, p) in enumerate(todo)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
