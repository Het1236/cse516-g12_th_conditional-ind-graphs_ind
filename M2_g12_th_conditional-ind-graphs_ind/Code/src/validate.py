import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.linalg
import torch

from baselines import _cpdag_to_adjacency, _dag_to_adjacency
from data import make_dataset, make_precision, minmax_scale, sample_gaussian, true_edge_vector
from ggm import GaussianGraphicalModel
from metrics import binary_structure_metrics, score_metrics, upper
from uglad_model import SymSqrt, UGladNet, classical_am, covariance_with_offset, fit_uglad, sym_sqrt

torch.set_num_threads(1)
CHECKS = []


def record(name, what, measured, criterion, passed, note=""):
    CHECKS.append({"check": name, "what is compared": what, "measured": measured,
                   "criterion": criterion, "pass": bool(passed), "note": note})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {measured}  ({criterion})", flush=True)


def check_ci_identity():
    rng = np.random.default_rng(0)
    d = 25
    theta = make_precision(d, 0.1, rng)
    model = GaussianGraphicalModel(theta)
    sigma = model.covariance
    formula = model.partial_correlation
    worst = 0.0
    zero_pair_worst = 0.0
    for i in range(d):
        for j in range(i + 1, d):
            rest = [k for k in range(d) if k not in (i, j)]
            a = [i, j]
            schur = sigma[np.ix_(a, a)] - sigma[np.ix_(a, rest)] @ np.linalg.solve(sigma[np.ix_(rest, rest)], sigma[np.ix_(rest, a)])
            pcorr = schur[0, 1] / np.sqrt(schur[0, 0] * schur[1, 1])
            worst = max(worst, abs(pcorr - formula[i, j]))
            if not model.adjacency[i, j]:
                zero_pair_worst = max(zero_pair_worst, abs(pcorr))
    record("V1a partial correlation formula",
           "P_ij = -Theta_ij / sqrt(Theta_ii Theta_jj) against the partial correlation computed from the covariance (Schur complement), all 300 pairs",
           f"max error {worst:.2e}", "below 1e-9", worst < 1e-9)
    record("V1b zero in Theta means conditional independence",
           "partial correlation of every pair with Theta_ij = 0, computed independently from the covariance",
           f"max |partial correlation| {zero_pair_worst:.2e}", "below 1e-9", zero_pair_worst < 1e-9)

    x = sample_gaussian(theta, 300000, np.random.default_rng(1))
    errs = []
    pairs = [(i, j) for i in range(d) for j in range(i + 1, d)][:40] + [e for e in model.edges][:20]
    for i, j in pairs:
        rest = [k for k in range(d) if k not in (i, j)]
        design = x[:, rest]
        ri = x[:, i] - design @ np.linalg.lstsq(design, x[:, i], rcond=None)[0]
        rj = x[:, j] - design @ np.linalg.lstsq(design, x[:, j], rcond=None)[0]
        errs.append(abs(np.corrcoef(ri, rj)[0, 1] - formula[i, j]))
    record("V1c partial correlation in samples",
           "formula against correlation of regression residuals on 300000 samples (60 pairs)",
           f"max error {max(errs):.4f}", "below 0.01 (sampling noise)", max(errs) < 0.01)


def check_theta_update():
    rng = np.random.default_rng(2)
    d = 25
    worst_res, min_eig, worst_pert = 0.0, np.inf, 0.0
    for _ in range(20):
        a = rng.standard_normal((d, 40))
        s = a @ a.T / 40 + 0.1 * np.eye(d)
        z = rng.standard_normal((d, d)) * 0.1
        z = (z + z.T) / 2
        lam = float(rng.uniform(0.05, 2.0))
        b = s / lam - z
        w, v = np.linalg.eigh(b.T @ b + (4.0 / lam) * np.eye(d))
        theta = 0.5 * (-b + (v * np.sqrt(w)) @ v.T)
        grad = -np.linalg.inv(theta) + s + lam * (theta - z)
        worst_res = max(worst_res, np.linalg.norm(grad))
        min_eig = min(min_eig, np.linalg.eigvalsh((theta + theta.T) / 2)[0])

        def obj(t):
            return -np.linalg.slogdet(t)[1] + np.trace(s @ t) + 0.5 * lam * np.linalg.norm(z - t) ** 2

        base = obj(theta)
        for _ in range(5):
            e = rng.standard_normal((d, d))
            e = (e + e.T) / 2
            e *= 1e-3 / np.linalg.norm(e)
            worst_pert = min(worst_pert, min(obj(theta + e) - base, obj(theta - e) - base))
    record("V2a Theta update solves the stationarity equation",
           "gradient of the relaxed objective, -Theta^-1 + S + lambda (Theta - Z), at the closed form Theta (20 random cases)",
           f"max gradient norm {worst_res:.2e}", "below 1e-8", worst_res < 1e-8)
    record("V2b Theta update is positive definite", "smallest eigenvalue of Theta over 20 random cases",
           f"{min_eig:.3f}", "above 0", min_eig > 0)
    record("V2c Theta update is a minimum", "objective after a small random move minus objective at Theta, worst case",
           f"{worst_pert:.2e}", "never negative", worst_pert >= -1e-12)


