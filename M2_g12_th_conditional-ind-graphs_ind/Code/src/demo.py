import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from baselines import run_bcd
from data import make_dataset, sample_gaussian, true_edge_vector
from ggm import GaussianGraphicalModel
from metrics import (binary_structure_metrics, conditional_prediction_rmse, heldout_nll, score_metrics, upper)
from uglad_model import fit_uglad


def draw(ax, true_adj, pred_adj, title):
    d = true_adj.shape[0]
    g = nx.Graph()
    g.add_nodes_from(range(d))
    pos = nx.circular_layout(g)
    for i in range(d):
        for j in range(i + 1, d):
            t, p = bool(true_adj[i, j]), bool(pred_adj[i, j])
            if t and p:
                nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color="black", width=1.8)
            elif p and not t:
                nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color="#7D1916", width=1.4, style="dashed")
            elif t and not p:
                nx.draw_networkx_edges(g, pos, [(i, j)], ax=ax, edge_color="#999999", width=1.2, style="dotted")
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color="white", edgecolors="#7D1916", node_size=380)
    nx.draw_networkx_labels(g, pos, {i: str(i + 1) for i in range(d)}, ax=ax, font_size=8)
    ax.set_title(title, fontsize=9)
    ax.axis("off")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=25)
    ap.add_argument("--m", type=int, default=50)
    ap.add_argument("--p", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--epochs", type=int, default=250)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "..", "Results", "demo"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    print("STEP 1  Generate data from a known Gaussian graphical model")
    x, theta = make_dataset(a.d, a.p, a.m, a.seed, generator="authors")
    x_test = sample_gaussian(theta, 1000, np.random.default_rng(a.seed + 10 ** 6))
    y = true_edge_vector(theta)
    iu = np.triu_indices(a.d, 1)
    true_adj = np.zeros((a.d, a.d), dtype=bool)
    true_adj[iu] = y.astype(bool)
    true_adj = true_adj | true_adj.T
    print(f"        {a.d} variables, {a.m} samples, {int(y.sum())} true edges out of {len(y)} possible pairs")

    print("STEP 2  Scale every column to [0, 1]. Both methods get exactly this matrix")
    lo, hi = x.min(axis=0), x.max(axis=0)
    span = np.where(hi - lo > 0, hi - lo, 1.0)
    xs = (x - lo) / span
    xt = (x_test - lo) / span - xs.mean(axis=0)
    theta_scaled = theta * np.outer(span, span)

    print("STEP 3  Learn the graph with graphical lasso (block coordinate descent, penalty by 3-fold CV)")
    t0 = time.perf_counter()
    prec_bcd, info = run_bcd(xs)
    print(f"        done in {time.perf_counter() - t0:.1f} s, chosen penalty {info['alpha']:.4f}")

    print(f"STEP 4  Learn the graph with uGLAD (15 unrolled steps, {a.epochs} epochs, 3-fold CV, no labels used)")
    t0 = time.perf_counter()
    prec_ug, info_ug = fit_uglad(xs, mode="cv", epochs=a.epochs, seed=a.seed)
    print(f"        done in {time.perf_counter() - t0:.1f} s, {info_ug['n_parameters']} learnable parameters, "
          f"best epoch {info_ug['best_epoch'] + 1} of {a.epochs}")

    print("STEP 5  Score both against the true graph")
    rows = []
    for name, prec in (("graphical lasso", prec_bcd), ("uGLAD", prec_ug)):
        prec = (prec + prec.T) / 2.0
        sc = np.abs(upper(prec))
        r = {"method": name}
        r.update(binary_structure_metrics(y, sc > 1e-10))
        r.update(score_metrics(y, sc))
        r["nll"] = heldout_nll(prec, xt)
        r["rmse"] = conditional_prediction_rmse(prec, xt)
        rows.append(r)
    print(f"        {'method':16s} {'edges':>6s} {'SHD':>5s} {'prec':>6s} {'recall':>7s} {'F1':>6s} {'AUPR':>6s} {'AUC':>6s} {'NLL':>8s} {'RMSE':>6s}")
    for r in rows:
        print(f"        {r['method']:16s} {r['n_pred_edges']:6d} {r['SHD']:5d} {r['precision']:6.3f} {r['recall']:7.3f} "
              f"{r['F1']:6.3f} {r['AUPR']:6.3f} {r['AUC']:6.3f} {r['nll']:8.2f} {r['rmse']:6.3f}")
    print(f"        reference: the true model has NLL {heldout_nll(theta_scaled, xt):.2f} and RMSE "
          f"{conditional_prediction_rmse(theta_scaled, xt):.3f} on the same test data")

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.4))
    draw(axes[0], true_adj, true_adj, f"True graph ({int(y.sum())} edges)")
    for ax, (name, prec) in zip(axes[1:], (("Graphical lasso", prec_bcd), ("uGLAD", prec_ug))):
        adj = np.abs((prec + prec.T) / 2) > 1e-10
        np.fill_diagonal(adj, False)
        tp = int((adj & true_adj).sum() // 2)
        draw(ax, true_adj, adj, f"{name}: {tp} correct, {int((adj & ~true_adj).sum() // 2)} extra, {int((~adj & true_adj).sum() // 2)} missed")
    fig.text(0.5, 0.02, "black solid = correct edge, dashed maroon = extra edge, dotted gray = missed edge", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(os.path.join(a.out, "demo_graphs.png"), dpi=170)
    plt.close(fig)
    print(f"        figure saved to {os.path.abspath(os.path.join(a.out, 'demo_graphs.png'))}")

    model, label = GaussianGraphicalModel(prec_ug), "uGLAD"
    if not model.edges:
        model, label = GaussianGraphicalModel(prec_bcd), "graphical lasso (the uGLAD graph is empty in this run)"
    print(f"STEP 6  Inference with the learned model: {label}. Exact, closed form")
    pc = model.partial_correlation
    edges = sorted(model.edges, key=lambda e: -abs(pc[e]))[:5]
    if edges:
        print("        strongest direct links (partial correlation):")
        for i, j in edges:
            print(f"          X{i + 1} - X{j + 1}: {pc[i, j]:+.3f}")
        pair = edges[0]
    else:
        print("        no edges in this run, so every pair is declared conditionally independent")
        pair = (0, 1)
    print(f"        query 1: are X{pair[0] + 1} and X{pair[1] + 1} independent given all other variables?  "
          f"{model.is_conditionally_independent(*pair)}")
    row = xt[0]
    k = pair[0]
    print(f"        query 2: predict X{k + 1} from all other variables for one test sample")
    print(f"          actual {row[k]:+.3f},  this model {model.predict_node(k, row):+.3f},  "
          f"true model {GaussianGraphicalModel(theta_scaled).predict_node(k, row):+.3f}")
    given = [k + 1, k + 2, k + 3]
    given = [g for g in given if g < a.d][:3]
    target = [k]
    mean, cov = model.conditional(target, given, row[given])
    print(f"        query 3: distribution of X{k + 1} given X{', X'.join(str(g + 1) for g in given)} = {np.round(row[given], 3).tolist()}")
    print(f"          mean {np.round(mean, 3).tolist()},  standard deviation {np.round(np.sqrt(np.diag(cov)), 3).tolist()}")
    print("DONE")


if __name__ == "__main__":
    main()
