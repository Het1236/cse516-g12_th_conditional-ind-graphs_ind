import warnings

import numpy as np
import pandas as pd
from sklearn.covariance import GraphicalLassoCV


def run_bcd(x, k_fold=3):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = GraphicalLassoCV(cv=k_fold, assume_centered=False).fit(x)
    prec = model.precision_
    return (prec + prec.T) / 2.0, {"alpha": float(model.alpha_)}


def _cpdag_to_adjacency(graph):
    d = graph.shape[0]
    skeleton = (graph != 0) | (graph.T != 0)
    np.fill_diagonal(skeleton, False)
    moral = skeleton.copy()
    for c in range(d):
        parents = [a for a in range(d) if graph[c, a] == 1 and graph[a, c] == -1]
        for i in range(len(parents)):
            for j in range(i + 1, len(parents)):
                moral[parents[i], parents[j]] = True
                moral[parents[j], parents[i]] = True
    return skeleton, moral


def _dag_to_adjacency(d, edges):
    skeleton = np.zeros((d, d), dtype=bool)
    parents = {c: [] for c in range(d)}
    for u, v in edges:
        skeleton[u, v] = skeleton[v, u] = True
        parents[v].append(u)
    moral = skeleton.copy()
    for c in range(d):
        ps = parents[c]
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                moral[ps[i], ps[j]] = moral[ps[j], ps[i]] = True
    return skeleton, moral


def run_pc(x, alpha=0.05):
    from causallearn.search.ConstraintBased.PC import pc
    result = pc(x, alpha, "fisherz", show_progress=False)
    return _cpdag_to_adjacency(np.asarray(result.G.graph))


def run_ges(x):
    from causallearn.search.ScoreBased.GES import ges
    result = ges(x, score_func="local_score_BIC")
    return _cpdag_to_adjacency(np.asarray(result["G"].graph))


def run_hc(x):
    from pgmpy.estimators import HillClimbSearch
    d = x.shape[1]
    names = [f"X{i}" for i in range(d)]
    dag = HillClimbSearch(pd.DataFrame(x, columns=names)).estimate(scoring_method="bic-g", show_progress=False)
    index = {n: i for i, n in enumerate(names)}
    edges = [(index[u], index[v]) for u, v in dag.edges()]
    return _dag_to_adjacency(d, edges)
