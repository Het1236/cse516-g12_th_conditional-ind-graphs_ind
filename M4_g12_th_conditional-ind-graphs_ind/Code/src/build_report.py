"""Builds the M4 report (docx, then PDF through Word). Every number is read from Results/tables."""
import os
import re

import numpy as np
import pandas as pd

import calib_fdr as cf
from latex_lib import LatexReport

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.normpath(os.path.join(HERE, "..", "..", "Results"))
T, FIG = os.path.join(RES, "tables"), os.path.join(RES, "figures")
OUTDIR = os.path.normpath(os.path.join(HERE, "..", "..", "Report"))
NAME = "M4_g12_th_conditional-ind-graphs_ind_Report"
X = "_exact"


def rd(n):
    return pd.read_csv(os.path.join(T, n))


# ------------------------------------------------------------------ data
q = rd(f"table_probability_quality_synth_rhino{X}.csv").set_index("variant")
qs = rd("table_probability_quality_synth_rhino.csv").set_index("variant")
fr = rd(f"table_fdr_control_synth_rhino{X}.csv")
frs = rd("table_fdr_control_synth_rhino.csv")
pt = rd(f"table_paired_tests_synth_rhino{X}.csv").set_index("quantity")
gr = rd(f"table_graph_rules_synth_rhino{X}.csv")
sa = rd(f"table_summary_all{X}.csv").set_index("tag")
br = rd(f"table_breakdown_rhino{X}.csv")
pdf = rd(f"per_dataset_fdr_synth_rhino{X}.csv")
pds = rd(f"per_dataset_synth_rhino{X}.csv")
tau = pds[pds.variant == "temperature"].tau
TAU_M, TAU_S = tau.mean(), tau.std()
chk = open(os.path.join(RES, "m4_exact_report.txt"), encoding="utf-8-sig").read()
m = re.findall(r"mean abs diff ([0-9.]+) \(largest per job ([0-9.]+)\); max abs diff ([0-9.]+)", chk)[-1]
CHK_MEAN, CHK_JOB, CHK_MAX = m
S = sa.loc["synth_rhino"]
NENT = int(S.n_entries)


def row(df, v, a):
    return df[(df.variant == v) & np.isclose(df.alpha, a)].iloc[0]


def fci(r, k="fdp"):
    return f"{r[k+'_mean']:.3f} [{r[k+'_ci_lo']:.3f}, {r[k+'_ci_hi']:.3f}]"


