"""Checks of calib_fdr.py on SIMULATED probabilities. These are code tests, not results.
Nothing simulated here is used in the report. Run:  python test_calib_fdr.py
"""
import json
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import calib_fdr as cf  # noqa: E402

S = 100


def simulate_run(rng, n_edges=70, overconf=1.0, prevalence=0.2):
    """q_true is calibrated by construction (y ~ Bernoulli(q_true)). The model reports
    p = sigmoid(overconf * logit(q_true)), then p is quantised to a multiple of 1/S by sampling S graphs."""
    z = rng.normal(loc=logit0(prevalence), scale=2.0, size=n_edges)
    q = cf.sigmoid(z)
    y = (rng.random(n_edges) < q).astype(int)
    p_model = cf.sigmoid(overconf * z)
    p_hat = rng.binomial(S, p_model) / S
    return p_hat, y


def logit0(p):
    return np.log(p / (1 - p))


def test_identity_is_exact():
    rng = np.random.default_rng(0)
    p, y = simulate_run(rng, overconf=2.0)
    sel = cf.bfdr_select(p, 0.2)
    m = cf.sel_metrics(sel, p, y)
    over = p[sel].mean() - y[sel].mean()
    assert abs(m["fdp"] - (m["promised"] + over)) < 1e-12


def test_bfdr_respects_budget_in_promise():
    rng = np.random.default_rng(1)
    p, y = simulate_run(rng)
    for a in cf.ALPHAS:
        sel = cf.bfdr_select(p, a)
        if sel.any():
            assert (1 - p[sel]).mean() <= a + 1e-12
        # maximality: adding the next best edge would break the budget
        if (~sel).any():
            nxt = np.argmax(np.where(sel, -1, p))
            sel2 = sel.copy()
            sel2[nxt] = True
            assert (1 - p[sel2]).mean() > a - 1e-12


def test_calibrated_posterior_controls_fdr():
    rng = np.random.default_rng(2)
    fdp, prom = [], []
    for _ in range(400):
        p, y = simulate_run(rng, overconf=1.0)
        sel = cf.bfdr_select(p, 0.1)
        m = cf.sel_metrics(sel, p, y)
        if m["k"]:
            fdp.append(m["fdp"])
            prom.append(m["promised"])
    assert abs(np.mean(fdp) - np.mean(prom)) < 0.03, (np.mean(fdp), np.mean(prom))


def test_overconfident_posterior_violates_and_temperature_repairs():
    rng = np.random.default_rng(3)
    runs = []
    for i in range(60):
        p, y = simulate_run(rng, overconf=2.5)
        runs.append(dict(meta=dict(job_id=f"j{i}", method="rhino", dataset=f"d{i}", dim=5, hist=1, inst=1, gtype="ER"),
                         S=S, p=p, y=y, is_lag=np.zeros_like(y, bool)))
    fdp_raw = np.mean([cf.sel_metrics(cf.bfdr_select(r["p"], 0.1), r["p"], r["y"])["fdp"] for r in runs])
    assert fdp_raw > 0.15, fdp_raw  # budget broken by raw posterior
    tau = cf.fit_tau(runs, range(len(runs)))
    assert 1.8 < tau < 3.3, tau  # recovers the overconfidence factor 2.5 approximately
    fdp_cal = np.mean([cf.sel_metrics(cf.bfdr_select(cf.apply_temp(r["p"], S, tau), 0.1), cf.apply_temp(r["p"], S, tau), r["y"])["fdp"]
                       for r in runs])
    assert fdp_cal < fdp_raw and abs(fdp_cal - 0.1) < 0.06, (fdp_raw, fdp_cal)


def test_temperature_keeps_ranking():
    rng = np.random.default_rng(4)
    p, _ = simulate_run(rng)
    p2 = cf.apply_temp(p, S, 2.0)
    assert np.all(np.argsort(p, kind="stable") == np.argsort(p2, kind="stable")) or \
        np.allclose(np.sort(p2), p2[np.argsort(p, kind="stable")])


def test_end_to_end_files():
    rng = np.random.default_rng(5)
    with tempfile.TemporaryDirectory() as d:
        for i in range(12):
            p, y = simulate_run(rng, n_edges=75, overconf=2.0)
            meta = dict(job_id=f"rhino__{i}", method="rhino", dataset=f"ds{i}", dim=5, gtype="ER", inst=1, hist=i % 2, seed=i)
            np.savez_compressed(os.path.join(d, f"rhino__{i}.npz"), probs=p.reshape(3, 5, 5).astype(np.float32),
                                truth=y.reshape(3, 5, 5).astype(np.uint8), mask=np.ones((3, 5, 5), np.uint8),
                                n_samples=np.array(S), meta=json.dumps(meta))
        runs = cf.load_export(d)
        assert len(runs) == 12
        res = cf.analyse(runs, 4, d, d, "test")
        for f in ("table_probability_quality_test.csv", "table_fdr_control_test.csv", "table_graph_rules_test.csv",
                  "table_paired_tests_test.csv", "fig_reliability_test.png", "fig_fdr_control_test.png"):
            assert os.path.isfile(os.path.join(d, f)), f


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok ", name)
