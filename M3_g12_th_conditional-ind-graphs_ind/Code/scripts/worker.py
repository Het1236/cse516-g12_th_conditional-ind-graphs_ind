"""Run jobs from jobs.csv. Safe to start many copies on one machine (each job is claimed with a lock file)
and safe to split between machines with --part K --of N (static partition by job index).

  python scripts/worker.py --jobs jobs.csv --threads 2 --timeout_h 24
  python scripts/worker.py --jobs jobs.csv --part 0 --of 2          # machine A of 2
Results go to results/<job_id>.json, logs to logs/<job_id>.log, raw run folders to runs/<job_id>/.
A finished job is never re-run. Delete results/<job_id>.json (and .claim) to force a re-run.
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
CAUSICA = os.path.join(ROOT, "causica")
for d in ("results", "logs", "runs"):
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)


def claim(job_id):
    try:
        fd = os.open(os.path.join(ROOT, "results", job_id + ".claim"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def kill_tree(proc):
    try:
        parent = psutil.Process(proc.pid)
        for c in parent.children(recursive=True):
            c.kill()
        parent.kill()
    except psutil.NoSuchProcess:
        pass


def run_job(job, threads, timeout_s, device):
    jid = job["job_id"]
    # Short run folder: the long job_id pushes the TensorBoard event file past the 260 character Windows path limit,
    # the writer thread then dies and training blocks forever. Mapping job_id -> folder is hashlib.md5(job_id)[:10].
    out_dir = os.path.join(ROOT, "runs", hashlib.md5(jid.encode()).hexdigest()[:10])
    cmd = [sys.executable, "-u", "-m", "causica.run_experiment", job["dataset"], "--model_type", job["model_type"],
           "-dc", "configs/dataset_config_temporal_causal_dataset.json", "-dv", device, "-c", "-o", out_dir]
    if job["config"]:
        cmd += ["--model_config", os.path.join(ROOT, job["config"])]
    if job.get("model_seed"):
        cmd += ["--random_seed", str(job["model_seed"])]
    if job.get("extra"):
        cmd += job["extra"].split()
    # One MLflow store per job: a shared store raced when two workers created an experiment for the same dataset.
    mlflow_dir = os.path.join(ROOT, "mlruns", os.path.basename(out_dir))
    env = dict(os.environ, PYTHONPATH=CAUSICA, OMP_NUM_THREADS=str(threads), MKL_NUM_THREADS=str(threads),
               MLFLOW_TRACKING_URI="file:///" + mlflow_dir.replace("\\", "/"))
    t0 = time.time()
    status = "ok"
    with open(os.path.join(ROOT, "logs", jid + ".log"), "w") as log:
        p = subprocess.Popen(cmd, cwd=CAUSICA, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=timeout_s)
            if p.returncode != 0:
                status = f"error_exit_{p.returncode}"
        except subprocess.TimeoutExpired:
            kill_tree(p)
            status = "timeout"
    wall = time.time() - t0
    res = {}
    hits = glob.glob(os.path.join(out_dir, "**", "target_results_causality.json"), recursive=True)
    if hits:
        res = json.load(open(hits[0])).get("test_data", {})
    elif status == "ok":
        status = "no_metrics_file"
    rec = dict(job, status=status, wall_seconds=round(wall, 1), threads=threads, device=device, metrics=res)
    json.dump(rec, open(os.path.join(ROOT, "results", jid + ".json"), "w"), indent=1)
    return status, wall


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", default="jobs.csv")
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--threads", type=int, default=2, help="BLAS/torch threads per job")
    ap.add_argument("--timeout_h", type=float, default=24.0)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--only_methods", nargs="*", default=None)
    ap.add_argument("--max_jobs", type=int, default=10**9)
    a = ap.parse_args()
    jobs = list(csv.DictReader(open(os.path.join(ROOT, a.jobs))))
    jobs = [j for i, j in enumerate(jobs) if i % a.of == a.part]
    if a.only_methods:
        jobs = [j for j in jobs if j["method"] in a.only_methods]
    done = 0
    for j in jobs:
        if done >= a.max_jobs:
            break
        if os.path.isfile(os.path.join(ROOT, "results", j["job_id"] + ".json")) or not claim(j["job_id"]):
            continue
        st, w = run_job(j, a.threads, a.timeout_h * 3600, a.device)
        done += 1
        print(f"{time.strftime('%H:%M:%S')} {j['job_id']} -> {st} in {w/60:.1f} min", flush=True)