def pv(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def f3(x):
    return f"{x:.3f}"


def f2(x):
    return f"{x:.2f}"


def pc(x):
    return f"{100 * x:.1f}%"


# paired tests of the selection rules on the same datasets
sel_tests = []
for a in (0.10, 0.20):
    x = pdf[np.isclose(pdf.alpha, a)]
    g = {v: x[x.variant == v].set_index("job_id").fdp for v in ("raw", "temperature", "cutoff_pooled")}
    for other in ("raw", "temperature"):
        d = (g["cutoff_pooled"] - a).abs() - (g[other] - a).abs()
        mm, sd, lo, hi, n = cf.mean_sd_ci(d.values)
        sel_tests.append(dict(a=a, other=other, mean=mm, lo=lo, hi=hi, wins=int((d < 0).sum()), loss=int((d > 0).sum()),
                              p=cf.wilcoxon((g["cutoff_pooled"] - a).abs().values, (g[other] - a).abs().values)))
ph = cf.holm([t["p"] for t in sel_tests])
for t, p in zip(sel_tests, ph):
    t["ph"] = p

# variants table
VAR = [("synth_rhino", "Rhino (paper settings)"), ("synth_rhino_g", "Rhino+g (Gaussian noise)"),
       ("synth_rhino_s", "Rhino+s (spline noise, no history)"), ("synth_rhino_shipped", "Rhino (released config)")]
vrows = []
for tag, lab in VAR:
    s_ = sa.loc[tag]
    p_ = rd(f"per_dataset_{tag}{X}.csv")
    p_ = p_[p_.variant == "raw"]
    fv = rd(f"table_fdr_control_{tag}{X}.csv")
    r01 = row(fv, "raw", 0.10)
    c02 = row(fv, "cutoff_pooled", 0.20)
    vrows.append([lab, int(s_.n_runs), f3(p_.auroc.mean()), f3(p_.f1_thr05.mean()), (pc(1 - s_.edge_rate_when_p_is_1) if s_.edge_rate_when_p_is_1 == s_.edge_rate_when_p_is_1 else "n/a"),
                  pc(s_.frac_p_eq_1), f3(s_.ece_raw), f3(r01.fdp_mean), f3(r01.power_mean), f3(c02.fdp_mean), f3(c02.power_mean)])

# real data
REAL = [("shift_netsim_rhino_paper", "Netsim, paper steps"), ("shift_netsim_rhino_shipped", "Netsim, released config"),
        ("shift_dream3_rhino_paper", "DREAM3, Rhino"), ("shift_dream3_rhino_g_paper", "DREAM3, Rhino+g")]
rrows = []
for tag, lab in REAL:
    s_ = sa.loc[tag]
    fv = rd(f"table_fdr_control_{tag}{X}.csv")
    a_raw, a_tmp, a_cut = row(fv, "raw", 0.10), row(fv, "temperature", 0.20), row(fv, "cutoff_pooled", 0.20)
    rrows.append([lab, int(s_.n_runs), f3(s_.auroc_mean), f3(a_raw.fdp_mean), f3(a_raw.power_mean), f3(a_tmp.fdp_mean),
                  f3(a_tmp.power_mean), f3(a_cut.fdp_mean), f3(a_cut.power_mean)])
NP, NR = sa.loc["shift_netsim_rhino_paper"], sa.loc["shift_netsim_rhino_shipped"]
DR = sa.loc["shift_dream3_rhino_paper"]

# convenient single numbers
r_raw = {a: row(fr, "raw", a) for a in (0.01, 0.05, 0.10, 0.20, 0.30)}
r_tmp = {a: row(fr, "temperature", a) for a in (0.01, 0.05, 0.10, 0.20, 0.30)}
r_cut = {a: row(fr, "cutoff_pooled", a) for a in (0.01, 0.05, 0.10, 0.20, 0.30)}
r_cd = {a: row(fr, "cutoff_same_dim", a) for a in (0.01, 0.05, 0.10, 0.20, 0.30)}
ER0, ER1 = S.edge_rate_when_p_is_0, S.edge_rate_when_p_is_1
GR = gr.set_index(["variant", "rule"]).f1_mean

rep = LatexReport(FIG, OUTDIR, NAME)
P, H1, H2 = rep.para, rep.h1, rep.h2

# ------------------------------------------------------------------ title and abstract
rep.front("Can a Deep Temporal Causal Posterior Be Trusted? Error-Controlled Edge Selection for Rhino",
          "Het Patel",
          ["Ahmedabad University, Ahmedabad, India (student ID AU2440266)",
           "CSE 516, Probabilistic Graphical Models. Individual project, Theoretical AI track.",
           "Group g12_th_conditional-ind-graphs_ind. Milestone 4, final report."])

rep.abstract(f"Rhino (Gong et al., ICLR 2023) learns non-linear temporal causal graphs with instantaneous effects and history-dependent noise, and it "
  f"returns a probability for every possible edge. The paper judges the output by AUROC and F1 against a known graph. It does not ask whether the "
  f"probabilities can be trusted, that is, whether a user who keeps the edges above a chosen level gets the share of wrong edges that the probabilities promise. "
  f"This report states that question as a small idea and a plan: take the finished Rhino models as they are, read the exact edge probabilities, select edges under an error budget, "
  f"and measure the realised share of wrong edges against the budget. For any selected set, the share of wrong edges equals the promised error plus the overconfidence of the "
  f"posterior on that set. As a first test I use 500 finished Rhino runs from M3. The posterior is saturated: {pc(S.frac_p_eq_1)} of the entries "
  f"have p above 0.999 and {pc(1 - ER1)} of them are not edges. With a budget of 0.01 the realised share is {fci(r_raw[0.01])} (95% CI over "
  f"120 datasets). Temperature scaling lowers the calibration error from {f3(q.loc['raw','ece_pooled'])} to {f3(q.loc['temperature','ece_pooled'])} but does not restore the promise. "
  f"A cutoff learned on other datasets brings the share close to the budget for budgets of 0.1 to 0.3, at the price of power, and it does not carry over to DREAM3. "
  f"These are early results on one benchmark family. They show where the idea holds and where it does not.")

# ------------------------------------------------------------------ 1 introduction
H1("1. Introduction")
P("A causal graph learned from data is only useful if someone can act on it. A biologist who reads a gene graph, or a "
  "neuroscientist who reads a brain connectivity graph, will follow up the edges one by one. What they need is a statement "
  "such as: at most one in ten of these edges is wrong. Most methods return one graph and give no such statement. "
  "Papers measure quality by comparing against a known true graph. A user in practice has no true graph.")
P("Rhino [1] is a Bayesian method. It models non-linear effects, instantaneous effects and history-dependent noise in time series, "
  "and it learns a distribution q(G) over graphs. This distribution looks like exactly what a user needs, because it gives "
  "a probability for every possible edge. But the paper scores the probabilities only through AUROC and through a graph rounded at 0.5. "
  "In M3 I saw a warning sign. On Netsim the AUROC of Rhino falls from 0.989 to 0.939 while the training goes on, "
  "and the validation likelihood falls from -31.5 to -76.1, while the F1 rises. The model becomes more sure without becoming more right.")
P("**Question.** Can the edge probabilities of a deep temporal causal posterior be used to select edges with a stated error budget, "
  "and if not, what is the cheapest way to repair this?")
P("**What this report offers.** It is a small idea with a plan and a first test, not a new causal discovery method.", "j", 2)
rep.bullets([
    "**An idea.** Treat Rhino's probabilities as a promise about the share of wrong edges, and check the promise. The one formal fact I use is an identity: "
    "the share of wrong edges equals the promised error plus the overconfidence on the selected set (Section 2).",
    f"**A plan that trains nothing.** Read the exact edge probabilities from the saved weights of the M3 runs, calibrate them with one temperature or one cutoff learned on other datasets, "
    f"and compare the realised share of wrong edges with the budget. I analyse 500 finished runs: 440 synthetic, 10 Netsim and 50 DREAM3 (Section 12).",
    "**First evidence, with limits.** The raw posterior is saturated and overconfident. Temperature scaling improves the probability scores but not the promise. "
    "A cutoff learned on other datasets helps for moderate budgets, costs power, and does not carry over to DREAM3 (Sections 12 and 15).",
])
P("**Scope and history.** In M1 and M2 I studied uGLAD for conditional independence graphs. On 31 October 2026 I changed the base paper to Rhino. "
  "M3 reproduced the experiments of the Rhino paper with the authors' code. This report uses the M3 runs as raw material. No model was trained "
  "again for M4. What I add is the question, a small idea with a plan, and a first test of the posterior on those runs. "
  "I reused from M1 and M2 the habit of fair baselines and of stating what did not reproduce.")
P("**Why it matters, and what it costs.** If the posterior could be trusted, a user could choose a budget and read off the graph. "
  "The first evidence says this works only after a repair that needs labelled graphs from similar data, and only for moderate budgets. "
  "That is a useful and a limited answer, and I state both sides in Sections 14 and 15.")
P("**How the report is organised.** It follows the order of the talk: what Rhino is and what its paper shows (Section 3), the gap the paper leaves (Section 2.1), "
  "then the idea, why it is logical, why it matters, the plan, the KPIs and what I expect (Sections 2, 11 and 12).")

# ------------------------------------------------------------------ 2 problem formulation
H1("2. Problem Formulation")
P("This section gives the idea behind the project and the plan to test it. It is short on purpose. It follows the order of the talk: the gap, the idea, why it is logical, why it matters, the plan, and what I expect. I do not claim a theory here. The one formal fact I use is an identity that holds for any selected set.")
H2("2.1 The gap")
P("The Rhino paper checks its output against a known true graph, with AUROC and with the F1 of a graph rounded at 0.5. A real user has no true graph. "
  "They will follow up the top edges one by one, in the lab or in the clinic, and they want to know how many will turn out to be wrong. "
  "That question has an answer only if the probabilities mean what they say. A probability is calibrated if, among the entries scored 0.9, about nine in ten are real edges.")
P("There is a warning sign. In M3 the validation likelihood of Rhino falls during training, as the paper's own Figure 8 shows, and the AUROC falls with it while the F1 rises (Section 1). "
  "I see four reasons to suspect the probabilities, and none of them is established. (1) The objective rewards likelihood and not the quality of edge probabilities. (2) The posterior is a product of independent factors and so ignores dependence between edges. "
  "(3) Long training with sparsity and acyclicity penalties can push the logits to extremes. (4) The posterior comes from one training run on small data and nobody checks it against the truth. The study tests whether these matter.")
H2("2.2 Our idea")
P(r"Take Rhino as given and ask whether its edge probabilities can be used to select edges under an error budget. Let $p_e\in[0,1]$ be the probability of edge entry $e=(l,i,j)$, meaning an edge from variable $i$ to variable $j$ at lag $l$, and let $y_e\in\{0,1\}$ be the unknown truth. "
  r"Given the probabilities and a budget $\alpha$, choose a set $S$ of entries that finds as many true edges as possible, while the expected share of wrong edges in $S$ stays at most $\alpha$. "
  "At use time no true graph is available. Labels are used only on calibration datasets, which do have true graphs. I call this selective temporal causal discovery. It is a way of using a causal discovery method, not a new one.")
H2("2.3 Why it is logical")
P(r"Write $\mathrm{FDP}(S)$ for the share of wrong edges in $S$, and $a(S)=\frac{1}{|S|}\sum_{e\in S}(1-p_e)$ for the error that the posterior promises on $S$. Then, for any non-empty $S$,")
rep.eq("", tex=r"\mathrm{FDP}(S)\;=\;a(S)\;+\;o(S),\qquad o(S)=\frac{1}{|S|}\sum_{e\in S}(p_e-y_e).")
P(r"The term $o(S)$ is the overconfidence of the posterior on the chosen set. The identity is one line of algebra, because both sides are one minus a mean (Appendix A). It says what to look for: the promise fails exactly where the posterior is overconfident on what it selects. "
  "If the probabilities are calibrated, the overconfidence averages to zero and the classical Bayesian false discovery rule of Newton et al. [11] controls the expected share of wrong edges. "
  "A second fact, also standard, limits any repair that only rescales the probabilities: a strictly increasing map of p keeps the order of the entries, so it keeps AUROC and the top-k sets. "
  "Both facts are stated and checked in Appendix A. I make no claim that they are new.")
H2("2.4 Why it matters")
P("Think of a gene network with a hundred candidate edges. Every edge that is followed costs an experiment. If the probabilities are trustworthy, a user can choose a budget, for example at most one wrong edge in ten, and get the longest list that respects it. "
  "If they are not, the user cannot choose how many edges to follow, and is misled without knowing it.")
H2("2.5 Our plan")
P("The plan has three steps and trains nothing. I keep the finished Rhino models from M3. (1) Read the exact edge probabilities from the saved weights. "
  "(2) Calibrate them, with one temperature or one cutoff on the log-odds, both learned on other datasets that have a known graph. (3) Select the edge set with the Bayesian false discovery rule. "
  "The selection itself costs a sort. Sections 7 and 8 give the details. Section 11 lists the KPIs and why each is used. The key one is the realised share of wrong edges against the budget, because it tests the promise directly, where the user reads the list.")
H2("2.6 What I expect")
rep.figure("slide_target.png", "Fig. 1: The target, as a schematic and not as a result. On the diagonal the promise is kept. Above it there are more wrong edges than promised.", 3.1)
P("I expect the raw posterior to land above the diagonal. I expect a repair to bring it near the diagonal for moderate budgets, at a price in power, and I do not expect the repair to transfer to real data without a check. "
  "These are expectations that the data can contradict, and Section 12 reports where they do. The wording of the five expectations is below. H5 was added after I saw the temperature result, so it is exploratory.")
rep.bullets([
    "**H1.** The raw posterior breaks its own budget: the realised share of wrong edges is clearly above alpha.",
    "**H2.** Temperature scaling, fitted on other datasets, lowers Brier score, log-loss and ECE, and brings the realised share close to alpha.",
    "**H3.** The graph that maximises the expected F1 under the calibrated posterior beats a threshold of 0.5 and comes close to the oracle threshold.",
    "**H4.** The temperature fitted on synthetic data transfers to Netsim and DREAM3, or if not, the promise degrades as expected when the calibration data differ from the new data.",
    "**H5 (exploratory, added after H2).** A cutoff on the log-odds, learned on other datasets so that the pooled share of wrong edges is at most alpha, brings the realised share close to alpha.",
])
H2("2.7 Benefits and costs")
P("**Benefits if it works.** A user gets an error budget in the units they care about. The method needs no change of the model and no "
  "retraining, and it costs seconds. **Costs and limits.** It needs labelled graphs from similar data. The promise is an average over datasets, not "
  "a guarantee for one dataset. Calibration cannot repair a weak ranking. A budget that is too strict selects nothing. I measure each of these costs.")

# ------------------------------------------------------------------ 3 background
H1("3. Background")
P("**What we want to learn, and why it is hard.** We observe several variables over time, for example gene expression or signals from brain regions, and we want to know which variable drives which and after how many time steps. "
  "The Rhino paper names three features of real series that make this hard. Effects are non-linear. With slow sampling, everything that happens between two measurements is folded into one time step, which creates instantaneous effects. "
  "And the noise is not fixed: how much a variable scatters can depend on its own past. Granger-type methods, including the neural ones [5, 6, 7], assume no instantaneous effects and a fixed noise distribution. "
  "VAR-LiNGAM [2] and DYNOTEARS [3] handle instantaneous effects but are linear with fixed noise. PCMCI+ [4] handles both kinds of effect with conditional independence tests, but does not model the noise. Rhino [1] handles all three features at once.")
P(r"**Rhino as a structural equation model.** The value of variable $i$ at time $t$ is given by")
rep.eq("", tex=r"X_{i,t}=f_i\big(\mathrm{Pa}_i^{<t},\mathrm{Pa}_i^{t}\big)+g_i\big(\mathrm{Pa}_i^{<t},\varepsilon_{i,t}\big).")
P(r"The function $f$ is a neural network, and $g$ is a conditional spline flow that reshapes the noise $\varepsilon$ as a function of the lagged parents. So the noise can grow or shrink with the history. The graph is a tensor of shape $[L+1,D,D]$. Slice 0 holds the instantaneous edges and the slices 1 to $L$ hold the lagged edges [1]. The paper proves that the graph is identifiable under conditions on $f$ and $g$ [1, Theorem 1]. I use this result and I do not re-prove it.")
P("**Variants.** Rhino+g uses Gaussian noise that does not depend on history. Rhino+s uses a spline noise that does not depend on history. "
  "These variants test single ideas of the model, and I use them to see how the posterior depends on the noise model.")
P("**Calibration.** A probability forecast is calibrated if events forecast with probability p happen in about a fraction p of the cases. "
  "I use the Brier score, the log-loss, the expected calibration error with 10 equal-width bins [18, 19] and reliability diagrams. "
  "Temperature scaling divides the logit by one parameter tau fitted on held-out data [18].")
P("**False discovery rate.** The false discovery proportion of a list is the fraction of wrong items. Benjamini and Hochberg [12] control its expectation with p-values. "
  "With posterior probabilities, the posterior expected FDP of a list is the mean of (1 - p) over the list, and the largest list with a given value is the Bayesian FDR "
  "selection [11].")

P("**What the base paper shows.** The paper uses three benchmarks: 160 synthetic datasets (five per setting, 75% built to mismatch Rhino's own configuration), the DREAM3 gene networks and the Netsim brain-region simulations. Its main results are below. "
  "The numbers are copied from the tables of the paper [1] and are not my runs. My own M3 reproduction of the same experiments is in the last row.")
rep.table("Table 1. Main results of the Rhino paper [1]", ["Benchmark and measure", "Rhino", "Comparison in the paper", "Reading"],
          [["Synthetic, temporal F1, true lag 2 (5, 10, 20, 40 nodes)", "0.59, 0.49, 0.39, 0.37", "Rhino with lag 1: 0.34, 0.28, 0.25, 0.20", "Best or close to best. History-dependent noise helps the lagged graph. A longer assumed lag (3) costs little"],
           ["DREAM3, AUROC of the summary graph, five networks", "0.685, 0.680, 0.664, 0.585, 0.567 (Rhino+g higher on the last two)", "eSRU: 0.660, 0.629, 0.627, 0.557, 0.550", "Rhino or Rhino+g is highest on all five networks"],
           ["Netsim, AUROC of the summary graph", "0.990", "cMLP 0.930, TCDF 0.910", "Without instantaneous effects Rhino drops to 0.930, so modelling them matters"],
           ["M3, Netsim, my reproduction with the authors' code", "0.987", "Not rerun", "Close to the paper's 0.990"]],
          [1.9, 1.5, 1.5, 1.6], size=8,
          note="Rhino+g is Rhino with Gaussian noise that does not depend on history. The paper reports the DREAM3 AUROC of Rhino and Rhino+g for the networks above; I show the Rhino value first.")
P("All of these measures compare the output with a known true graph. They say how accurate Rhino is. They do not say whether its probabilities can be trusted, and this is the gap that Section 2 takes up.")

# ------------------------------------------------------------------ 4 related work
H1("4. Related Work")
P("**Temporal causal discovery.** PCMCI+ [4] uses conditional independence tests with lags and instantaneous effects. DYNOTEARS [3] uses continuous "
  "optimisation with an acyclicity penalty [10]. VAR-LiNGAM [2] uses non-Gaussianity. Nonlinear Granger methods use neural networks [5, 6, 7]. "
  "Rhino [1] adds history-dependent noise and a posterior over graphs. A survey is in [9]. These works evaluate by F1, SHD or AUROC against a known graph.")
P("**Uncertainty and calibration of causal graphs.** Jabbari et al. [13] show that bootstrap estimates of edge probabilities are not guaranteed to be calibrated, and calibrate them "
  "after the fact for causal Bayesian networks. AVICI [14] reports the expected calibration error of its edge probabilities, for static graphs. "
  "PRCD-MAP [20] calibrates how much to trust an outside prior in the causal discovery objective. It does not study the final edge probabilities or the error "
  "of the selected edges (I read the abstract and a summary of the paper, not the full text). I did not find a study of the calibration of Rhino's posterior.")
P("**Error control for edges.** MMPC-p [15] controls the false discovery rate of a structure learner for time series with p-values. "
  "Bayesian FDR [11] and the Benjamini-Hochberg procedure [12] are the classical tools. Learn then Test [16] gives a general way to choose a parameter, "
  "such as my cutoff, so that a risk is controlled with a finite-sample guarantee. My cutoff rule has no such guarantee, and I say so in Section 15. "
  "**Position.** To my knowledge, I did not find earlier work that audits the posterior of a deep temporal causal model for error control. "
  "The search was limited, and I make no claim of being first.")

# ------------------------------------------------------------------ 5 SOTA positioning
H1("5. SOTA Positioning")
P("I follow the course loop: identify, understand, compare, validate, reposition.")
rep.table("Table 2. The anchor work and this project", ["Item", "Rhino (Gong et al., Microsoft Research, ICLR 2023) [1]", "This project"],
          [["Problem", "Causal discovery from time series with non-linear effects, instantaneous effects and history-dependent noise",
            "Can the posterior of such a model be used to select edges with a stated error budget?"],
           ["Representation", "SEM over time. Graph tensor [L+1, D, D]. Variational posterior q(G)", "Same posterior, plus a selection layer: forecasts p, a set S, a budget alpha"],
           ["Learning", "ELBO, augmented Lagrangian for acyclicity, Gumbel-softmax samples", "Rhino weights from M3. One temperature, or a cutoff, learned on other datasets"],
           ["Inference", "Edge probabilities, rounded graph, treatment effects", "Exact marginal p_e from the logits. Bayesian FDR set, learned cutoff"],
           ["Evaluation", "F1, SHD, AUROC, treatment effect RMSE. Synthetic, DREAM3, Netsim", "ECE, Brier, log-loss, realised FDP versus budget, power. Same data"],
           ["Findings", "Best or close to best on synthetic data and real benchmarks", "First test: the posterior is saturated. Calibration alone does not keep the promise. A learned cutoff comes close for moderate budgets"],
           ["Limits", "Cost. Hand-tuned settings. No uncertainty on the graph quality", "Needs labelled data. Average guarantee. Loses power. No transfer to DREAM3"]],
          [1.0, 2.7, 2.8], size=8)
P("**Compare and validate.** In M3 the F1 of Rhino was the highest of the six methods on synthetic data, with a significant gain over PCMCI+ at 5 and 10 nodes only. "
  "That comparison measures accuracy. This report measures trust. The two disagree: among the Rhino variants, the one with the lowest F1 (Rhino+s) is the only one whose raw probabilities are close to their promise (Section 12.6).")
P("**Reposition.** My M1 position was a study of uGLAD with a Microsoft Research anchor on causal order. After the change of base paper, my anchor is Rhino. "
  "I do not claim a better causal discovery algorithm, and I do not claim a new theory. The project is an idea for checking the trust of a published method, a plan to test it, "
  "and a first test on finished runs, with its limits. I did not survey work after the Rhino paper beyond the search in Section 4.")

# ------------------------------------------------------------------ 6 graphical representation
H1("6. Graphical Representation")
rep.figure("fig_model.png", "Fig. 2: Left, the temporal graph that Rhino models (three variables, lag 2). Middle, the posterior q(G) over its edges. "
           "Right, the selection layer added in this work.", 6.4)
P("**Variables and nodes.** The nodes are the D observed variables at each time step. An edge entry (l, i, j) means that variable i at time t - l is a direct cause of variable j at time t.")
P(r"**Factorization.** Given a graph $G$, the data follow")
rep.eq("", tex=r"p(X_t\mid X_{<t},G)=\prod_{i=1}^{D}p\big(x_{i,t}\mid \mathrm{Pa}_i^{<t},\mathrm{Pa}_i^{t},G\big).")
P(r"Each variable depends on its parents only. So $x_{i,t}$ is conditionally independent of its non-parents given its parents. The instantaneous slice must be acyclic. The lagged slices may contain any pattern, since time orders them.")
P("**The posterior as a second graphical model.** The posterior over graphs factorises as a product over node pairs and lags. For each pair (i, j) with i > j the instantaneous part "
  "is one categorical variable with three states: edge from j to i, edge from i to j, or no edge. For each lag l >= 1 and each (i, j) the lagged part is an independent Bernoulli variable "
  "[1]. This product form matters for my argument. The marginal probability of each entry is a simple function of the learned logits, so I can read it exactly (Section 8). "
  "The product form is also wrong in one respect: it ignores dependencies between edges, which the acyclicity penalty creates during training.")
P("**Why a PGM is appropriate.** The directed graph states which variables influence which, and the factorization turns this into a likelihood. "
  "The posterior over graphs turns structure learning into inference, and this is why a calibration question can be asked at all. "
  "A method that returns a single graph has no probabilities to check.")

# ------------------------------------------------------------------ 7 learning method
H1("7. Learning Method")
P(r"**Parameter and structure learning in Rhino.** Rhino maximises the evidence lower bound")
rep.eq("", tex=r"\mathrm{ELBO}=\mathbb{E}_{q(G)}\Big[\sum_{n}\log p(X_n\mid G)+\log p(G)\Big]+H\big(q(G)\big).")
P(r"The prior $p(G)$ rewards sparse graphs with a weight $\lambda_s$. An acyclicity penalty $h(G)=\mathrm{tr}\,\exp(G\circ G)-D$ [10] acts on the instantaneous part, and its weight grows in steps of an augmented Lagrangian method. Graph samples use the Gumbel-softmax estimator. The number of augmented Lagrangian steps is the training length. I did not retrain. I use the models of M3: Rhino with the settings printed in the paper ($\lambda_s=9$, lag 2), Rhino+g, Rhino+s, and Rhino with the released configuration.")
P("**What I learn in this report.** Two things, both on top of the frozen posterior, and both with labelled calibration data:")
rep.bullets([
    f"**Temperature.** p' = sigmoid(logit(p) / tau). One parameter, fitted by minimising log-loss on pooled entries of the calibration datasets. "
    f"The fit uses grouped 5-fold cross-validation over datasets, so a dataset never helps to fit the tau that is applied to it (numpy seed 0). Mean tau = {f2(TAU_M)} (SD {f2(TAU_S)}).",
    "**Cutoff.** For each budget alpha, find on the pooled calibration entries the lowest score cutoff (on the log-odds) so that the selected entries have FDP at most alpha. "
    "Cutoffs are placed only between distinct score values. A cutoff needs at least 10 entries. If no cutoff exists the rule selects nothing. "
    "One variant pools all calibration datasets. The other uses only datasets with the same number of nodes (it falls back to pooling if there are none).",
])
P("**Why these choices.** Temperature scaling is the standard single-parameter fix and it keeps the ranking [18]. The cutoff rule is the simplest direct way to hit a target FDP on average. "
  "It is the empirical version of choosing a parameter for risk control [16], without the finite-sample guarantee.")

# ------------------------------------------------------------------ 8 inference method
H1("8. Inference Method")
P("**What is inferred.** The marginal probability p_{e} of every edge entry, and from it a selected set S. These are the quantities a user would read from the posterior.")
P("**Exact marginals.** The saved weights hold the logits of q(G). For an instantaneous pair (i > j), p(j to i), p(i to j) and p(no edge) are the softmax of the three logits. "
  "For a lagged entry, p = softmax(logits_lag)[1]. For data sets whose truth is an aggregated graph (Netsim, DREAM3), the entry (i, j) is an edge if it exists at any lag, so "
  "p = 1 - product over lags of (1 - p_l). This is exact under q, because the lags are independent. "
  f"I check this against the mean of the 100 graphs that the official code saves. The mean absolute difference is {CHK_MEAN} over all entries of the 760 exported runs "
  f"(the largest per-run mean is {CHK_JOB}, and the largest single difference is {CHK_MAX}). The largest value is what 100 samples give by chance over about a million entries, and a "
  "wrong mapping would give much larger differences.")
P("**Why exact and not sampled.** 100 samples give a resolution of 0.01 and many ties at 0 and 1. Exact values break the ties and show how far the saturation goes. "
  "I report the sampled version as a robustness check (Appendix C). The conclusions do not change.")
P("**Bayesian FDR selection.** Sort the entries by p, take cumulative means of (1 - p) and keep the largest top-k with mean at most alpha. This takes O(E log E) time for E entries, "
  "which is negligible. The cost of the whole approach is the training of the model, which in M3 was about 170 times that of PCMCI+ at 20 nodes.")

# ------------------------------------------------------------------ 9 experimental setup
H1("9. Experimental Setup")
P(f"**Data and models.** All runs are the finished runs of M3 [Appendix C]. Synthetic: the authors' generator [21], 5, 10 and 20 nodes, graph family ER or SF, with or without instantaneous effects, "
  f"with or without history-dependent noise, data seeds 0 to 4, 40 datasets per dimension, 120 datasets per method. One model seed per dataset. Rhino, Rhino+g and Rhino+s run on all 120. "
  f"The released configuration of Rhino ran on 80. A dataset has 70, 290 or 1,180 edge entries (3 N^{2} - N for N = 5, 10, 20), so the 120 Rhino datasets give {NENT} entries. "
  "Real: Netsim Sim-3 (15 regions, 5 runs per setting) and DREAM3 size 100 (5 networks, 5 seeds). Truth for Netsim and DREAM3 is an aggregated graph.")
P("**Protocol.** (1) Read the exact p of each run and the true graph. (2) For the synthetic runs, fit the calibration on 4/5 of the datasets and apply it to the other 1/5, five times. "
  "(3) For the real data, fit on all synthetic Rhino runs and apply to the real runs, which tests a shift of distribution. (4) Compute all KPIs per dataset. "
  "I do not change any condition between methods. Hardware and software: M3 runs used Windows 11, Python 3.9, torch 1.12.1 on CPU. "
  "The analysis of this report runs on Python 3.14 with numpy 2.4.2, scipy 1.17.1, pandas 3.0.1 and scikit-learn 1.9.0. Commands and seeds are in Code/README.md.")
P("**Statistics.** Mean and standard deviation over datasets. 95% intervals from the t distribution, except the pooled ECE, which uses a bootstrap over datasets (1000 resamples, seed 0). "
  "Paired comparisons use the Wilcoxon signed-rank test [17] with the Holm correction [8].")

# ------------------------------------------------------------------ 10 baselines
H1("10. Baselines")
rep.table("Table 3. Selection rules compared (same data, same folds)", ["Rule", "How it chooses the edge set", "Uses labels?"],
          [["Raw, threshold 0.5", "Round q(G) at 0.5. This is how Rhino's graph is read in the paper", "No"],
           ["Raw, Bayesian FDR", "Largest top-k with mean(1 - p) <= alpha, using Rhino's p as given", "No"],
           ["Temperature, Bayesian FDR", "Same, after p' = sigmoid(logit(p)/tau), tau from other datasets", "Calibration datasets"],
           ["Temperature, expected F1", "Top-k that maximises 2 sum(p') / (k + sum of all p')", "Calibration datasets"],
           ["Learned cutoff (pooled, or same size)", "Log-odds cutoff with pooled FDP <= alpha on other datasets", "Calibration datasets"],
           ["Oracle threshold", "Best F1 over all thresholds, using the truth. An upper bound, not usable", "Truth of the test dataset"]],
          [1.8, 3.7, 1.0], size=8.5)
P("The first two rows are the practice that the paper suggests. The oracle is a ceiling. M3 compared Rhino with PCMCI+, DYNOTEARS and VAR-LiNGAM on accuracy. "
  "These methods return no probabilities, so they cannot take part in a calibration comparison. I use Rhino+g and Rhino+s as comparators, since they change only the noise model.")

# ------------------------------------------------------------------ 11 KPIs
H1("11. KPIs")
rep.table("Table 4. KPIs and why each one is used", ["Layer", "KPI", "Why", "Caveat"],
          [["Representation", "Share of entries with p < 0.001 or > 0.999. Edge rate in each group", "Shows how saturated the posterior is, and how often certainty is wrong", "Depends on the 0.001 cut"],
           ["Learning", "Brier score, log-loss, pooled ECE (10 bins)", "Probability quality, as the course asks", "ECE is small when edges are rare, even for bad rankings"],
           ["Learning", "tau (fitted temperature)", "Size of the overconfidence in one number", "Single global value"],
           ["Inference", "Realised FDP against budget alpha, promised error, empty-set rate", "Direct test of the claim 'at most alpha wrong'", "Empty set counts as FDP 0, so power must be read with it"],
           ["Inference", "Power (recall of true edges)", "Price of control", "Needs the truth"],
           ["Structure", "AUROC, AUPRC, F1 at 0.5, oracle F1", "Quality of the ranking and of the graph", "AUROC pools entries per dataset"],
           ["Cost", "Training time (M3), selection time", "Practical cost", "CPU only"]],
          [0.9, 2.0, 2.1, 1.5], size=8)

# ------------------------------------------------------------------ 12 results
H1("12. Results")
P("These results are a first test of the plan in Section 2.5 on finished M3 runs. They are one benchmark family, one model seed per dataset, and a small real-data part. I read them as early evidence for the idea and not as a validation of it.")
H2("12.1 The posterior is saturated")
P(f"Over {NENT} synthetic entries of Rhino, {pc(S.frac_p_eq_0)} have p below 0.001 and {pc(S.frac_p_eq_1)} have p above 0.999. Only a small part lies in between. "
  f"Among the entries that Rhino calls certainly absent, {pc(ER0)} are true edges. Among the entries it calls certainly present, {pc(1 - ER1)} are not edges (Fig. 3, Table 5).")
rep.figure("fig_reliability_synth_rhino_exact.png", "Fig. 3: Left, reliability diagram, pooled over 120 synthetic datasets, exact probabilities. Right, histogram of the probabilities (log scale).", 6.2)
rep.table("Table 5. Probability quality, Rhino (paper settings), 120 synthetic datasets",
          ["Variant", "Pooled ECE [95% CI]", "Brier (pooled)", "Log-loss (pooled)", "Brier, mean ± SD over datasets", "AUROC", "AUPRC"],
          [[v, f"{q.loc[k,'ece_pooled']:.3f} [{q.loc[k,'ece_pooled_ci_lo']:.3f}, {q.loc[k,'ece_pooled_ci_hi']:.3f}]", f3(q.loc[k, "brier_pooled"]),
            f2(q.loc[k, "logloss_pooled"]), f"{q.loc[k,'brier_mean']:.3f} ± {q.loc[k,'brier_sd']:.3f}", f3(q.loc[k, "auroc_mean"]), f3(q.loc[k, "auprc_mean"])]
           for v, k in (("Raw q(G)", "raw"), ("Temperature scaled", "temperature"))],
          [1.2, 1.5, 0.7, 0.8, 1.2, 0.5, 0.5], size=8,
          note="Log-loss clips probabilities at 1e-6. AUROC and AUPRC are means over datasets and are identical for both rows because temperature scaling keeps the ranking (Proposition 3).")
P("**What happened.** Rhino's probabilities are close to 0 or 1 and both kinds of certainty are often wrong. **Was it expected?** Partly. M3 showed that training makes the posterior more "
  "confident. **Why?** The variational posterior is trained to maximise the likelihood of the data, and the acyclicity penalty and the entropy term push the logits apart as the number of augmented Lagrangian steps grows. "
  "I did not isolate the cause, and Section 12.7 gives indirect evidence only. **What it tells us.** The posterior does not report uncertainty about the graph in a usable way.")

H2("12.2 The trust gap: promised and realised error")
P(f"At a budget of 0.01 the raw posterior promises an error of {f3(r_raw[0.01].promised_mean)}. The realised FDP is {fci(r_raw[0.01])}. "
  f"At a budget of 0.1 it is {fci(r_raw[0.10])}, and at 0.2 it is {fci(r_raw[0.20])}. So H1 is supported. By the identity of Section 2.3, the gap equals the overconfidence of the posterior on the selected set. "
  f"The sampled estimate of p (100 graphs) gives the same result: {fci(row(frs,'raw',0.01))} at a budget of 0.01.")
P(f"The dependence on the data is strong (Table 6). Rhino is much better when the noise is history-dependent, which is the case it was designed for, and worse when the graph is larger. "
  f"For example, at 5 nodes with history-dependent noise the realised FDP at budget 0.1 is {f3(br.iloc[1].fdp_at_alpha_0_1_raw)} and the AUROC is {f3(br.iloc[1].auroc)}. "
  f"At 20 nodes without history-dependent noise they are {f3(br.iloc[4].fdp_at_alpha_0_1_raw)} and {f3(br.iloc[4].auroc)}.")
rep.table("Table 6. Rhino (paper settings) by dataset type, exact probabilities, 20 datasets per row",
          ["Nodes", "History-dependent noise", "AUROC", "Brier", "F1 at 0.5", "Oracle F1", "Realised FDP at budget 0.1 (raw)"],
          [[int(r.dim), "yes" if r.history_dependent_noise == 1 else "no", f3(r.auroc), f3(r.brier), f3(r.f1_thr05), f3(r.f1_oracle), f3(r.fdp_at_alpha_0_1_raw)] for r in br.itertuples()],
          [0.6, 1.3, 0.7, 0.7, 0.8, 0.8, 1.6], size=8.5,
          note="F1 is computed over all temporal edge entries. It matches the orientation F1 of the M3 report (0.67, 0.55, 0.44 at 5, 10, 20 nodes), which shows that the export reads the same graphs.")

H2("12.3 Temperature scaling repairs the scores, not the error control")
P(f"The fitted temperature is {f2(TAU_M)} (SD {f2(TAU_S)} over folds). It lowers the pooled ECE from {f3(q.loc['raw','ece_pooled'])} to {f3(q.loc['temperature','ece_pooled'])}, "
  f"the pooled Brier score from {f3(q.loc['raw','brier_pooled'])} to {f3(q.loc['temperature','brier_pooled'])}, and the pooled log-loss from {f2(q.loc['raw','logloss_pooled'])} to {f2(q.loc['temperature','logloss_pooled'])} (Table 5). "
  f"The per-dataset differences are significant (Table 10). But error control is not restored (Table 7, Fig. 4). At budgets of 0.01 and 0.05 the rule selects no edges at all. "
  f"At 0.1 it selects edges in {pc(1 - r_tmp[0.10].frac_empty)} of the datasets. At 0.2 it promises {f3(r_tmp[0.20].promised_mean)}, and the realised FDP is {fci(r_tmp[0.20])}. "
  "So H2 is supported for the scores and not supported for error control. "
  "**Why.** ECE and log-loss measure the average match over all entries, and most entries are easy ones with p near 0. Error control depends on the match in the top of the ranking, "
  "and this part stays overconfident. A better ECE is therefore a poor guide to whether the selected edges are reliable.")

H2("12.4 A cutoff learned on other datasets")
P(f"The learned cutoff (pooled) gives a realised FDP of {fci(r_cut[0.10])} at budget 0.1, {fci(r_cut[0.20])} at 0.2 and {fci(r_cut[0.30])} at 0.3. "
  f"The same-size variant gives {fci(r_cd[0.10])}, {fci(r_cd[0.20])} and {fci(r_cd[0.30])}. At budgets of 0.1 and 0.3 the intervals contain or lie below the budget. At 0.2 the pooled cutoff is above it (interval {r_cut[0.20].fdp_ci_lo:.3f} to {r_cut[0.20].fdp_ci_hi:.3f}) and the same-size cutoff contains it, "
  f"so control is approximate and not exact. The price is power: {f3(r_cut[0.10].power_mean)} at 0.1, {f3(r_cut[0.20].power_mean)} at 0.2 and {f3(r_cut[0.30].power_mean)} at 0.3, "
  f"and at budget 0.1 the rule selects nothing in {pc(r_cut[0.10].frac_empty)} of the datasets. Compared with the raw rule, which has {f3(r_raw[0.20].power_mean)} power at budget 0.2 but a realised FDP of {f3(r_raw[0.20].fdp_mean)}, "
  "the learned cutoff gives up power to keep its promise.")
rep.figure("fig_fdr_control_synth_rhino_exact.png", "Fig. 4: Realised false discovery proportion (left) and power (right) against the nominal budget, Rhino (paper settings), 120 datasets, exact probabilities. Bars: 95% t intervals over datasets.", 6.4)
rows6 = []
for a in (0.05, 0.10, 0.20, 0.30):
    rows6.append([a, f3(r_raw[a].promised_mean), fci(r_raw[a]), f3(r_raw[a].power_mean), fci(r_tmp[a]), f"{f3(r_tmp[a].power_mean)} / {pc(r_tmp[a].frac_empty)}",
                  fci(r_cut[a]), f"{f3(r_cut[a].power_mean)} / {pc(r_cut[a].frac_empty)}"])
rep.table("Table 7. Error control at budget alpha: realised FDP [95% CI] and power / share of datasets with an empty selection",
          ["alpha", "Raw: promised", "Raw: realised", "Raw: power", "Temperature: realised", "Temp.: power / empty", "Learned cutoff: realised", "Cutoff: power / empty"],
          rows6, [0.4, 0.6, 1.05, 0.5, 1.05, 0.75, 1.05, 0.75], size=7.5,
          note="An empty selection counts as FDP = 0. The shares of empty selections show how much of a low realised FDP comes from selecting nothing.")
P("**Reading.** The H5 result is mixed. The learned cutoff keeps the error near the budget for budgets of 0.1 to 0.3, but at budgets of 0.05 or lower it has almost no power. "
  "For this benchmark the smallest useful budget is about 0.1. Section 12.7 shows that this does not hold on real data. H5 was added after the H2 result, so it is an exploratory finding.")

H2("12.5 Choosing a graph: the expected-F1 rule")
P(f"After temperature scaling, the graph that maximises the expected F1 under the posterior gives an F1 of {f3(GR[('temperature','expected-F1 rule')])}. A threshold of 0.5 gives {f3(GR[('temperature','threshold 0.5')])}, "
  f"and the oracle threshold gives {f3(GR[('temperature','oracle threshold (uses truth)')])}. The paired difference to the 0.5 threshold is {pt.loc['F1, expected-F1 rule','mean_diff_cal_minus_raw']:+.3f} "
  f"[{pt.loc['F1, expected-F1 rule','ci_lo']:+.3f}, {pt.loc['F1, expected-F1 rule','ci_hi']:+.3f}] (Holm p = {pv(pt.loc['F1, expected-F1 rule','p_holm'])}). "
  "So H3 is not supported: the label-free rule is slightly worse than a plain threshold, and even the plain threshold is about 0.09 below the oracle. "
  "**Why.** The rule needs the probabilities to be calibrated in the region that decides the F1, and temperature scaling does not give this (Section 12.3). "
  "**What it tells us.** The gap to the oracle is the value of knowing the right threshold for each dataset. The paper tunes the threshold on DREAM3 with the truth, which hides this gap.")

H2("12.6 Accuracy against trust across the Rhino variants")
rep.table("Table 8. Variants of Rhino, exact probabilities (budget 0.1 for the raw rule, budget 0.2 for the learned cutoff)",
          ["Variant", "Runs", "AUROC", "F1 (0.5)", "Wrong at p > 0.999", "Share p > 0.999", "ECE", "Raw FDP (0.1)", "Raw power (0.1)", "Cutoff FDP (0.2)", "Cutoff power (0.2)"],
          vrows, [1.2, 0.4, 0.6, 0.5, 0.55, 0.5, 0.45, 0.5, 0.5, 0.5, 0.5], size=7,
          note="Rhino (released config) has 80 runs on a different subset of datasets. It is not paired with the other rows.")
P(f"Rhino has the best ranking and the best F1 of the variants that ran on all 120 datasets (AUROC {vrows[0][2]}, F1 {vrows[0][3]}). Its trust is poor ({vrows[0][7]} realised at a budget of 0.1), and Rhino+g is worse ({vrows[1][7]}). "
  f"Rhino+s has a weaker ranking (AUROC {vrows[2][2]}) and much lower F1 ({vrows[2][3]}), "
  f"but its raw posterior is close to its promise: {vrows[2][7]} realised at a budget of 0.1. Many of its selections are empty ({pc(sa.loc['synth_rhino_s']['empty_raw_a0.1'])} of the datasets at budget 0.1), so part of this is selecting little. "
  "I read this as an accuracy against trust trade-off between the noise models. I do not claim a cause. A model that fits the noise more flexibly may also produce a more saturated posterior. I did not test this.")

H2("12.7 Real data and the shift of distribution")
rep.table("Table 9. Real data. Tau and cutoffs are fitted on the synthetic Rhino runs only. Raw rule at budget 0.1, temperature and cutoff at budget 0.2",
          ["Data", "Runs", "AUROC", "Raw FDP (0.1)", "Raw power (0.1)", "Temp. FDP (0.2)", "Temp. power (0.2)", "Cutoff FDP (0.2)", "Cutoff power (0.2)"],
          rrows, [1.3, 0.45, 0.65, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6], size=7.5,
          note="Netsim has 5 runs per setting, so intervals are wide and I report means only. DREAM3 has 25 runs (5 networks times 5 seeds).")
P(f"On Netsim with the paper's training steps, the raw posterior is close to its promise ({f3(NP['fdp_raw_a0.1'])} realised at budget 0.1). With the released configuration, which trains for a different number of augmented Lagrangian steps, "
  f"it is not ({f3(NR['fdp_raw_a0.1'])}). The two settings differ in more than the number of steps that I could isolate, and each has 5 runs. This is indirect evidence for the link between training length and overconfidence, and no more than that. "
  f"On the synthetic runs, the released configuration has more entries with p above 0.999 ({pc(sa.loc['synth_rhino_shipped'].frac_p_eq_1)} against {pc(S.frac_p_eq_1)}) and a higher ECE ({f3(sa.loc['synth_rhino_shipped'].ece_raw)} against {f3(S.ece_raw)}), "
  "which points in the same direction.")
P(f"On DREAM3 the method fails. The AUROC is {f3(DR.auroc_mean)}, and {pc(DR['fdp_raw_a0.1'])} of the edges selected at budget 0.1 are wrong. The temperature and the cutoffs from synthetic data do not help: the learned cutoff gives a realised FDP of "
  f"{rrows[2][7]} at budget 0.2. The temperature fitted on synthetic data also does not transfer to Netsim: with the paper's steps it is too strong and the rule selects nothing, even at budget 0.2 (Table 9). "
  "So H4 holds in its second form: the guarantee does not transfer, and it degrades in line with Proposition 2. When the ranking is poor (DREAM3), no calibration can help (Proposition 3).")

# ------------------------------------------------------------------ 13 statistical analysis
H1("13. Statistical Analysis")
rows9 = []
for qn in ("Brier", "log-loss", "ECE (per dataset)", "F1, expected-F1 rule"):
    r = pt.loc[qn]
    rows9.append([qn + (" (vs threshold 0.5)" if qn.startswith("F1") else ""), f"{r.mean_diff_cal_minus_raw:+.3f} [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]", f"{int(r.wins_cal)} / {int(r.wins_raw)}", pv(r.p_holm)])
for t in sel_tests:
    rows9.append([f"|FDP - alpha|, alpha = {t['a']:.1f}: learned cutoff minus {'raw' if t['other']=='raw' else 'temperature'}",
                  f"{t['mean']:+.3f} [{t['lo']:+.3f}, {t['hi']:+.3f}]", f"{t['wins']} / {t['loss']}", pv(t['ph'])])
rep.table("Table 10. Paired comparisons over the 120 synthetic datasets (mean difference [95% t interval], wins / losses, Holm-corrected Wilcoxon p)",
          ["Quantity (second method minus first)", "Mean difference [95% CI]", "Wins / losses", "p (Holm)"], rows9, [3.3, 1.7, 0.8, 0.7], size=8,
          note="For Brier, log-loss, ECE and |FDP - alpha| a negative difference is better for the second method. Wins are counted in favour of the second method, and ties are not counted. For the F1 row, the difference is the expected-F1 rule minus the 0.5 threshold, after temperature scaling.")
P("**Reading.** Temperature scaling improves the Brier score, the log-loss and the ECE on most datasets, and the differences are far from zero. The learned cutoff is much closer to the budget than the raw rule at both budgets. "
  "Against temperature scaling the answer depends on the budget. At 0.1 both rules select nothing on most datasets, so most comparisons are ties, and the cutoff is slightly farther from the budget (+0.021, interval touching zero). "
  "At 0.2 the cutoff is closer (-0.023, 71 wins against 47 losses). I applied the Holm correction within this family of tests. **Sources of uncertainty.** The intervals show spread over datasets. "
  "Each dataset has one model seed, so I cannot separate dataset spread from training noise. The Netsim comparisons rest on 5 runs, and the DREAM3 numbers on 25 runs from 5 networks, so they are not independent. "
  "The bootstrap interval of the ECE resamples datasets, not entries.")
rep.table("Table 11. Expectations and outcomes", ["Hypothesis", "Outcome", "Evidence"],
          [["H1 raw posterior breaks its budget", "Supported", f"Realised FDP {f3(r_raw[0.01].fdp_mean)} at budget 0.01 and {f3(r_raw[0.10].fdp_mean)} at 0.1, intervals far above the budget"],
           ["H2 temperature fixes scores and control", "Scores: supported. Control: not supported", f"ECE {f3(q.loc['raw','ece_pooled'])} to {f3(q.loc['temperature','ece_pooled'])}. FDP at 0.2 is {f3(r_tmp[0.20].fdp_mean)} against {f3(r_tmp[0.20].promised_mean)} promised"],
           ["H3 expected-F1 rule beats threshold 0.5", "Not supported", f"F1 {f3(GR[('temperature','expected-F1 rule')])} against {f3(GR[('temperature','threshold 0.5')])}"],
           ["H4 tau transfers to real data, or degrades as predicted", "Does not transfer. Degrades as predicted", "Netsim over-corrected, DREAM3 fails because the ranking is weak"],
           ["H5 learned cutoff gives FDP near alpha (exploratory)", "Partly supported", f"Within or near the budget for 0.1 to 0.3 on synthetic data. Power {f3(r_cut[0.10].power_mean)} to {f3(r_cut[0.30].power_mean)}. Fails on DREAM3"]],
          [2.2, 1.6, 2.7], size=8)

# ------------------------------------------------------------------ 14 discussion
H1("14. Discussion")
P("**What the results mean.** A Bayesian graph posterior is only useful for error control if it is calibrated where the decisions are made. Rhino's is not. It is saturated, and the certainty is often wrong. "
  "The identity of Section 2.3 reads the failure in one line: the realised error is the promised error plus the overconfidence on the selected set. Standard calibration reduces the average overconfidence and "
  "leaves the part in the top of the ranking. That is why the ECE drops by a factor of five while the realised FDP at budget 0.2 stays 0.12 above the promise.")
P("**What works, and when.** A cutoff learned on similar datasets gives approximate control for moderate budgets, and it needs no change of the model. It works because it uses the labels exactly where the decision is made. "
  "It fails when the calibration data do not resemble the new data (DREAM3, and partly Netsim) and when the ranking is weak.")
P("**Benefits and costs for a practitioner.** Benefit: one can state a budget and get a list, at a small and known price in power. Cost: one needs labelled graphs from a similar setting, "
  "the guarantee is on average and not per dataset, and for small budgets the list is empty. In a field where no such labelled data exist (most real applications), "
  "the honest advice from this study is to treat Rhino's probabilities as a ranking and not as probabilities.")
P("**What I learned.** Reproducing a paper is not enough to say that its output can be used. The accuracy ranking of the variants and their trust ranking differ. "
  "A good-looking calibration metric can hide a failure in the part of the ranking that matters. The metrics chosen at the start (realised FDP against budget) were the ones that exposed this.")
P("**Revisiting M1 and M2.** The research question of M1 and M2 was about uGLAD. It is replaced here. What survived is the KPI discipline (precision, recall, F1, SHD), the habit of checking my own implementation against "
  "the authors' output, and the habit of reporting what did not reproduce. M3 reproduced the base paper, and this report asks a question that it did not ask.")

# ------------------------------------------------------------------ 15 limitations
H1("15. Limitations")
rep.bullets([
    "**Average guarantee only.** The cutoff controls the expected FDP over datasets like the calibration datasets. It gives no finite-sample guarantee and no per-dataset guarantee. A method such as Learn then Test [16] would give a finite-sample bound. I did not implement it.",
    "**Needs labelled graphs** from similar data. This is the main practical cost.",
    "**Transfer fails** from synthetic to DREAM3, and partly to Netsim. Netsim has 5 runs per setting.",
    "**Weak ranking limits everything.** Calibration cannot repair it (Proposition 3).",
    "**Training length is only indirectly tested.** The comparison of paper and released settings is confounded, and the runs are few. I did not run a controlled sweep of the number of steps.",
    "**One model seed per dataset.** I cannot separate training noise from dataset variation.",
    "**Scope.** 5, 10 and 20 nodes, one family of models, no 40-node runs. No missing data, no hidden confounders and no non-stationary noise beyond what the model assumes.",
    "**Cycle removal.** I select edge entries without enforcing that the instantaneous part is acyclic. A graph with cycles would need removal of edges, which breaks Proposition 2. I did not measure this.",
    "**Product-form posterior.** Rhino's q(G) ignores dependencies between edges. The identity holds regardless, but the probabilities themselves may be poor for this reason.",
    "**Related work.** The search for earlier work was short. I read the PRCD-MAP paper only in summary.",
])

# ------------------------------------------------------------------ 16 conclusion
H1("16. Conclusion")
P("I asked whether the edge probabilities of Rhino can be trusted for error-controlled selection. In this first test on 500 finished runs the answer is no for the raw posterior: it is saturated and overconfident, and at a budget of 0.01 about 31% of the selected edges are wrong. "
  "Temperature scaling makes the probabilities score well and leaves the error control broken. A cutoff learned on other datasets restores approximate control for budgets of about 0.1 to 0.3, at a large cost in power, and it does not transfer to DREAM3. "
  "The identity between promised error, realised error and overconfidence is consistent with each of these outcomes. These are early results on one benchmark family, and they support the idea only within the limits of Section 15.")
P("**Next research steps.** (1) Replace the learned cutoff by a rule with a finite-sample guarantee. (2) Test the link between training length and saturation with a controlled sweep and a posterior that is regularised against saturation. "
  "(3) Use an ensemble over model seeds or a posterior that models dependencies between edges, and see whether the ranking improves. (4) Repeat the audit for other graph posteriors. (5) Extend to 40 nodes, to missing data and to hidden confounders.")

# ------------------------------------------------------------------ references
REFS = [
    "W. Gong, J. Jennings, C. Zhang, and N. Pawlowski, \"Rhino: Deep Causal Temporal Relationship Learning with History-dependent Noise,\" in International Conference on Learning Representations (ICLR), 2023, arXiv:2210.14706.",
    "A. Hyvarinen, K. Zhang, S. Shimizu, and P. O. Hoyer, \"Estimation of a structural vector autoregression model using non-Gaussianity,\" Journal of Machine Learning Research, vol. 11, 2010.",
    "R. Pamfil et al., \"DYNOTEARS: Structure learning from time-series data,\" in International Conference on Artificial Intelligence and Statistics (AISTATS), PMLR, pp. 1595-1605, 2020.",
    "J. Runge, \"Discovering contemporaneous and lagged causal relations in autocorrelated nonlinear time series datasets,\" in Conference on Uncertainty in Artificial Intelligence (UAI), PMLR, pp. 1388-1397, 2020.",
    "S. Khanna and V. Y. F. Tan, \"Economy statistical recurrent units for inferring nonlinear Granger causality,\" arXiv:1911.09879, 2019.",
    "A. Tank, I. Covert, N. Foti, A. Shojaie, and E. Fox, \"Neural Granger causality for nonlinear time series,\" 2018.",
    "M. Nauta, D. Bucur, and C. Seifert, \"Causal discovery with attention-based convolutional neural networks,\" Machine Learning and Knowledge Extraction, vol. 1, no. 1, p. 19, 2019.",
    "S. Holm, \"A simple sequentially rejective multiple test procedure,\" Scandinavian Journal of Statistics, vol. 6, no. 2, pp. 65-70, 1979.",
    "C. K. Assaad, E. Devijver, and E. Gaussier, \"Survey and evaluation of causal discovery methods for time series,\" Journal of Artificial Intelligence Research, vol. 73, pp. 767-819, 2022.",
    "X. Zheng, B. Aragam, P. Ravikumar, and E. P. Xing, \"DAGs with NO TEARS: Continuous optimization for structure learning,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 31, 2018.",
    "M. A. Newton, A. Noueiry, D. Sarkar, and P. Ahlquist, \"Detecting differential gene expression with a semiparametric hierarchical mixture method,\" Biostatistics, vol. 5, no. 2, pp. 155-176, 2004.",
    "Y. Benjamini and Y. Hochberg, \"Controlling the false discovery rate: a practical and powerful approach to multiple testing,\" Journal of the Royal Statistical Society, Series B, vol. 57, no. 1, pp. 289-300, 1995.",
    "F. Jabbari, M. P. Naeini, and G. F. Cooper, \"Obtaining accurate probabilistic causal inference by post-processing calibration,\" arXiv:1712.08626, 2017.",
    "L. Lorch, S. Sussex, J. Rothfuss, A. Krause, and B. Scholkopf, \"Amortized inference for causal structure learning,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 35, pp. 13104-13118, 2022.",
    "B. Guillen Pegueroles, B. Vinzamuri, K. Shanmugam, S. Hedden, J. D. Moyer, and K. R. Varshney, \"Structure learning from time series with false discovery control,\" arXiv:1805.09909, 2018.",
    "A. N. Angelopoulos, S. Bates, E. J. Candes, M. I. Jordan, and L. Lei, \"Learn then Test: Calibrating predictive algorithms to achieve risk control,\" arXiv:2110.01052, 2021.",
    "F. Wilcoxon, \"Individual comparisons by ranking methods,\" Biometrics Bulletin, vol. 1, no. 6, pp. 80-83, 1945.",
    "C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, \"On calibration of modern neural networks,\" in International Conference on Machine Learning (ICML), PMLR 70, pp. 1321-1330, 2017.",
    "M. P. Naeini, G. F. Cooper, and M. Hauskrecht, \"Obtaining well calibrated probabilities using Bayesian binning,\" in AAAI Conference on Artificial Intelligence, 2015.",
    "X. Shan and D. Zhou, \"PRCD-MAP: Learning how much to trust imperfect priors in causal discovery,\" arXiv:2605.01669, 2026.",
    "Microsoft, causica (Rhino code), release v0.0.0, github.com/microsoft/causica/tree/v0.0.0.",
]
rep.references(REFS)

# ------------------------------------------------------------------ appendix
H1("Appendix A. The identity and two standard facts")
P("The first item is the identity of Section 2.3. The other two are standard facts that I state for completeness and that the code checks. I do not present them as results of this project.")
P(r"**Proposition 1 (identity).** For a non-empty set $S$, $\mathrm{FDP}(S)=\frac{1}{|S|}\sum_{e\in S}(1-y_e)=1-\bar y_S$ and $a(S)=1-\bar p_S$, where the bars are means over $S$. So $\mathrm{FDP}(S)-a(S)=\bar p_S-\bar y_S=o(S)$. This is an identity for any $S$, any dataset and any $p$. The code checks it in tests/test_calib_fdr.py.")
P(r"**Proposition 2 (control under calibration).** Let $p=(p_e)$ be the vector of forecasts of a dataset and let the set $S=S(p)$ be a function of $p$ only. Assume $\mathbb{E}[y_e\mid p]=p_e$ for every $e$. Then $\mathbb{E}\big[\sum_{e\in S}(1-y_e)\mid p\big]=\sum_{e\in S}(1-p_e)$ by linearity of expectation, since $S$ is fixed given $p$. Dividing by $|S|$ gives $\mathbb{E}[\mathrm{FDP}(S)\mid p]=a(S)$. For $S=S_\alpha$, $a(S)\le\alpha$. If instead $\mathbb{E}[y_e\mid p]\ge p_e-\varepsilon$, the same steps give $\mathbb{E}[\mathrm{FDP}(S)\mid p]\le a(S)+\varepsilon$. No independence between the $y_e$ is used.")
P(r"**Proposition 3 (rank invariance).** Let $g$ be strictly increasing and let $p'=g(p)$. The order of entries by $p'$ equals the order by $p$. So the sets of the top-$k$ entries are identical for each $k$, and so are AUROC and AUPRC. Only the mapping from $k$ to the promised error $a(S_k)$ changes.")
P(r"**Remark (what is not proved).** The learned cutoff rule has an in-sample guarantee on the pooled calibration entries. I do not prove a bound on the FDP for a new dataset. Section 12.4 is empirical.")
H1("Appendix B. Exact marginals of q(G)")
P(r"Let $l_0,l_1,l_2$ be the three logits of an instantaneous pair $(i>j)$ and let $\pi=\mathrm{softmax}(l)$. Then $P(\text{edge from } j \text{ to } i)=\pi_0$, $P(\text{edge from } i \text{ to } j)=\pi_1$ and $P(\text{no edge})=\pi_2$. For a lagged entry with logits $(m_0,m_1)$, $P(\text{edge})=e^{m_1}/(e^{m_0}+e^{m_1})$. The log-odds of an entry are $l_k-\log\sum_{j\ne k}e^{l_j}$, or $m_1-m_0$. I keep the log-odds for the ranking of entries whose probability rounds to 1 in floating point. The code is Code/src/export_exact_q.py. A numpy simulation of the same layout agrees with a direct Monte Carlo sampling of the categorical and Bernoulli variables to within 0.002 ($2\times 10^5$ samples, largest difference 0.0016).")
H1("Appendix C. Robustness, reproducibility and files")
rows_a = []
for k, lab in (("raw", "Raw"), ("temperature", "Temperature")):
    rows_a.append([lab, f3(qs.loc[k, "ece_pooled"]), f3(q.loc[k, "ece_pooled"]), f2(qs.loc[k, "logloss_pooled"]), f2(q.loc[k, "logloss_pooled"]),
                   fci(row(frs, k, 0.10)), fci(row(fr, k, 0.10))])
rep.table("Table A1. Sampled probabilities (100 graphs per run) against exact probabilities, Rhino, 120 datasets",
          ["Variant", "ECE (sampled)", "ECE (exact)", "Log-loss (sampled)", "Log-loss (exact)", "Realised FDP at 0.1 (sampled)", "Realised FDP at 0.1 (exact)"], rows_a,
          [0.9, 0.7, 0.7, 0.8, 0.8, 1.3, 1.3], size=8,
          note="The conclusions are the same. The log-loss of the raw posterior differs because sampled values are exactly 0 or 1 more often.")
P("**Reproduction.** (1) M3 runs, see M3 folder, Code/README.md. (2) On the workstation, Code/workstation/ builds the two return files: export_qG.py (100-sample estimate) and export_exact_q.py (exact probabilities). "
  "(3) python run_all_analysis.py --exact, then python run_all_analysis.py (Code/src). (4) python make_model_figure.py, python build_report.py. Seeds: the fold split and the bootstrap use numpy seed 0. "
  "All tables are in Results/tables, all figures in Results/figures, and the exported probabilities in Results/qG_export and Results/qG_exact.")
P("**Analysed runs.** 760 runs were exported. 500 are analysed here: Rhino 120, Rhino+g 120, Rhino+s 120, Rhino released config 80, Netsim Rhino 10 (two settings), DREAM3 Rhino and Rhino+g 50. "
  "The lag ablation runs and Rhino+NoInst on Netsim were exported but not analysed.")

os.makedirs(OUTDIR, exist_ok=True)
rep.save()
