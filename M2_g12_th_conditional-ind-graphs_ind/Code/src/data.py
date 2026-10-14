import numpy as np


def make_precision(d, p, rng, w_low=-1.0, w_high=1.0, min_eig=1.0):
    iu = np.triu_indices(d, 1)
    has_edge = rng.random(len(iu[0])) < p
    weights = rng.uniform(w_low, w_high, size=len(iu[0])) * has_edge
    a = np.zeros((d, d))
    a[iu] = weights
    a = a + a.T
    smallest = np.linalg.eigvalsh(a)[0]
    theta = a + (min_eig - smallest) * np.eye(d)
    return theta


def make_precision_authors(d, p, rng, w_low=-1.0, w_high=1.0, min_eig=1.0):
    iu = np.triu_indices(d, 1)
    adj = np.zeros((d, d))
    adj[iu] = (rng.random(len(iu[0])) < p).astype(float)
    adj = adj + adj.T
    w = rng.uniform(w_low, w_high, size=(d, d))
    off = adj * w
    off = (off + off.T) / 2.0
    smallest = np.linalg.eigvalsh(off)[0]
    return off + (min_eig - smallest) * np.eye(d)


def sample_gaussian(theta, m, rng):
    cov = np.linalg.inv(theta)
    cov = (cov + cov.T) / 2.0
    chol = np.linalg.cholesky(cov)
    z = rng.standard_normal((m, theta.shape[0]))
    return z @ chol.T


def make_dataset(d, p, m, seed, generator="symmetric"):
    rng = np.random.default_rng(seed)
    theta = make_precision_authors(d, p, rng) if generator == "authors" else make_precision(d, p, rng)
    x = sample_gaussian(theta, m, rng)
    return x, theta


def true_edge_vector(theta, tol=0.0):
    iu = np.triu_indices(theta.shape[0], 1)
    return (np.abs(theta[iu]) > tol).astype(int)


def minmax_scale(x):
    lo = x.min(axis=0)
    hi = x.max(axis=0)
    span = np.where(hi - lo > 0, hi - lo, 1.0)
    return (x - lo) / span