def check_sqrt():
    rng = np.random.default_rng(3)
    a = rng.standard_normal((8, 30))
    pd_mat = torch.tensor(a @ a.T + np.eye(8), dtype=torch.float64)
    err = np.abs(sym_sqrt(pd_mat).numpy() - scipy.linalg.sqrtm(pd_mat.numpy()).real).max()
    record("V3a matrix square root forward", "eigendecomposition square root against scipy.linalg.sqrtm",
           f"max error {err:.2e}", "below 1e-10", err < 1e-10)
    m = pd_mat.clone().requires_grad_(True)
    ok = torch.autograd.gradcheck(SymSqrt.apply, (m,), eps=1e-6, atol=1e-5)
    record("V3b matrix square root backward", "hand written gradient against finite differences (torch gradcheck)",
           "gradcheck passed" if ok else "gradcheck failed", "passes", ok)


def _relaxed_objective(theta, z, s, rho, lam):
    off = ~np.eye(s.shape[0], dtype=bool)
    sign, logdet = np.linalg.slogdet(theta)
    return -logdet + np.trace(s @ theta) + rho * np.abs(z[off]).sum() + 0.5 * lam * np.linalg.norm(z - theta) ** 2


def _independent_minimizer(s, rho, lam):
    d = s.shape[0]
    s_t = torch.as_tensor(s, dtype=torch.float64)
    chol = torch.linalg.cholesky(torch.linalg.inv(s_t + torch.eye(d, dtype=torch.float64)))
    factor = chol.contiguous().clone().requires_grad_(True)
    low = torch.tril(torch.ones(d, d, dtype=torch.float64))
    off = 1 - torch.eye(d, dtype=torch.float64)

    def objective(raw):
        lm = raw * low
        t = lm @ lm.T
        a = t.abs()
        huber = torch.where(a > rho / lam, rho * a - rho ** 2 / (2 * lam), 0.5 * lam * a ** 2)
        return -torch.logdet(t) + torch.trace(s_t @ t) + (huber * off).sum()

    opt = torch.optim.LBFGS([factor], lr=1, max_iter=2000, tolerance_grad=1e-13, tolerance_change=1e-16,
                            line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        v = objective(factor)
        v.backward()
        return v

    for _ in range(5):
        opt.step(closure)
    lm = (factor * low).detach()
    return (lm @ lm.T).numpy()


def check_am_convergence(out):
    x, _ = make_dataset(8, 0.3, 300, seed=5)
    x = (x - x.mean(axis=0)) / x.std(axis=0)
    s8 = np.cov(x, rowvar=False, bias=True) + 0.01 * np.eye(8)
    worst_increase = -np.inf
    for lam in (0.5, 2.0, 8.0):
        th, zs = classical_am(s8, 0.1, lam, 1500)
        f = np.array([_relaxed_objective(t, z, s8, 0.1, lam) for t, z in zip(th, zs)])
        worst_increase = max(worst_increase, float(np.diff(f).max()))
    record("V4a AM never increases its objective",
           "relaxed objective after every AM iteration (1500 iterations, lambda 0.5, 2, 8). Each step is an exact minimization over one block, so it cannot go up",
           f"largest single-step increase {worst_increase:.1e}", "below 1e-10", worst_increase < 1e-10)

    th, zs = classical_am(s8, 0.1, 2.0, 3000)
    reference = _independent_minimizer(s8, 0.1, 2.0)
    rel = np.linalg.norm(th[-1] - reference) / np.linalg.norm(reference)
    record("V4b AM fixed point is the true minimizer",
           "Theta from AM after 3000 iterations against the minimizer of the same objective found by an independent optimizer (L-BFGS)",
           f"relative difference {rel:.1e}", "below 1e-6", rel < 1e-6)

    x25, _ = make_dataset(25, 0.1, 500, seed=7)
    s25 = covariance_with_offset(minmax_scale(x25))
    rho, lam, n = 0.01, 5.0, 20000
    th25, z25 = classical_am(s25, rho, lam, n)
    f25 = np.array([_relaxed_objective(t, z, s25, rho, lam) for t, z in zip(th25, z25)])
    gaps = np.maximum((f25 - f25[-1]) / abs(f25[-1]), 1e-16)
    rows = {k: float(gaps[k - 1]) for k in (15, 100, 1000, 5000)}
    pd.DataFrame([{"AM iterations": k, "relative objective gap to the final value": v} for k, v in rows.items()]).to_csv(
        os.path.join(out, "am_speed_experiment_scale.csv"), index=False)
    record("V4c speed of AM with fixed settings (reported, no threshold)",
           "relative gap of the AM objective to its final value on a D = 25 problem at the scale used in the experiments (rho 0.01, lambda 5)",
           "after 15, 100, 1000, 5000 iterations: " + ", ".join(f"{v:.1e}" for v in rows.values()),
           "reported only", True,
           "uGLAD uses 15 learned steps, so it does not follow this path")

    f8 = np.array([_relaxed_objective(t, z, s8, 0.1, 2.0) for t, z in zip(th, zs)])
    gaps8 = np.maximum((f8 - f8[-1]) / abs(f8[-1]), 1e-16)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.loglog(np.arange(1, len(gaps8) + 1), gaps8, label="D = 8, standardized data")
    ax.loglog(np.arange(1, len(gaps) + 1), gaps, label="D = 25, min-max scaled data")
    ax.axvline(15, color="gray", linestyle="--", linewidth=1)
    ax.text(16, 1e-14, "15 steps (uGLAD depth)", fontsize=8)
    ax.set_xlabel("AM iteration")
    ax.set_ylabel("relative objective gap")
    ax.set_title("AM with fixed settings")
    ax.legend(fontsize=8)
    fig.tight_layout()
    os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, "am_convergence.png"), dpi=160)
    plt.close(fig)
    return rows


