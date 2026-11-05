"""Treatment-effect evaluation (paper Fig 2, Appendix D.1) on already trained synthetic Rhino models.

For every finished synthetic job of the given methods it loads the saved model (--model_dir) and runs the released
treatment-effect evaluation (-te) against interventions.json. No retraining. The likelihood part (-el) is switched off because
the released code crashes there (Rhino.log_prob receives a numpy array). ATE RMSE does not need it.

  python scripts/cate_worker.py --methods rhino rhino_g rhino_s --threads 2
Results: results_te/<job_id>.json (claim files <job_id>.claim). Safe to start many copies.
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAUSICA = os.path.join(ROOT, "causica")
OUT = os.path.join(ROOT, "results_te")
os.makedirs(OUT, exist_ok=True)


def claim(jid):
    try:
        fd = os.open(os.path.join(OUT, jid + ".claim"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def model_dir_of(jid):
    for key in (hashlib.md5(jid.encode()).hexdigest()[:10], jid):
        hits = glob.glob(os.path.join(ROOT, "runs", key, "*", "models", "*", "model.pt"))
        if hits:
            return os.path.dirname(sorted(hits)[-1])
    return None


def run_te(rec, threads):
    jid = rec["job_id"]
    md = model_dir_of(jid)
    if md is None:
        return dict(job_id=jid, status="no_model_dir")
    h = hashlib.md5(jid.encode()).hexdigest()[:10]
    scratch = os.path.join(ROOT, "runs_te", h)
    cmd = [sys.executable, "-u", "-m", "causica.run_experiment", rec["dataset"], "--model_type", "rhino",
           "-dc", "configs/dataset_config_temporal_causal_dataset.json", "-dv", "cpu", "-md", md, "-te", "-el", "-o", scratch]
    env = dict(os.environ, PYTHONPATH=CAUSICA, OMP_NUM_THREADS=str(threads), MKL_NUM_THREADS=str(threads),
               MLFLOW_TRACKING_URI="file:///" + os.path.join(ROOT, "mlruns", "te_" + h).replace("\\", "/"))
    t0 = time.time()
    with open(os.path.join(ROOT, "logs", "te_" + h + ".log"), "w") as log:
        p = subprocess.run(cmd, cwd=CAUSICA, env=env, stdout=log, stderr=subprocess.STDOUT)
    res_file = os.path.join(md, "results_interventions.json")
    out = dict(job_id=jid, method=rec["method"], dataset=rec["dataset"], dim=rec["dim"], model_dir=md,
               wall_seconds=round(time.time() - t0, 1))
    if p.returncode == 0 and os.path.isfile(res_file) and os.path.getmtime(res_file) >= t0:
        out["status"] = "ok"
        out["te"] = json.load(open(res_file)).get("test_data", {})
    else:
        out["status"] = f"error_exit_{p.returncode}"
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", nargs="+", default=["rhino", "rhino_g", "rhino_s"])
    ap.add_argument("--dims", type=int, nargs="+", default=[5, 10, 20])
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    recs = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
        r = json.load(open(f))
        if r.get("method") in a.methods and r.get("status") == "ok" and int(r.get("dim") or 0) in a.dims and r.get("seed") != "":
            recs.append(r)
    recs.sort(key=lambda r: (int(r["dim"]), r["job_id"]))
    for r in recs:
        if os.path.isfile(os.path.join(OUT, r["job_id"] + ".json")) or not claim(r["job_id"]):
            continue
        res = run_te(r, a.threads)
        json.dump(res, open(os.path.join(OUT, r["job_id"] + ".json"), "w"), indent=1)
        print(time.strftime("%H:%M:%S"), r["job_id"][:60], res["status"], flush=True)
