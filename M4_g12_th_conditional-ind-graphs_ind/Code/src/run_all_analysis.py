"""Regenerate every table and figure of the M4 study from the exported edge probabilities.

  python run_all_analysis.py                  # sample-based probabilities  (Results/qG_export)  -> tags without suffix
  python run_all_analysis.py --exact          # exact probabilities from model.pt (Results/qG_exact) -> tags with _exact
Then summary_tables.py builds the consolidated tables and figures (it is called at the end).
Seeds: the grouped K-fold split uses numpy seed 0, the bootstrap of the pooled ECE uses seed 0.
"""
import argparse
import os
import subprocess
import sys

import calib_fdr as cf

SYNTH = {"synth_rhino": ["rhino"], "synth_rhino_g": ["rhino_g"], "synth_rhino_s": ["rhino_s"],
         "synth_rhino_shipped": ["rhino_shipped"]}
SHIFT = {"shift_netsim_rhino_paper": ["netsim_rhino_paper"], "shift_netsim_rhino_shipped": ["netsim_rhino_shipped"],
         "shift_dream3_rhino_paper": ["dream3_rhino_paper"], "shift_dream3_rhino_g_paper": ["dream3_rhino_g_paper"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exact", action="store_true")
    ap.add_argument("--folds", type=int, default=5)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    res = os.path.join(here, "..", "..", "Results")
    export = os.path.join(res, "qG_exact" if a.exact else "qG_export")
    suffix = "_exact" if a.exact else ""
    tabs, figs = os.path.join(res, "tables"), os.path.join(res, "figures")
    os.makedirs(tabs, exist_ok=True)
    os.makedirs(figs, exist_ok=True)
    fit_runs = cf.load_export(export, ["rhino"])
    for tag, methods in SYNTH.items():
        runs = cf.load_export(export, methods)
        print(tag + suffix, len(runs), "runs")
        cf.analyse(runs, a.folds, tabs, figs, tag + suffix)
    for tag, methods in SHIFT.items():
        runs = cf.load_export(export, methods)
        print(tag + suffix, len(runs), "runs (tau fitted on synthetic Rhino)")
        cf.analyse(runs, a.folds, tabs, figs, tag + suffix, fit_runs=fit_runs)
    cmd = [sys.executable, os.path.join(here, "summary_tables.py"), "--export_dir", export, "--tables", tabs, "--figs", figs,
           "--suffix", suffix]
    subprocess.run(cmd, check=True, cwd=here)


if __name__ == "__main__":
    main()