def check_uglad_properties(out):
    x, theta = make_dataset(25, 0.1, 100, seed=11)
    xs = minmax_scale(x)
    z, info = fit_uglad(xs, mode="cv", seed=11)
    net = info["net"]
    s = torch.as_tensor(covariance_with_offset(xs), dtype=torch.float64)
    with torch.no_grad():
        _, path = net(s, 15, return_path=True)
    min_eigs = [np.linalg.eigvalsh((t.numpy() + t.numpy().T) / 2)[0] for t, _, _ in path]
    record("V5a every Theta step is positive definite", "smallest eigenvalue of Theta_k over the 15 unrolled steps",
           f"min over steps {min(min_eigs):.3f}", "above 0", min(min_eigs) > 0)
    record("V5b output is symmetric", "max |Z - Z^T|", f"{np.abs(z - z.T).max():.2e}", "below 1e-12", np.abs(z - z.T).max() < 1e-12)
    sizes = {d: UGladNet().n_parameters() for d in (10, 25, 100)}
    record("V5c parameter count does not depend on D", "learnable parameters of the network, built for D = 10, 25, 100",
           f"{sizes[10]}, {sizes[25]}, {sizes[100]}", "all equal", len(set(sizes.values())) == 1)
    tr = info["train_curve"]
    record("V5d training reduces the loss", "training loss in the first and the last epoch of the selected fold",
           f"{tr[0]:.2f} to {tr[-1]:.2f}", "last below first", tr[-1] < tr[0])
    losses = []
    for t, zk, _ in path:
        zk_t = zk
        sign, logdet = np.linalg.slogdet(zk_t.numpy())
        losses.append(np.nan if sign <= 0 else float(-logdet + np.trace(s.numpy() @ zk_t.numpy())))
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    ax.plot(range(1, 16), losses, "o-")
    ax.set_xlabel("unrolled step k")
    ax.set_ylabel("loss  -log det Z + tr(S Z)")
    ax.set_title("Loss along the unrolled steps (trained model)")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "loss_along_steps.png"), dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    ax.plot(info["train_curve"], label="training fold")
    ax.plot(info["val_curve"], label="validation fold")
    ax.set_xlabel("epoch")
    ax.set_ylabel("loss")
    ax.set_title("uGLAD training curve (one dataset)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out, "training_curve.png"), dpi=160)
    plt.close(fig)


def check_inference():
    rng = np.random.default_rng(5)
    d = 25
    theta = make_precision(d, 0.1, rng)
    model = GaussianGraphicalModel(theta)
    x = sample_gaussian(theta, 400000, np.random.default_rng(6))

    i = 3
    others = [k for k in range(d) if k != i]
    coef = np.linalg.lstsq(x[:, others], x[:, i], rcond=None)[0]
    res_var = np.var(x[:, i] - x[:, others] @ coef)
    formula_coef = -theta[i, others] / theta[i, i]
    record("V6a conditional mean given all other variables", "-Theta_ij / Theta_ii against regression coefficients from 400000 samples",
           f"max coefficient error {np.abs(coef - formula_coef).max():.4f}", "below 0.01", np.abs(coef - formula_coef).max() < 0.01)
    record("V6b conditional variance given all other variables", "1 / Theta_ii against the residual variance of that regression",
           f"{model.conditional_variance(i):.4f} against {res_var:.4f}", "relative error below 1%",
           abs(model.conditional_variance(i) - res_var) / res_var < 0.01)

    a, b = [0, 1], [2, 3, 4, 5]
    x_b = np.array([0.3, -0.5, 0.8, 0.1])
    mean, cov = model.conditional(a, b, x_b)
    coef_sub = np.linalg.lstsq(x[:, b], x[:, a], rcond=None)[0]
    resid = x[:, a] - x[:, b] @ coef_sub
    err = max(np.abs(coef_sub.T @ x_b - mean).max(), np.abs(np.cov(resid.T) - cov).max())
    record("V6c conditional given a subset of variables", "mean and covariance of X_0, X_1 given X_2..X_5, with the other variables integrated out, against regression on samples",
           f"max error {err:.4f}", "below 0.01", err < 0.01)

    mean_m, cov_m = model.marginal([0, 1, 2])
    err_m = np.abs(np.cov(x[:, :3].T) - cov_m).max()
    record("V6d marginal", "Sigma[0:3, 0:3] against the sample covariance of X_0..X_2", f"max error {err_m:.4f}", "below 0.01", err_m < 0.01)

    xs_ = rng.standard_normal((50, d))
    diffs = np.array([model.log_unnormalized(row) - model.log_density(row) for row in xs_])
    record("V6e factorization into node and edge factors", "sum of node and edge log factors minus the exact log density, for 50 random points (must be one constant)",
           f"spread {diffs.max() - diffs.min():.2e}", "below 1e-9", diffs.max() - diffs.min() < 1e-9)

    worst = 0.0
    for row in x[:200]:
        for node in range(d):
            nb = model.neighbors(node)
            via_neighbours = -(theta[node, nb] @ row[nb]) / theta[node, node] if nb else 0.0
            worst = max(worst, abs(via_neighbours - model.predict_node(node, row)))
    record("V6f local Markov property", "prediction of a variable from its neighbours only against prediction from all other variables (200 samples, 25 variables)",
           f"max difference {worst:.2e}", "below 1e-9", worst < 1e-9)

    rows = []
    for dim in (25, 100, 400):
        th = make_precision(dim, min(0.1, 3.0 / dim), np.random.default_rng(1))
        mdl = GaussianGraphicalModel(th)
        _ = mdl.covariance
        xrow = np.random.default_rng(2).standard_normal(dim)
        reps = 200
        t0 = time.perf_counter()
        for _ in range(reps):
            mdl.predict_node(0, xrow)
        t_pred = (time.perf_counter() - t0) / reps
        t0 = time.perf_counter()
        for _ in range(reps):
            mdl.conditional([0, 1], list(range(2, min(dim, 12))), np.zeros(min(dim, 12) - 2))
        t_cond = (time.perf_counter() - t0) / reps
        t0 = time.perf_counter()
        _ = mdl.partial_correlation
        t_pc = time.perf_counter() - t0
        rows.append({"D": dim, "predict one variable (microseconds)": t_pred * 1e6,
                     "conditional of 2 given 10 (microseconds)": t_cond * 1e6,
                     "all partial correlations (milliseconds)": t_pc * 1e3})
    return pd.DataFrame(rows)


def check_baseline_conversion_and_metrics():
    d = 3
    skel, moral = _dag_to_adjacency(d, [(0, 2), (1, 2)])
    ok1 = bool(skel[0, 2] and skel[1, 2] and not skel[0, 1] and moral[0, 1])
    skel2, moral2 = _dag_to_adjacency(d, [(0, 1), (1, 2)])
    ok2 = bool(not moral2[0, 2])
    g = np.zeros((3, 3), dtype=int)
    g[2, 0], g[0, 2] = 1, -1
    g[2, 1], g[1, 2] = 1, -1
    sk3, mo3 = _cpdag_to_adjacency(g)
    ok3 = bool(mo3[0, 1] and not sk3[0, 1])
    g2 = np.zeros((3, 3), dtype=int)
    g2[0, 1], g2[1, 0] = -1, -1
    sk4, mo4 = _cpdag_to_adjacency(g2)
    ok4 = bool(sk4[0, 1] and (sk4 == mo4).all())
    record("V7a moralization", "collider adds an edge between the parents, chain does not, for both the DAG and the CPDAG converters",
           f"{ok1}, {ok2}, {ok3}, {ok4}", "all True", ok1 and ok2 and ok3 and ok4)

    t = np.array([1, 1, 0, 0, 1, 0])
    p = np.array([1, 0, 1, 0, 1, 0])
    m = binary_structure_metrics(t, p)
    ok = (m["TP"], m["FP"], m["FN"], m["SHD"]) == (2, 1, 1, 2) and abs(m["precision"] - 2 / 3) < 1e-12 and abs(m["F1"] - 2 / 3) < 1e-12
    sm = score_metrics(t, np.array([0.9, 0.8, 0.1, 0.05, 0.7, 0.0]))
    ok_s = abs(sm["AUC"] - 1.0) < 1e-12 and abs(sm["AUPR"] - 1.0) < 1e-12
    record("V7b metrics on a hand worked example", "SHD, precision, F1 and perfect-ranking AUC and AUPR against values worked out by hand",
           f"{m['TP']} TP, {m['FP']} FP, {m['FN']} FN, SHD {m['SHD']}; AUC {sm['AUC']:.1f}", "equal to hand values", ok and ok_s)


def check_official(out):
    from official import run_official_uglad
    rows = []
    for m_, seed in ((10, 0), (50, 1), (100, 2), (500, 3)):
        x, theta = make_dataset(25, 0.1, m_, seed=2026 + seed)
        xs = minmax_scale(x)
        mine, info = fit_uglad(xs, mode="cv", seed=2026 + seed)
        theirs = run_official_uglad(xs, 2026 + seed)
        y = true_edge_vector(theta)
        a = score_metrics(y, np.abs(upper(mine)))
        b = score_metrics(y, np.abs(upper(theirs.astype(float))))
        rows.append({"M": m_, "seed": 2026 + seed,
                     "max |Z_mine - Z_official|": float(np.abs(mine - theirs).max()),
                     "mean |Z_official|": float(np.abs(theirs).mean()),
                     "edges mine": int((np.abs(upper(mine)) > 1e-10).sum()),
                     "edges official": int((np.abs(upper(theirs)) > 1e-10).sum()),
                     "AUPR mine": a["AUPR"], "AUPR official": b["AUPR"], "AUC mine": a["AUC"], "AUC official": b["AUC"]})
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out, "official_crosscheck.csv"), index=False)
    worst_aupr = float(np.abs(df["AUPR mine"] - df["AUPR official"]).max())
    same_edges = bool((df["edges mine"] == df["edges official"]).all())
    record("V8 same results as the public uGLAD code", "my implementation and the public one, same data, same seed, same settings (4 datasets, M = 10, 50, 100, 500)",
           f"max AUPR difference {worst_aupr:.4f}; same edge counts: {same_edges}; max entry difference {df['max |Z_mine - Z_official|'].max():.3f}",
           "AUPR difference below 0.01", worst_aupr < 0.01)


