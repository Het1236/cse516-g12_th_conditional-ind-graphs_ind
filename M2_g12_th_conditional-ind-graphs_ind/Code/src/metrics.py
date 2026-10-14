import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def upper(a):
    return a[np.triu_indices(a.shape[0], 1)]


def binary_structure_metrics(true_edges, pred_edges):
    t = np.asarray(true_edges).astype(bool)
    p = np.asarray(pred_edges).astype(bool)
    tp = int(np.sum(t & p))
    fp = int(np.sum(~t & p))
    fn = int(np.sum(t & ~p))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"SHD": fp + fn, "TP": tp, "FP": fp, "FN": fn, "precision": precision, "recall": recall,
            "F1": f1, "n_pred_edges": int(p.sum())}


def score_metrics(true_edges, scores):
    t = np.asarray(true_edges).astype(int)
    if t.sum() == 0 or t.sum() == len(t):
        return {"AUC": float("nan"), "AUPR": float("nan")}
    return {"AUC": float(roc_auc_score(t, scores)), "AUPR": float(average_precision_score(t, scores))}


def is_positive_definite(theta):
    try:
        np.linalg.cholesky((theta + theta.T) / 2.0)
        return True
    except np.linalg.LinAlgError:
        return False


def heldout_nll(theta, x_test_centered):
    if not is_positive_definite(theta):
        return float("nan")
    d = theta.shape[0]
    sign, logdet = np.linalg.slogdet(theta)
    quad = np.einsum("ni,ij,nj->n", x_test_centered, theta, x_test_centered)
    return float(np.mean(0.5 * quad - 0.5 * logdet + 0.5 * d * np.log(2 * np.pi)))


def conditional_prediction_rmse(theta, x_test_centered):
    diag = np.diag(theta)
    if np.any(diag <= 0):
        return float("nan")
    off = theta - np.diag(diag)
    pred = -(x_test_centered @ off) / diag
    return float(np.sqrt(np.mean((x_test_centered - pred) ** 2)))
