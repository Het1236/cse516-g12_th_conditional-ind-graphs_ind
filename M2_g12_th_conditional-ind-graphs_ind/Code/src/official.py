import contextlib
import io
import os
import sys

import torch


def run_official_uglad(x, seed, epochs=250, lr=0.002, n_steps=15, k_fold=3):
    path = os.environ.get("UGLAD_OFFICIAL_PATH")
    if path and path not in sys.path:
        sys.path.insert(0, path)
    from uglad.main import uGLAD_GL

    torch.manual_seed(seed)
    model = uGLAD_GL()
    with contextlib.redirect_stdout(io.StringIO()):
        model.fit(x, mode="cv", k_fold=k_fold, epochs=epochs, lr=lr, L=n_steps, verbose=False)
    return model.precision_


def author_dataset(d, p, m, seed, w_min=-1.0, w_max=1.0, eig_offset=1.0):
    import random

    import numpy as np

    path = os.environ.get("UGLAD_OFFICIAL_PATH")
    if path and path not in sys.path:
        sys.path.insert(0, path)
    from uglad.utils.prepare_data import get_data

    random.seed(seed)
    np.random.seed(seed)
    xb, theta = get_data(num_nodes=d, sparsity=[p, p], num_samples=m, batch_size=1,
                         eig_offset=eig_offset, w_min=w_min, w_max=w_max)
    return np.asarray(xb[0], dtype=float), np.asarray(theta[0], dtype=float)
