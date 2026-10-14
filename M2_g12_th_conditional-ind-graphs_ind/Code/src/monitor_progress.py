import argparse
import json
import os
import shutil
import statistics
import sys
import time

import pandas as pd

BAR = 40


def fmt(seconds):
    seconds = int(max(0, seconds))
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


def estimate(prog):
    left = prog["total"] - prog["done"]
    ft = list(prog.get("finish_times", []))
    if left <= 0:
        return 0.0, None
    for i in range(len(ft) - 1, 0, -1):
        if ft[i] - ft[i - 1] > 1800:
            ft = ft[i:]
            break
    ft = ft[-16:]
    if len(ft) < 4 or ft[-1] - ft[0] <= 0:
        return None, None
    rate = (len(ft) - 1) / (ft[-1] - ft[0])
    return left / rate, rate * 60.0


def draw(path):
    with open(path) as f:
        p = json.load(f)
    total, done = max(p["total"], 1), p["done"]
    frac = done / total
    filled = int(BAR * frac)
    bar = "#" * filled + "-" * (BAR - filled)
    eta, rate = estimate(p)
    active = [t for t in p.get("finish_times", [])]
    elapsed = (active[-1] - p["started"]) if active else (time.time() - p["started"])
    lines = []
    state = "FINISHED" if p.get("finished") else ("running" if time.time() - p["updated"] < 900 else "no update for a while")
    lines.append(f"{p['tag']}   ({p['generator']} generator, {p['epochs']} epochs, {p['workers']} workers)   [{state}]")
    lines.append(f"[{bar}] {done}/{p['total']}  {100 * frac:5.1f}%")
    if p.get("finished") or done >= p["total"]:
        lines.append(f"time used {fmt(elapsed)}    time left 0:00:00    all datasets done")
    elif rate:
        lines.append(f"time used {fmt(elapsed)}    time left {fmt(eta)}    speed {rate:.2f} datasets/min")
    else:
        lines.append(f"time used {fmt(elapsed)}    time left estimating...")
    if p.get("last"):
        lines.append(f"last finished: M={p['last']['M']}  graph={p['last']['graph']}")
    try:
        df = pd.read_csv(p["out"])
        t = df.groupby(["method", "M"])["AUPR"].agg(["mean", "count"]).round(3)
        lines.append("")
        lines.append("running mean AUPR (number of graphs in brackets)")
        sizes = sorted(df.M.unique())
        lines.append("  method   " + "".join(f"M={s:<4d}          " for s in sizes))
        for m in sorted(df.method.unique()):
            cells = []
            for s in sizes:
                if (m, s) in t.index:
                    cells.append(f"{t.loc[(m, s), 'mean']:.3f} ({int(t.loc[(m, s), 'count']):2d})   ")
                else:
                    cells.append("   -            ")
            lines.append(f"  {m:<8s} " + "".join(cells))
        e = df[df.method == "uGLAD"]
        if len(e):
            lines.append(f"  uGLAD empty graphs so far: {int((e.n_pred_edges == 0).sum())} of {len(e)}")
    except Exception:
        pass
    lines.append("")
    lines.append(f"results file: {p['out']}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("progress", nargs="+")
    ap.add_argument("--every", type=float, default=2.0)
    a = ap.parse_args()
    try:
        while True:
            out = ["uGLAD reproduction   (Ctrl+C to leave this window, the run keeps going)", "=" * 70, ""]
            for path in a.progress:
                if os.path.exists(path):
                    try:
                        out += draw(path) + ["", "-" * 70, ""]
                    except Exception as e:
                        out += [f"{path}: could not read yet ({e})", ""]
                else:
                    out += [f"waiting for {path}", ""]
            sys.stdout.write("\033[H\033[J" + "\n".join(out) + "\n")
            sys.stdout.flush()
            time.sleep(a.every)
    except KeyboardInterrupt:
        print("bye")


if __name__ == "__main__":
    main()
