import numpy as np


class GaussianGraphicalModel:
    def __init__(self, precision, names=None, tol=1e-10):
        precision = np.asarray(precision, dtype=float)
        if precision.ndim != 2 or precision.shape[0] != precision.shape[1]:
            raise ValueError("precision must be a square matrix")
        self.theta = (precision + precision.T) / 2.0
        self.d = self.theta.shape[0]
        self.names = list(names) if names is not None else [f"X{i + 1}" for i in range(self.d)]
        self.tol = tol

    @property
    def adjacency(self):
        adj = np.abs(self.theta) > self.tol
        np.fill_diagonal(adj, False)
        return adj

    @property
    def edges(self):
        iu = np.triu_indices(self.d, 1)
        keep = self.adjacency[iu]
        return list(zip(iu[0][keep].tolist(), iu[1][keep].tolist()))

    def neighbors(self, i):
        return np.flatnonzero(self.adjacency[i]).tolist()

    @property
    def partial_correlation(self):
        s = np.sqrt(np.diag(self.theta))
        p = -self.theta / np.outer(s, s)
        np.fill_diagonal(p, 1.0)
        return p

    @property
    def covariance(self):
        if getattr(self, "_cov", None) is None:
            self._cov = np.linalg.inv(self.theta)
        return self._cov

    def is_conditionally_independent(self, i, j):
        return not bool(self.adjacency[i, j])

    def node_log_factor(self, i, xi):
        return -0.5 * self.theta[i, i] * np.asarray(xi) ** 2

    def edge_log_factor(self, i, j, xi, xj):
        return -self.theta[i, j] * np.asarray(xi) * np.asarray(xj)

    def log_unnormalized(self, x):
        total = sum(self.node_log_factor(i, x[i]) for i in range(self.d))
        total += sum(self.edge_log_factor(i, j, x[i], x[j]) for i, j in self.edges)
        return float(total)

    def log_density(self, x):
        x = np.asarray(x, dtype=float)
        sign, logdet = np.linalg.slogdet(self.theta)
        if sign <= 0:
            return float("nan")
        quad = x @ self.theta @ x
        return float(0.5 * logdet - 0.5 * quad - 0.5 * self.d * np.log(2 * np.pi))

    def marginal(self, idx):
        idx = list(idx)
        cov = self.covariance[np.ix_(idx, idx)]
        return np.zeros(len(idx)), cov

    def conditional(self, target, given, values):
        a = list(target)
        b = list(given)
        values = np.asarray(values, dtype=float)
        idx = a + b
        if sorted(idx) == list(range(self.d)):
            precision = self.theta[np.ix_(idx, idx)]
        else:
            precision = np.linalg.inv(self.covariance[np.ix_(idx, idx)])
        p_aa = precision[: len(a), : len(a)]
        p_ab = precision[: len(a), len(a):]
        mean = -np.linalg.solve(p_aa, p_ab @ values) if len(b) else np.zeros(len(a))
        return mean, np.linalg.inv(p_aa)

    def predict_node(self, i, x_rest):
        x_rest = np.asarray(x_rest, dtype=float)
        others = [j for j in range(self.d) if j != i]
        return float(-(self.theta[i, others] @ x_rest[others]) / self.theta[i, i])

    def predict_all_nodes(self, x):
        x = np.asarray(x, dtype=float)
        diag = np.diag(self.theta)
        off = self.theta - np.diag(diag)
        return -(x @ off) / diag

    def conditional_variance(self, i):
        return float(1.0 / self.theta[i, i])
