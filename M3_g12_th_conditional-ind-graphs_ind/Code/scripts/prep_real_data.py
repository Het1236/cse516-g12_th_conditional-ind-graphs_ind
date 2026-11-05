"""Convert the raw DREAM3 (size 100) and Netsim Sim-3 downloads into the causica temporal CSV format.

Run with the isolated interpreter (the raw files are downloaded data):
  rhino_env\\venv\\Scripts\\python.exe -I scripts\\prep_real_data.py

Output: causica/data/<name>/{train.csv, val.csv, test.csv, adj_matrix.npy}
train.csv / val.csv / test.csv: no header, column 0 = series index, then one column per variable.
adj_matrix.npy: 2D summary graph, adj[i, j] = 1 means i -> j (causica convention).
"""
import glob
import os
import re

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data_real")
OUT = os.path.join(ROOT, "causica", "data")


def write_csv(path, series_list):
    """series_list: list of arrays [T, D]. Series index column = position in the list."""
    rows = [np.hstack([np.full((s.shape[0], 1), k), s]) for k, s in enumerate(series_list)]
    np.savetxt(path, np.vstack(rows), delimiter=",", fmt="%.10g")


def prep_netsim():
    name = "netsim_sim3"
    out = os.path.join(OUT, name)
    os.makedirs(out, exist_ok=True)

    def load(s):
        z = np.load(os.path.join(RAW, "netsim_raw", f"sim3_subject_{s}.npz"), allow_pickle=False)
        return z["X_np"].T.astype(float), z["Gref"].astype(int)  # [T=200, D=15], [15, 15]

    data = {s: load(s) for s in range(50)}
    g0 = data[0][1]
    assert all((data[s][1] == g0).all() for s in data), "Gref differs between subjects"
    # Paper (Appendix G.4): subjects 2-6 train, 7-8 validation. Indices are the file numbers (0-based names). Assumption.
    write_csv(os.path.join(out, "train.csv"), [data[s][0] for s in range(2, 7)])
    write_csv(os.path.join(out, "val.csv"), [data[s][0] for s in range(7, 9)])
    write_csv(os.path.join(out, "test.csv"), [data[s][0] for s in range(9, 11)])
    # Gref[i, j] = 1 means j -> i (verified with a pooled VAR(1) fit, AUROC 0.974 vs 0.861), so transpose.
    np.save(os.path.join(out, "adj_matrix.npy"), g0.T.astype(int))
    print(name, "train series 5, val 2, test 2; edges (incl. self):", int(g0.sum()))


def prep_dream3():
    base = os.path.join(RAW, "dream3_unzip", "DREAM3 in silico challenge", "Size100")
    for net in ["Ecoli1", "Ecoli2", "Yeast1", "Yeast2", "Yeast3"]:
        name = f"dream3_100_{net.lower()}"
        out = os.path.join(OUT, name)
        os.makedirs(out, exist_ok=True)
        tfile = os.path.join(base, "DREAM3 data", f"InSilicoSize100-{net}-trajectories.tsv")
        series, cur = [], []
        for line in open(tfile):
            line = line.strip()
            if line.startswith('"Time"'):
                continue
            if not line:  # a blank line separates two trajectories
                if cur:
                    series.append(np.array(cur))
                cur = []
                continue
            cur.append([float(v) for v in line.split("\t")[1:]])  # drop the time column
        if cur:
            series.append(np.array(cur))
        assert len(series) == 46 and all(s.shape == (21, 100) for s in series), (len(series), series[0].shape)
        # 80/20 split by series (paper Appendix G.1 uses 80/20 for tuning). Fixed seed. Assumption for the final fit.
        perm = np.random.RandomState(0).permutation(46)
        n_val = int(round(0.2 * 46))
        val_idx, train_idx = sorted(perm[:n_val]), sorted(perm[n_val:])
        write_csv(os.path.join(out, "train.csv"), [series[i] for i in train_idx])
        write_csv(os.path.join(out, "val.csv"), [series[i] for i in val_idx])
        write_csv(os.path.join(out, "test.csv"), [series[i] for i in val_idx])
        gfile = glob.glob(os.path.join(base, "DREAM3 gold standards", f"*Size100_{net}.txt"))[0]
        adj = np.zeros((100, 100), dtype=int)
        n_lines = 0
        for line in open(gfile):
            a, b, lab = line.split()
            i, j = int(re.sub(r"\D", "", a)) - 1, int(re.sub(r"\D", "", b)) - 1
            adj[i, j] = int(lab)  # regulator a -> target b
            n_lines += 1
        assert n_lines == 9900
        np.save(os.path.join(out, "adj_matrix.npy"), adj)
        print(name, "train", len(train_idx), "val", len(val_idx), "edges:", int(adj.sum()), "diag:", int(np.trace(adj)))


if __name__ == "__main__":
    prep_netsim()
    prep_dream3()
