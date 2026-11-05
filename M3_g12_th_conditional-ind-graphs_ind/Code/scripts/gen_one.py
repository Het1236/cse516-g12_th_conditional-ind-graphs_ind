"""Generate ONE synthetic Rhino dataset with the authors' generator (same arguments as generate_all_cts.py)."""
import argparse, json, os
from causica.data_generation.temporal_synthetic.data_gen_util import (
    generate_cts_temporal_data, generate_name, set_random_seed)

p = argparse.ArgumentParser()
p.add_argument("--dim", type=int, required=True)
p.add_argument("--inst", default="ER", choices=["ER", "SF", "none"])
p.add_argument("--lagtype", default="ER", choices=["ER", "SF"])
p.add_argument("--hist", type=int, default=1)
p.add_argument("--con", type=int, default=2)
p.add_argument("--seed", type=int, default=0)
p.add_argument("--save_dir", default="data")
a = p.parse_args()

lag, noise_level = 2, 0.5
disable_inst = a.inst == "none"
inst_type = "ER" if disable_inst else a.inst
graph_type = [inst_type, a.lagtype]
big = a.dim >= 40
series_length, burnin, ntrain = (400, 100, 100) if big else (200, 50, 50)
graph_config = [{"m": a.dim * 2 * a.con if not disable_inst else 0, "directed": True},
                {"m": a.dim * a.con, "directed": True}]
set_random_seed(a.seed)
name = generate_name(a.dim, graph_type, lag, bool(a.hist), noise_level, function_type="mlp",
                     noise_function_type="spline_product", disable_inst=disable_inst, seed=a.seed,
                     connection_factor=a.con, intervention_history=3)
path = os.path.join(a.save_dir, name)
generate_cts_temporal_data(path=path, series_length=series_length, burnin_length=burnin,
    num_train_samples=ntrain, num_test_samples=50, num_nodes=a.dim, graph_type=graph_type,
    graph_config=graph_config, lag=lag, is_history_dep=bool(a.hist), noise_level=noise_level,
    function_type="mlp", noise_function_type="spline_product", base_noise_type="gaussian",
    num_interventions=5, num_intervention_samples=5000, intervention_value=10, intervention_history=3)
with open(os.path.join(path, "graph_config.json"), "w", encoding="utf-8") as f:
    json.dump(graph_config, f)
print("DATASET", name)
