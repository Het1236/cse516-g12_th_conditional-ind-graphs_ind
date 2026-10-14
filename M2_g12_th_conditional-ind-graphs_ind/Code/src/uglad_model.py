import copy
import time

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import KFold

DTYPE = torch.float64


class SymSqrt(torch.autograd.Function):

    @staticmethod
    def forward(ctx, a):
        a_sym = (a + a.T) / 2.0
        w, v = torch.linalg.eigh(a_sym)
        sw = torch.sqrt(torch.clamp(w, min=0.0))
        ctx.save_for_backward(v, sw)
        return (v * sw) @ v.T

    @staticmethod
    def backward(ctx, g):
        v, sw = ctx.saved_tensors
        g_tilde = v.T @ g @ v
        x_tilde = g_tilde / (sw[:, None] + sw[None, :])
        x = v @ x_tilde @ v.T
        return (x + x.T) / 2.0


def sym_sqrt(a):
    return SymSqrt.apply(a)


class UGladNet(nn.Module):
    def __init__(self, hidden=3, theta_init_offset=1.0):
        super().__init__()
        self.theta_init_offset = nn.Parameter(torch.tensor([theta_init_offset], dtype=DTYPE))
        self.rho_net = nn.Sequential(
            nn.Linear(3, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1), nn.Sigmoid(),
        )
        self.lam_net = nn.Sequential(
            nn.Linear(2, hidden), nn.Tanh(),
            nn.Linear(hidden, 1), nn.Sigmoid(),
        )
        self.double()

    def n_parameters(self):
        return sum(p.numel() for p in self.parameters())

    def first_lambda(self):
        return self.lam_net(torch.tensor([1.0, 0.0], dtype=DTYPE))

    def soft_threshold(self, theta, s, z_prev):
        feats = torch.stack([theta.reshape(-1), s.reshape(-1), z_prev.reshape(-1)], dim=-1)
        rho = self.rho_net(feats).reshape(theta.shape)
        return torch.sign(theta) * torch.clamp(theta.abs() - rho, min=0.0)

    def next_lambda(self, gap, lam_prev):
        feats = torch.stack([gap.detach().reshape(()), lam_prev.detach().reshape(())])
        return self.lam_net(feats)

    def forward(self, s, n_steps=15, return_path=False):
        d = s.shape[-1]
        eye = torch.eye(d, dtype=DTYPE)
        z = torch.linalg.inv(s + self.theta_init_offset * eye)
        lam = self.first_lambda()
        path = []
        for _ in range(n_steps):
            b = s / lam - z
            root = sym_sqrt(b.T @ b + (4.0 / lam) * eye)
            theta = 0.5 * (-b + root)
            z = self.soft_threshold(theta, s, z)
            lam = self.next_lambda(((z - theta) ** 2).sum(), lam)
            if return_path:
                path.append((theta.detach().clone(), z.detach().clone(), float(lam.detach())))
        return (z, path) if return_path else z


def glasso_loss(z, s):
    return -torch.logdet(z) + torch.trace(s @ z)


def covariance_with_offset(x, offset=0.1):
    s = np.cov(x, rowvar=False, bias=True)
    s = np.atleast_2d(s)
    smallest = np.linalg.eigvalsh(s)[0]
    if smallest <= 1e-6:
        s = s + np.eye(s.shape[0]) * (offset - smallest)
    return s


def _as_tensor(a):
    return torch.as_tensor(a, dtype=DTYPE)


def _train_one(net, s_train, s_val, epochs, lr, n_steps):
    opt = torch.optim.Adam(net.parameters(), lr=lr, betas=(0.9, 0.999), eps=1e-8)
    best_val = float("inf")
    best_state = None
    best_epoch = -1
    train_curve, val_curve = [], []
    for epoch in range(epochs):
        opt.zero_grad()
        z_tr = net(s_train, n_steps)
        loss_tr = glasso_loss(z_tr, s_train)
        val_loss = float("nan")
        if s_val is not None:
            with torch.no_grad():
                val_loss = float(glasso_loss(net(s_val, n_steps), s_val))
            if np.isfinite(val_loss) and val_loss < best_val:
                best_val = val_loss
                best_epoch = epoch
                best_state = copy.deepcopy(net.state_dict())
        if not torch.isfinite(loss_tr):
            break
        train_curve.append(float(loss_tr.detach()))
        val_curve.append(val_loss)
        loss_tr.backward()
        opt.step()
    if s_val is None:
        best_state = copy.deepcopy(net.state_dict())
        best_epoch = epochs - 1
    return best_state, best_val, train_curve, val_curve, best_epoch


def fit_uglad(x, mode="cv", epochs=250, lr=0.002, n_steps=15, k_fold=3, seed=0,
              offset=0.1, hidden=3):
    t0 = time.perf_counter()
    torch.manual_seed(seed)
    x = np.asarray(x, dtype=float)
    s_full = _as_tensor(covariance_with_offset(x, offset))
    info = {}

    if mode == "direct":
        net = UGladNet(hidden)
        state, _, tr_curve, _, best_epoch = _train_one(net, s_full, None, epochs, lr, n_steps)
        info["best_epoch"] = best_epoch
        net.load_state_dict(state)
        info["train_curve"] = tr_curve
    elif mode == "cv":
        best_net, best_val = None, float("inf")
        for fold, (tr_idx, va_idx) in enumerate(KFold(n_splits=k_fold).split(x)):
            s_tr = _as_tensor(covariance_with_offset(x[tr_idx], offset))
            s_va = _as_tensor(covariance_with_offset(x[va_idx], offset))
            net = UGladNet(hidden)
            state, val, tr_curve, va_curve, best_epoch = _train_one(net, s_tr, s_va, epochs, lr, n_steps)
            if state is not None and val < best_val:
                net.load_state_dict(state)
                best_net, best_val = net, val
                info["train_curve"], info["val_curve"] = tr_curve, va_curve
                info["best_fold"] = fold
                info["best_epoch"] = best_epoch
        if best_net is None:
            raise RuntimeError("uGLAD training failed on every fold (loss was never finite)")
        net = best_net
        info["best_val_loss"] = best_val
    else:
        raise ValueError("mode must be 'cv' or 'direct'")

    with torch.no_grad():
        z = net(s_full, n_steps).numpy()
    info["n_parameters"] = net.n_parameters()
    info["seconds"] = time.perf_counter() - t0
    info["net"] = net
    return z, info


def soft_threshold_np(a, t, off_diagonal_only=True):
    out = np.sign(a) * np.maximum(np.abs(a) - t, 0.0)
    if off_diagonal_only:
        np.fill_diagonal(out, np.diag(a))
    return out


def classical_am(s, rho, lam, n_steps, z0=None):
    d = s.shape[0]
    eye = np.eye(d)
    z = np.linalg.inv(s + eye) if z0 is None else z0
    thetas, zs = [], []
    for _ in range(n_steps):
        b = s / lam - z
        w, v = np.linalg.eigh(b.T @ b + (4.0 / lam) * eye)
        root = (v * np.sqrt(w)) @ v.T
        theta = 0.5 * (-b + root)
        z = soft_threshold_np(theta, rho / lam)
        thetas.append(theta)
        zs.append(z)
    return thetas, zs


def glasso_objective(theta, s, alpha):
    sign, logdet = np.linalg.slogdet(theta)
    if sign <= 0:
        return float("inf")
    off = np.abs(theta).sum() - np.abs(np.diag(theta)).sum()
    return float(-logdet + np.trace(s @ theta) + alpha * off)