def write_report(out, timing, am_rows):
    df = pd.DataFrame(CHECKS)
    df.to_csv(os.path.join(out, "validation_checks.csv"), index=False)
    timing.to_csv(os.path.join(out, "inference_query_time.csv"), index=False)
    lines = ["# Validation report", "",
             f"{int(df['pass'].sum())} of {len(df)} checks passed.", "",
             "| Check | What is compared | Measured | Criterion | Result |", "|---|---|---|---|---|"]
    for _, r in df.iterrows():
        lines.append(f"| {r['check']} | {r['what is compared']} | {r['measured']} | {r['criterion']} | {'pass' if r['pass'] else 'FAIL'} |")
    lines += ["", "## Inference query time", "", timing.round(2).to_markdown(index=False), ""]
    with open(os.path.join(out, "validation_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--with-official", action="store_true")
    ap.add_argument("--only-official", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.only_official:
        check_official(args.out)
        pd.DataFrame(CHECKS).to_csv(os.path.join(args.out, "validation_official_check.csv"), index=False)
        return
    check_ci_identity()
    check_theta_update()
    check_sqrt()
    am_rows = check_am_convergence(args.out)
    check_uglad_properties(args.out)
    timing = check_inference()
    check_baseline_conversion_and_metrics()
    if args.with_official:
        check_official(args.out)
    write_report(args.out, timing, am_rows)
    failed = [c["check"] for c in CHECKS if not c["pass"]]
    print("\nAll checks passed." if not failed else f"\nFAILED: {failed}")


if __name__ == "__main__":
    main()
