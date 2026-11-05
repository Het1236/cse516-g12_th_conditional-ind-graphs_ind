"""Write the model configs for the DREAM3 and Netsim experiments into rhino_work/configs_m3/real/.

Two variants per Rhino configuration:
  *_paper   : hyperparameters from the paper (Table 4, Appendix G.1 and G.4); augmented Lagrangian steps with 2000 inner iterations
  *_shipped : the config released by the authors (configs/rhino/model_config_rhino_<name>.json), unchanged
The paper and the released configs differ in the number of augmented Lagrangian steps (open point 3 of the guide).
Baseline configs follow Table 5 (DYNOTEARS, DREAM3), Appendix G.4 (Netsim) and the tigramite default for PCMCI+.
Run from rhino_work/ :  rhino_env\\venv\\Scripts\\python.exe scripts\\make_real_configs.py
"""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "causica", "configs", "rhino")
DEF = os.path.join(ROOT, "causica", "configs", "defaults")
OUT = os.path.join(ROOT, "configs_m3", "real")
os.makedirs(OUT, exist_ok=True)


def load(p):
    return json.load(open(p))


def save(name, cfg):
    json.dump(cfg, open(os.path.join(OUT, name + ".json"), "w"), indent=2)


# Paper Table 4: node embedding, flow embedding, lambda_s, aug-Lag steps (each 2000 iterations)
T4_RHINO = {"ecoli1": (16, 16, 19, 30), "ecoli2": (16, 100, 25, 80), "yeast1": (32, 100, 25, 10),
            "yeast2": (32, 100, 25, 80), "yeast3": (32, 16, 25, 5)}
T4_RHINO_G = {"ecoli1": (100, None, 15, 60), "ecoli2": (100, None, 25, 25), "yeast1": (100, None, 15, 5),
              "yeast2": (100, None, 19, 125), "yeast3": (100, None, 9, 10)}
# Paper Table 5: DYNOTEARS lag, lambda_a (lagged), lambda_w (instantaneous)
T5 = {"ecoli1": (2, 0.01, 0.5), "ecoli2": (2, 0.1, 0.01), "yeast1": (2, 0.005, 0.1),
      "yeast2": (3, 0.01, 0.01), "yeast3": (2, 0.01, 0.005)}

for net in T4_RHINO:
    for tag, table, suffix in (("rhino", T4_RHINO, ""), ("rhino_g", T4_RHINO_G, "_gaussian")):
        shipped = load(os.path.join(SRC, f"model_config_rhino_{net}{suffix}.json"))
        save(f"dream3_{net}_{tag}_shipped", shipped)
        emb, flow, lam, steps = table[net]
        paper = copy.deepcopy(shipped)
        mh, th = paper["model_hyperparams"], paper["training_hyperparams"]
        mh["ICGNN_embedding_size"], mh["conditional_embedding_size"], mh["lambda_sparse"] = emb, flow, lam
        th["max_steps_auglag"], th["max_auglag_inner_epochs"] = steps, 2000
        save(f"dream3_{net}_{tag}_paper", paper)
    lag, la, lw = T5[net]
    dy = load(os.path.join(DEF, "model_config_dynotears.json"))
    dy["model_hyperparams"].update(lag=lag, lambda_a=la, lambda_w=lw)
    dy["training_hyperparams"].update(max_iter=1000, h_tol=1e-8, w_threshold=0.05)
    save(f"dream3_{net}_dynotears", dy)
save("dream3_pcmci_plus", load(os.path.join(DEF, "model_config_pcmci_plus.json")))   # max lag 2, parcorr, default alpha

# Netsim (Appendix G.4): lambda_s = 25, init edge probability 0.5, 2x64 MLPs, embedding = number of nodes (15), 5 aug-Lag steps
ns = load(os.path.join(SRC, "model_config_rhino_netsim.json"))
variants = {
    "rhino": dict(base_distribution_type="conditional_spline", allow_instantaneous=True),
    "rhino_g": dict(base_distribution_type="gaussian", allow_instantaneous=True),
    "rhino_noinst": dict(base_distribution_type="conditional_spline", allow_instantaneous=False),
}
for tag, ch in variants.items():
    for steps_tag, steps in (("paper", 5), ("shipped", 60)):
        cfg = copy.deepcopy(ns)
        cfg["model_hyperparams"].update(ch)
        cfg["training_hyperparams"]["max_steps_auglag"] = steps
        cfg["training_hyperparams"]["max_auglag_inner_epochs"] = 2000
        save(f"netsim_{tag}_{steps_tag}", cfg)
dy = load(os.path.join(DEF, "model_config_dynotears.json"))
dy["model_hyperparams"].update(lag=2, lambda_a=0.5, lambda_w=0.5)
dy["training_hyperparams"].update(max_iter=1000, h_tol=1e-8, w_threshold=0.05)   # training params assumed as for DREAM3
save("netsim_dynotears", dy)
pc = load(os.path.join(DEF, "model_config_pcmci_plus.json"))
pc["model_hyperparams"]["max_lag"] = 3
save("netsim_pcmci_plus", pc)
save("netsim_varlingam", load(os.path.join(DEF, "model_config_varlingam.json")))   # lag 2, defaults
print(len(os.listdir(OUT)), "configs written to", OUT)
