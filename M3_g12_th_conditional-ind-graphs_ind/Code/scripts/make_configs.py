"""Write the Rhino model-config variants used in the reproduction into rhino_work/configs_m3/.

Values follow the paper (Appendix F.2): Rhino and Rhino+s use lambda_s = 9, Rhino+g uses lambda_s = 5.
The shipped configs/rhino/model_config_rhino_synthetic.json has lambda_sparse = 5 for the plain Rhino model.
Both are written so the difference can be tested: rhino_shipped.json keeps the shipped value.
Run from rhino_work/ :  python scripts/make_configs.py
"""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "causica", "configs", "rhino", "model_config_rhino_synthetic.json")
OUT = os.path.join(ROOT, "configs_m3")
os.makedirs(OUT, exist_ok=True)
base = json.load(open(SRC))


def write(name, **changes):
    cfg = copy.deepcopy(base)
    mh = cfg["model_hyperparams"]
    for k, v in changes.items():
        mh[k] = v
    json.dump(cfg, open(os.path.join(OUT, name + ".json"), "w"), indent=2)


write("rhino", lambda_sparse=9)                                             # paper: 9
write("rhino_shipped", lambda_sparse=5)                                     # value in the released config
write("rhino_g", lambda_sparse=5, base_distribution_type="gaussian")        # Rhino+g, paper: 5
write("rhino_s", lambda_sparse=9, base_distribution_type="spline")          # Rhino+s, paper: 9
for lag in (1, 3):                                                          # Table 1 lag ablation
    write(f"rhino_lag{lag}", lambda_sparse=9, lag=lag)
print("written to", OUT, sorted(os.listdir(OUT)))
