"""Builds the Milestone 3 report (docx, then PDF through Word). All numbers come from the exported result files."""
import math, os
import numpy as np, pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor

R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Results"))
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(R, "tables", "report_extra"); FIG = os.path.join(R, "figures", "report")
NAME = "M3_g12_th_conditional-ind-graphs_ind_Report"
DOCX = os.path.normpath(os.path.join(HERE, "..", "..", "Report", NAME + ".docx"))

sm = pd.read_csv(os.path.join(R, "tables", "synth_summary_orientation.csv"))
pr = pd.read_csv(os.path.join(R, "tables", "synth_paired_orientation.csv"))
rt = pd.read_csv(os.path.join(R, "tables", "synth_runtime.csv"))
t1 = pd.read_csv(os.path.join(R, "tables", "table1_lag_ablation.csv"))
t1p = pd.read_csv(os.path.join(R, "tables", "table1_lag_paired_tests.csv"))
te = pd.read_csv(os.path.join(R, "tables", "te_summary.csv"))
x_hist = pd.read_csv(os.path.join(B, "x_hist.csv"))
x_lam = pd.read_csv(os.path.join(B, "x_lambda.csv"))
x_err = pd.read_csv(os.path.join(B, "x_error.csv"))
x_gap = pd.read_csv(os.path.join(B, "x_gap.csv"))
x_tep = pd.read_csv(os.path.join(B, "x_te_paired.csv"))
x_tec = pd.read_csv(os.path.join(B, "x_te_corr.csv"))
x_f8 = pd.read_csv(os.path.join(B, "x_fig8.csv"), index_col=0)
x_rl = pd.read_csv(os.path.join(B, "x_real_all.csv"))
x_rw = pd.read_csv(os.path.join(B, "x_real_welch.csv"))
d3 = pd.read_csv(os.path.join(R, "tables", "real_dream3_auroc.csv"))
ns = pd.read_csv(os.path.join(R, "tables", "real_netsim_auroc.csv"))
NM = {"rhino": "Rhino", "rhino_g": "Rhino+g", "rhino_s": "Rhino+s", "dynotears": "DYNOTEARS", "varlingam": "VAR-LiNGAM", "pcmci_plus": "PCMCI+"}
ORD = list(NM)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(1.0); sec.top_margin = Inches(0.9); sec.bottom_margin = Inches(0.9)
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.0


def run(p, text, bold=False, italic=False, size=None, sub=False, sup=False):
    r = p.add_run(text); r.bold = bold; r.italic = italic; r.font.name = "Times New Roman"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    if size: r.font.size = Pt(size)
    if sub: r.font.subscript = True
    if sup: r.font.superscript = True
    return r


def rich(p, text, size=None):
    """**bold** and _italic_ markers."""
    import re
    for tok in re.split(r"(\*\*.+?\*\*|__.+?__)", text):
        if tok.startswith("**"): run(p, tok[2:-2], bold=True, size=size)
        elif tok.startswith("__"): run(p, tok[2:-2], italic=True, size=size)
        else: run(p, tok, size=size)


def para(text, align="j", after=6, size=None, keep=False):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(after)
    p.alignment = {"j": WD_ALIGN_PARAGRAPH.JUSTIFY, "c": WD_ALIGN_PARAGRAPH.CENTER, "l": WD_ALIGN_PARAGRAPH.LEFT}[align]
    if keep: p.paragraph_format.keep_with_next = True
    rich(p, text, size); return p


def h1(text):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(12); p.paragraph_format.space_after = Pt(5); p.paragraph_format.keep_with_next = True
    run(p, text, bold=True, size=14)


def h2(text):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(3); p.paragraph_format.keep_with_next = True
    run(p, text, bold=True, size=11.5)


def bullets(items):
    for it in items:
        p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.first_line_indent = Inches(-0.2)
        p.paragraph_format.space_after = Pt(3); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run(p, "\u2022  "); rich(p, it)


def shade(cell, color):
    tcPr = cell._element.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcPr.append(s)


def borders(tbl):
    tblPr = tbl._element.tblPr; b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        x = OxmlElement(f"w:{e}"); x.set(qn("w:val"), "single"); x.set(qn("w:sz"), "4"); x.set(qn("w:space"), "0"); x.set(qn("w:color"), "444444"); b.append(x)
    tblPr.append(b)


def table(caption, header, rows, widths, size=8.5, bold_first=False, note=None):
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_after = Pt(3); c.paragraph_format.keep_with_next = True
    run(c, caption, size=10)
    t = doc.add_table(rows=1, cols=len(header)); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False; borders(t)
    for i, htxt in enumerate(header):
        cell = t.rows[0].cells[i]; cell.width = Inches(widths[i]); shade(cell, "EDEDED")
        p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(0); run(p, htxt, bold=True, size=size)
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].width = Inches(widths[i]); p = cells[i].paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            run(p, str(v), bold=(bold_first and i == 0), size=size)
    # keep rows together with the table where possible
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)
    sp = doc.add_paragraph(); sp.paragraph_format.space_after = Pt(2)
    if note:
        n = doc.add_paragraph(); n.paragraph_format.space_after = Pt(6); run(n, note, size=9, italic=False)
    return t


def figure(fname, caption, width=6.5):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(os.path.join(FIG, fname), width=Inches(width))
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_after = Pt(8)
    run(c, caption, size=10)


def eq(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(6)
    for it in items:
        if isinstance(it, str): run(p, it)
        else: run(p, it[0], sub=(it[1] == "sub"), sup=(it[1] == "sup"))
    return p


def pv(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def pe(p):
    return "below 0.001" if p < 0.001 else f"= {p:.3f}"


def f2(x): return f"{x:.2f}"
def f3(x): return f"{x:.3f}"


# footer page number
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run(); r.font.name = "Times New Roman"; r.font.size = Pt(10)
for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if tag:
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag); r._r.append(e)
    else:
        e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)


def S(dim, meth, metric, col="mean"):
    return sm[(sm.dim == dim) & (sm.method == meth) & (sm.metric == metric)].iloc[0][col]


def PR(dim, other, metric="F1_temporal"):
    return pr[(pr.dim == dim) & (pr.other == other) & (pr.metric == metric)].iloc[0]


def RTm(dim, meth): return rt[(rt.dim == dim) & (rt.method == meth)].iloc[0]


# ------------------------------------------------------------------ title block
p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0); run(p, "Milestone 3 Report", bold=True, size=11)
p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
run(p, "Studying Rhino: Results, Comparison with Baselines and What Could Be Reproduced", bold=True, size=19)
for line in ("CSE 516 - Probabilistic Graphical Models, Monsoon Semester 2026",
             "Group: g12_th_conditional-ind-graphs_ind   |   Track: Theoretical AI (Individual)",
             "Student: Het Patel, AU2440266"):
    q = doc.add_paragraph(); q.paragraph_format.space_after = Pt(0); run(q, line, size=11)
doc.add_paragraph().paragraph_format.space_after = Pt(2)

# ------------------------------------------------------------------ 1
h1("1. Problem Statement and Research Question")
para("The problem is temporal causal discovery. I observe D variables over time. I want to know which variable causes which, at which time lag, "
     "and whether a cause acts inside the same time step. The second case is called an instantaneous effect. The base paper is Rhino [1]. "
     "It learns a graph over the variables and their lags. It also models the noise so that it can change with the past values of the variables. "
     "This is called history-dependent noise.")
para("Rhino assumes that the causal structure does not change over time and that no hidden common causes exist. It also assumes that the model is minimal "
     "and that the joint density is well defined [1, Appendix B]. The graph of the current time step must be acyclic. These assumptions hold in every experiment of this report.")
para("The research question of the project is this:", keep=True)
para("__When does Rhino recover the temporal causal graph better than other methods, and which of its parts explain the gain? "
     "The parts are the instantaneous effects, the history-dependent noise, the model lag and the training length.__", after=6)
para("I state four hypotheses from the claims of the paper [1]. H1: Rhino is better than the baselines when the noise is history-dependent. "
     "H2: it has no clear advantage when the noise is not history-dependent. H3: removing the instantaneous effects hurts when the data contain them. "
     "H4: a model lag below the true lag hurts, and a model lag above it does not.")
para("M3 asks what the evidence says. I ran the experiments of the paper with the authors' released code. All methods saw exactly the same data. "
     "I added paired tests, a precision and recall analysis, and a study of treatment effect error. M1 gave the problem and the review of existing work. "
     "M2 gave the model and the setup. This report restates only what M3 needs, so it can be read alone.")

# ------------------------------------------------------------------ 2
h1("2. Existing Work and SOTA Anchor (Revisited)")
para("The methods near Rhino differ in what they can model. Table 1 shows this, as described in the paper [1, Section 5 and Appendix C]. A survey of time series methods is in [12].")
table("Table 1. What each method can model",
      ["Method", "Type", "Nonlinear", "Instantaneous", "History-dependent noise"],
      [["VAR-LiNGAM [2]", "Linear VAR, non-Gaussian noise", "No", "Yes", "No"],
       ["DYNOTEARS [3]", "Linear VAR, continuous DAG penalty", "No", "Yes", "No"],
       ["PCMCI+ [4]", "Constraint-based, conditional independence tests", "Depends on the test (partial correlation here)", "Yes, up to an equivalence class", "Not modelled"],
       ["cMLP, cLSTM [6], TCDF [7], SRU, eSRU [5]", "Granger causality with neural networks", "Yes", "No", "No"],
       ["Rhino [1]", "Neural VAR with a conditional spline flow", "Yes", "Yes", "Yes"]],
      [1.55, 1.85, 1.2, 1.0, 0.9])
para("The base paper compares Rhino with exactly these methods. I keep them as my SOTA anchor. On synthetic data the strongest comparator in the paper is PCMCI+. "
     "On real data it is the family of nonlinear Granger methods. I did not survey work that appeared after the paper. This is a limit of this report. "
     "I revise the position in Section 10.")

# ------------------------------------------------------------------ 3
h1("3. The Model: Representation, Learning and Inference")
h2("3.1 Representation")
para("Rhino is a structural equation model over time. The value of variable i at time t is")
eq(["X", ("i,t", "sub"), " = f", ("i", "sub"), "( Pa", ("i", "sub"), "(<t), Pa", ("i", "sub"), "(t) ) + g", ("i", "sub"), "( Pa", ("i", "sub"), "(<t), \u03b5", ("i,t", "sub"), " )"])
para("The sets Pa(<t) and Pa(t) are the lagged and the instantaneous parents of variable i given by the graph G. The function f is a neural network. "
     "The function g is a conditional spline flow that transforms the noise \u03b5. It depends only on the lagged parents. So the noise can grow or shrink with the history. "
     "The graph is stored as a tensor of shape [lag + 1, D, D]. Slice 0 holds the instantaneous edges and slice \u03c4 holds the edges from t \u2212 \u03c4 to t [1, Section 3].")
para("I use four versions of the model. **Rhino** has the conditional spline noise. **Rhino+g** has Gaussian noise that does not depend on history. "
     "**Rhino+s** has a spline noise that does not depend on history. **Rhino+NoInst** is Rhino with the instantaneous effects switched off. "
     "These are the variants of the paper, so each one tests a single idea.")
h2("3.2 Learning")
para("Rhino learns a distribution over graphs and not one graph. The distribution q(G) is a product of independent Bernoulli variables. "
     "The parameters are found by maximising the evidence lower bound (ELBO):")
eq(["ELBO = E", ("q(G)", "sub"), "[ \u03a3", ("n", "sub"), " log p", ("\u03b8", "sub"), "( X", ("(n)", "sup"), " | G ) + log p(G) ] + H( q(G) )"])
para("The prior p(G) rewards sparse graphs and penalises cycles in the instantaneous part. The cycle penalty is h(G\u2080) = tr(exp(G\u2080 \u2218 G\u2080)) \u2212 D, which is zero only for a DAG [11]. "
     "Its weight grows during training in steps of an augmented Lagrangian method. The graph samples use the Gumbel-softmax estimator [1, Section 3.2]. "
     "The number of these steps is the training length. It matters in Section 7.")
h2("3.3 Inference")
para("After training I read the graph from q(G). Two readouts are used. The edge probabilities give a ranking of all possible edges, which is scored by AUROC. "
     "Rounding at 0.5 gives one graph, which is scored by F1 and SHD. Treatment effects come from simulation. The model is rolled forward with the incoming edges of the treated variable removed, "
     "once for each graph sample. The mean over graph samples is called E[ATE]. The same simulation with the single most likely graph is called ML ATE [1, Appendix D]. This follows the design of DECI, the static model on which Rhino builds [10]. "
     "The paper proves that the graph is identifiable under conditions on f and g [1, Theorem 1]. I did not re-prove it. My experiments test what happens in practice.")

# ------------------------------------------------------------------ 4
h1("4. Experimental Design")
table("Table 2. Experiments of the paper and what I ran",
      ["Paper element", "What I ran", "Status"],
      [["Synthetic data, Fig 1, 3, 4, 5", "120 datasets of 5, 10 and 20 nodes, six methods", "Done. 40 nodes not run."],
       ["Lag ablation, Table 1", "Lag 1, 2 and 3 on the same 120 datasets", "Done (one cell has 39 of 40)"],
       ["Treatment effect, Fig 2", "360 trained models (three variants on 120 datasets)", "Done"],
       ["DREAM3, Tables 2, 6, 7", "Five networks, size 100, AUROC", "Partial. See Section 7."],
       ["Netsim, Tables 3, 8, Fig 8", "Sim-3, five runs per setting", "Done"]],
      [2.1, 3.2, 1.2])
h2("Data")
para("**Synthetic data.** I use the authors' generator [15]. A dataset is defined by the number of nodes (5, 10, 20), the graph family (Erd\u0151s-R\u00e9nyi or scale-free), "
     "instantaneous effects on or off, history-dependent noise on or off, and the data seed (0 to 4). This gives 40 datasets per dimension and 120 in total. "
     "Datasets with instantaneous effects have 4N instantaneous and 2N lagged edges. Datasets without them have 2N lagged edges. Each dataset has 50 training series of 200 steps with 50 burn-in steps. "
     "The functions are random MLPs. The true lag is 2.")
para("**Real data.** DREAM3 in silico size 100 has five gene networks. Each has 46 trajectories of 21 time points and 100 genes [8, 9]. "
     "Netsim Sim-3 has 15 brain regions and 200 time steps per subject. I train on subjects 2 to 6 and validate on subjects 7 and 8, as in the paper [1, Appendix G.4]. "
     "The preprocessing steps and checksums are in Data/README.md.")
h2("Methods and settings")
table("Table 3. Methods compared",
      ["Method", "Settings", "Runs per dataset"],
      [["Rhino, Rhino+g, Rhino+s", "Authors' code (causica v0.0.0), lag 2, sparsity weight 9 (Rhino, Rhino+s) and 5 (Rhino+g) as in the paper, CPU", "1 model seed per dataset"],
       ["DYNOTEARS [3]", "Authors' wrapper, lag 2, default settings of the released code", "1 (deterministic)"],
       ["VAR-LiNGAM [2]", "Lag 2, default settings with pruning", "1 (deterministic)"],
       ["PCMCI+ [4]", "Lag 2, partial correlation test, significance level 0.05, all DAGs of the equivalence class enumerated", "1"],
       ["cMLP, cLSTM, TCDF, SRU, eSRU", "Numbers quoted by the paper from [5]. Not re-run.", "Not applicable"]],
      [1.7, 3.8, 1.2])
h2("KPIs")
table("Table 4. KPIs",
      ["Layer", "KPI", "How it is computed"],
      [["Graph", "Orientation F1 (instantaneous, lagged, temporal)", "Edge with the correct direction and lag counts as correct. Rounded at 0.5."],
       ["Graph", "Adjacency F1, precision, recall, number of predicted edges", "Direction is ignored for adjacency F1."],
       ["Graph", "SHD", "As computed by the released code."],
       ["Graph", "AUROC of the summary graph", "Edge probabilities, max over lags (real data)."],
       ["Fit", "Training log-likelihood per sample", "Last logged value of each run. It is not a held-out value."],
       ["Inference", "RMSE of the average treatment effect", "E[ATE] and ML ATE against 5000 true intervention samples."],
       ["Cost", "Wall time per job", "Minutes on one CPU worker with 2 threads."]],
      [0.9, 2.4, 3.3])
h2("Statistics and seeds")
para("Every method is run on every dataset, so comparisons are paired. I report the mean and standard deviation over datasets. "
     "The 95 % interval is the t interval. For a difference between two methods I report the mean of the paired differences with a bootstrap interval of 10000 resamples. "
     "The test is the Wilcoxon signed-rank test [14] with the Holm correction [13] inside each dimension and metric. "
     "For the real data I average five runs with different model seeds and report the standard error, as the paper does. I use the Welch test for differences. "
     "The synthetic data seeds are 0 to 4. Each dataset has one model seed. So the spread in the tables is the spread over datasets and not over model seeds.")
para("Runs were made on Windows 11 with Python 3.9 and CPU only. The torch version of the authors' code (1.12.1) has no kernels for the new GPU of the workstation. "
     "Up to 16 workers ran in parallel with 2 threads each. A job had a time limit of 10 hours.")

# ------------------------------------------------------------------ 5
h1("5. Results on Synthetic Data")
h2("5.1 Rhino against the baselines")
rows = []
for m in ORD:
    rows.append([NM[m]] + [f"{S(d, m, 'F1_temporal'):.3f} \u00b1 {S(d, m, 'F1_temporal', 'sd'):.3f}" for d in (5, 10, 20)])
table("Table 5. Temporal orientation F1, mean \u00b1 standard deviation over 40 datasets per dimension", ["Method", "5 nodes", "10 nodes", "20 nodes"], rows,
      [1.8, 1.55, 1.55, 1.55], size=9, bold_first=True)
figure("fig1_main.png", "Fig. 1: Orientation F1 of the instantaneous part, the lagged part and the whole temporal graph. Bars are means over datasets with the 95 % interval. "
       "The instantaneous part uses the 20 datasets per dimension that have instantaneous effects.")
rows = []
for d in (5, 10, 20):
    for m in ("pcmci_plus", "rhino_g", "dynotears", "rhino_s", "varlingam"):
        r = PR(d, m)
        rows.append([f"{d}", NM[m], f"{r.mean_diff:+.3f} [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]", f"{int(r.wins)} / {int(r.losses)}", pv(r.p_holm)])
table("Table 6. Paired difference in temporal F1, Rhino minus the other method, with the 95 % t interval (all datasets of a dimension)",
      ["Nodes", "Other method", "Mean difference [95 % interval]", "Wins / losses", "p (Holm)"], rows, [0.6, 1.4, 2.5, 1.0, 1.0], size=8.5)
pc20 = PR(20, "pcmci_plus")
para(f"**What happened.** Rhino has the highest mean temporal F1 at every dimension (Table 5). It beats DYNOTEARS, VAR-LiNGAM, Rhino+g and Rhino+s on the same datasets at 5 and 10 nodes "
     f"with Holm p below 0.01 (Table 6). It beats PCMCI+ at 5 and 10 nodes by {PR(5,'pcmci_plus').mean_diff:.2f} and {PR(10,'pcmci_plus').mean_diff:.2f}. "
     f"At 20 nodes the gain over PCMCI+ is {pc20.mean_diff:.2f} with a bootstrap interval of 0.001 to 0.103. Rhino wins on 20 datasets and loses on 20. The Holm p value is {pv(pc20.p_holm)}. "
     "I cannot call this a difference. VAR-LiNGAM is close to zero everywhere. The instantaneous part is the hardest. Rhino reaches about 0.25 and the three baselines stay near 0.1 or below.")
para("**Was it expected.** The paper reports the same order and says that Rhino is best or competitive, especially in low dimensions [1, Section 6.1]. "
     "My result agrees with that wording. The paper does not say that the gain shrinks with the dimension. In my data it does. All methods lose F1 as the dimension grows, "
     "but Rhino loses most in absolute terms (0.67 to 0.44) and the spread over datasets grows (standard deviation 0.14 to 0.19). "
     "A larger graph gives the model more to fit with the same number of series, and the variance of the training result grows with it.")
para("**Limit.** Differences of this size depend on the data generator. A different mix of graph types or noise would change them. "
     "I did not run 40 nodes. So I cannot say whether the gain over PCMCI+ stays at zero, shrinks further or reverses.")

h2("5.2 Accuracy and cost")
rows = []
for m in ORD:
    rows.append([NM[m]] + [(f"{RTm(d, m)['median']:.1f}" if RTm(d, m)['median'] >= 10 else f"{RTm(d, m)['median']:.2f}") for d in (5, 10, 20)])
table("Table 7. Median wall time per dataset in minutes (one worker, 2 threads)", ["Method", "5 nodes", "10 nodes", "20 nodes"], rows, [1.8, 1.55, 1.55, 1.55], size=9, bold_first=True)
figure("fig3_tradeoff.png", "Fig. 2: Accuracy against cost. Each marker is one method at one dimension. The horizontal axis is logarithmic. "
       "PCMCI+, DYNOTEARS and VAR-LiNGAM are about 100 to 200 times cheaper than Rhino.", width=4.9)
para(f"The three Rhino variants take {min(RTm(5,v)['median'] for v in ('rhino','rhino_g','rhino_s')):.0f} to {max(RTm(5,v)['median'] for v in ('rhino','rhino_g','rhino_s')):.0f} minutes per dataset at 5 nodes and "
     f"{min(RTm(20,v)['median'] for v in ('rhino','rhino_g','rhino_s')):.0f} to {max(RTm(20,v)['median'] for v in ('rhino','rhino_g','rhino_s')):.0f} minutes at 20 nodes. The baselines need about one minute or less. "
     "So Rhino buys its gain at 5 and 10 nodes with a cost of two orders of magnitude. At 20 nodes it buys nothing measurable over PCMCI+ in F1, and PCMCI+ is cheaper by a factor of about 170. "
     "This is the clearest answer to the question of when a flexible model is worth its cost. It is worth it when the data have history-dependent noise (Section 5.3). "
     f"PCMCI+ has a long tail. Its slowest job at 20 nodes took {RTm(20,'pcmci_plus')['max']:.0f} minutes. This matches the paper's remark that PCMCI+ becomes expensive in high dimensions.")

h2("5.3 Ablations: history-dependent noise, instantaneous effects and graph type")
figure("fig2_factors.png", "Fig. 3: Temporal orientation F1 split by history-dependent noise (a) and by instantaneous effects (b). Means over 20 datasets per bar with the 95 % interval.")
rows = []
for d in (5, 10, 20):
    for h in (1, 0):
        for m in ("rhino_g", "pcmci_plus"):
            r = x_hist[(x_hist.dim == d) & (x_hist["hist"] == h) & (x_hist.comparison == f"Rhino minus {m}")].iloc[0]
            rows.append([f"{d}", "yes" if h else "no", NM[m], f"{r.mean_diff:+.3f} [{r.boot_lo:+.3f}, {r.boot_hi:+.3f}]", f"{int(r.wins)} / {int(r.losses)}", pv(r.p_holm)])
table("Table 8. Rhino minus Rhino+g and PCMCI+ in temporal F1, split by history-dependent noise (20 datasets each)",
      ["Nodes", "History-dep. noise", "Other method", "Mean difference [95 % interval]", "Wins / losses", "p (Holm)"], rows, [0.55, 1.0, 1.1, 2.3, 0.9, 0.8], size=8.5)
para("**What happened.** With history-dependent noise Rhino is better than Rhino+g by 0.26, 0.18 and 0.21 at 5, 10 and 20 nodes and better than PCMCI+ by 0.23, 0.18 and 0.20. All six Holm p values are below 0.001 (Table 8). "
     "Without history-dependent noise the picture changes. At 5 and 10 nodes Rhino and Rhino+g are equal (difference 0.006 and \u22120.001). Rhino is 0.098 below PCMCI+ at 20 nodes. It loses on all 20 datasets (Holm p below 0.001). "
     "Rhino is also 0.071 below Rhino+g at 20 nodes, but this difference is not significant after correction (p = 0.13).")
para("**Reading.** This supports H1 and H2. The gain of Rhino comes from the history-dependent noise and from nothing else. When the data do not have it, Rhino+g fits as well at small size and PCMCI+ is better at 20 nodes. "
     "The reason is probably the cost of flexibility. Without history dependence the conditional flow adds parameters that the data cannot constrain. I did not test this reason. "
     "It follows from the pattern but I have no experiment that isolates it.")
para("**Instantaneous effects.** All the main methods score lower on data with instantaneous effects (Fig. 3b). The drop is 0.06 to 0.17 in temporal F1. The paper calls all methods robust to this setting [1, Appendix F.3]. "
     "In my data the drop is clear but Rhino stays the best or close to the best. Rhino has the higher mean than Rhino+g and PCMCI+ in all six cases. "
     "After Holm correction over these twelve comparisons only three are significant. They are both methods at 5 nodes with instantaneous effects (p = 0.001) and Rhino+g at 10 nodes without them (p = 0.023). "
     "The sample is only 20 datasets for each bar. The instantaneous F1 itself is low for every method (Fig. 1). "
     "So H3 is only partly tested here. I did not run Rhino+NoInst on synthetic data. I did run it on Netsim (Section 7).")
para("**Graph type.** Rhino, Rhino+s, PCMCI+ and VAR-LiNGAM do better on Erd\u0151s-R\u00e9nyi graphs than on scale-free graphs at every dimension. For example at 20 nodes Rhino gets 0.515 on ER and 0.364 on SF, and PCMCI+ gets 0.474 and 0.302. "
     "DYNOTEARS does better on SF at 10 and 20 nodes (0.204 on ER and 0.409 on SF at 20 nodes). Rhino+g does so too (0.328 and 0.408 at 20 nodes). "
     "The paper reports DYNOTEARS as the only exception [1, Appendix F.3]. So I reproduce the rule with one more exception. The numbers are in Results/tables/synth_factors_orientation.csv.")

h2("5.4 Lag ablation (Table 1 of the paper)")
rows = []
paper_t = {(5, 1): ("0.34 \u00b1 0.12", "\u22124.14 \u00b1 1.63"), (5, 2): ("0.59 \u00b1 0.20", "\u22123.83 \u00b1 1.62"), (5, 3): ("0.56 \u00b1 0.22", "\u22123.75 \u00b1 1.64"),
           (10, 1): ("0.28 \u00b1 0.11", "\u22127.97 \u00b1 2.09"), (10, 2): ("0.49 \u00b1 0.18", "\u22127.21 \u00b1 2.22"), (10, 3): ("0.45 \u00b1 0.20", "\u22127.01 \u00b1 1.91"),
           (20, 1): ("0.25 \u00b1 0.13", "\u221215.62 \u00b1 3.16"), (20, 2): ("0.39 \u00b1 0.22", "\u221214.70 \u00b1 2.87"), (20, 3): ("0.37 \u00b1 0.21", "\u221214.72 \u00b1 2.82")}
for _, r in t1.iterrows():
    lag = int(str(r["lag"]).split("=")[1]); pt = paper_t[(int(r["dim"]), lag)]
    rows.append([f"{int(r['dim'])}", f"{lag}", str(r["F1_temporal"]).replace("+-", "\u00b1"), pt[0], str(r["LL"]).replace("+-", "\u00b1").replace("-", "\u2212"), pt[1]])
table("Table 9. Lag ablation. Temporal F1 and training log-likelihood, this run against the paper (mean \u00b1 standard deviation)",
      ["Nodes", "Model lag", "F1, this run", "F1, paper", "Log-lik., this run", "Log-lik., paper"], rows, [0.6, 0.8, 1.35, 1.2, 1.5, 1.35], size=8.5)
figure("fig4_lag.png", "Fig. 4: Lag ablation. Means over 39 to 40 datasets with the 95 % interval. The true lag is 2. The log-likelihood is a training value.", width=5.9)
lp = t1p
g = lambda d, c: lp[(lp.dim == d) & (lp.comparison == c)]
para("**What happened.** A model lag of 2 gives the best F1 at every dimension (Table 9). Lag 1 is worse by 0.25, 0.19 and 0.15 (Holm p below 0.001). Lag 3 is worse than lag 2 by 0.08, 0.06 and 0.05 (also p below 0.001). "
     "The training log-likelihood rises from lag 1 to lag 2 at every dimension (paired difference 0.42, 0.69 and 1.02, p below 0.001). From lag 2 to lag 3 it changes by less than the spread, "
     "except at 5 nodes where it rises by 0.14 (Holm p = 0.026).")
para("**Reading.** This supports H4 for lag 1 and shows that lag 3 is not free. The paper concludes that Rhino is robust to a longer lag. "
     "I see the same shape but with a measurable cost of 0.05 to 0.08 F1. The extra lag adds possible edges and the F1 drops while the likelihood does not improve. "
     "The absolute values are 0.05 to 0.08 higher than the paper for lag 2. My datasets are not the same as the paper's, because the grid of the paper is not fully specified (Section 11). "
     "So I compare the pattern and not the absolute numbers. The log-likelihood is a training value, so it cannot show overfitting.")
h2("5.5 Sparsity weight")
l5 = x_lam[x_lam.dim == 5].iloc[0]; l10 = x_lam[x_lam.dim == 10].iloc[0]
para(f"The paper uses a sparsity weight of 9 for Rhino. The released config has 5. I ran both at 5 and 10 nodes (40 datasets each). The paired difference in temporal F1 is {l5.mean_diff:+.3f} at 5 nodes "
     f"(bootstrap interval [{l5.boot_lo:+.3f}, {l5.boot_hi:+.3f}], p = {l5.p:.2f}) and {l10.mean_diff:+.3f} at 10 nodes ([{l10.boot_lo:+.3f}, {l10.boot_hi:+.3f}], p = {l10.p:.2f}). "
     "So the choice between 9 and 5 does not matter in this range. The open point between the paper and the code has no effect on my conclusions.")

h2("5.6 Error analysis: what kind of mistakes")
rows = []
for d in (5, 10, 20):
    for m in ORD:
        r = x_err[(x_err.dim == d) & (x_err.method == m)].iloc[0]
        gp = x_gap[x_gap.dim == d].iloc[0][m]
        rows.append([f"{d}", NM[m], f"{r.prec:.2f}", f"{r.rec:.2f}", f"{r.ratio:.2f}", f"{gp:.3f}"])
table("Table 10. Oriented precision, oriented recall, predicted edges relative to true edges and the gap between adjacency F1 and orientation F1",
      ["Nodes", "Method", "Precision", "Recall", "Predicted / true edges", "Adjacency F1 minus orientation F1"], rows, [0.6, 1.3, 0.9, 0.9, 1.4, 1.5], size=8.5)
figure("fig5_pr.png", "Fig. 5: Precision against recall of oriented edges in the temporal graph. Marker size grows with the dimension (5, 10, 20).", width=4.8)
para("**What happened.** The methods fail in different ways. PCMCI+ has the highest precision (0.89, 0.80, 0.69) and the lowest recall among the useful methods (0.40, 0.36, 0.30). It predicts too few edges at 5 and 10 nodes. "
     "DYNOTEARS predicts two to six times too many edges and has precision between 0.28 and 0.41. VAR-LiNGAM predicts almost no edges (recall 0.02). "
     "Rhino sits in between. It predicts about the right number of edges at 5 nodes (ratio 1.04) and too many at 20 nodes (ratio 1.55). Rhino+g predicts too many at 10 and 20 nodes (1.64 and 2.88). "
     "Rhino+s predicts too few (0.40 to 0.71) and so has low recall.")
para("Rhino rarely finds a pair of variables and gets the direction wrong. The gap between adjacency F1 and orientation F1 is 0.002 to 0.007 for Rhino and 0.065 to 0.098 for DYNOTEARS. "
     "So the main mistakes of Rhino are missing edges and, at larger size, extra edges, and not wrong directions. "
     "Rhino+s is the weakest variant and does worse than Rhino+g. The paper finds Rhino+s close to Rhino. I do not reproduce this (Section 9). I did not test the reason. "
     "One possible reason is that a spline noise with no history dependence is hard to fit and the model then keeps too few edges. The low edge count is consistent with that, but it is not a test.")
para("**Failure case of Rhino.** The clearest failure is data without history-dependent noise at 20 nodes. There Rhino is below PCMCI+ on every one of the 20 datasets. "
     "A user who does not know whether the noise depends on the history should run Rhino+g or PCMCI+ as well.")

# ------------------------------------------------------------------ 6
h1("6. Treatment Effect Estimation")
rows = []
for d in (5, 10, 20):
    for m in ("rhino", "rhino_g", "rhino_s"):
        r = te[(te.dim == d) & (te.method == m) & (te.estimator == "E[ATE]")].iloc[0]
        r2 = te[(te.dim == d) & (te.method == m) & (te.estimator == "ML ATE")].iloc[0]
        rows.append([f"{d}", NM[m], f"{r.mean_rmse:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}]", f"{r['median']:.3f}", f"{r2.mean_rmse:.3f}", f"{RTm(d, m)['median']:.0f}"])
table("Table 11. RMSE of the average treatment effect over 40 datasets (lower is better)",
      ["Nodes", "Method", "E[ATE], mean [95 % interval]", "E[ATE], median", "ML ATE, mean", "Median time (min)"], rows, [0.6, 1.0, 2.1, 1.0, 1.0, 1.0], size=8.5)
figure("fig6_te.png", "Fig. 6: (a) RMSE of the average treatment effect by method. (b) The same error, normalised, against the temporal F1 of the same model. Each point is one trained model.")
tp = lambda d, c: x_tep[(x_tep.dim == d) & (x_tep.comparison == c)].iloc[0]
a20 = tp(20, "rhino minus rhino_g (ATE RMSE)"); b20 = tp(20, "rhino_g minus rhino_s (ATE RMSE)")
cp = x_tec[(x_tec.method == "all") & (x_tec.dim == "all") & (x_tec.target == "ATE_RMSE") & (x_tec.strata == "none")].iloc[0]
cs = x_tec[(x_tec.method == "all") & (x_tec.dim == "all") & (x_tec.target == "ATE_RMSE") & (x_tec.strata != "none")].iloc[0]
para("**What happened.** Rhino+s has the lowest mean error at every dimension (0.567, 0.523 and 0.338), although it has the worst graph F1. "
     f"The paired tests are weak at 5 and 10 nodes. All Holm p values there are above 0.06. At 20 nodes the error of Rhino is {abs(a20.mean_diff):.2f} lower than that of Rhino+g (p = {pv(a20.p_holm)}) "
     f"and the error of Rhino+s is {abs(b20.mean_diff):.2f} lower than that of Rhino+g (p below 0.001). E[ATE] and ML ATE agree within 0.02 in every row, which suggests that the posterior over graphs is concentrated.")
para(f"**Is the treatment effect linked to graph quality.** Over all 360 models the Spearman correlation between F1 and the error is {cp.spearman:+.2f}. It is positive, so a better graph goes with a larger error. "
     f"This comes mainly from the type of data. Datasets with history-dependent noise give both higher F1 and larger effects. Inside groups of equal method, dimension, history dependence and instantaneous setting, the correlation falls to {cs.spearman:+.2f}. "
     "So I find no sign that a better graph gives a better treatment effect. The paper makes the same remark and calls it a question for further study [1, Appendix D]. "
     "I only confirm it. I do not explain it. A possible reason is that the effect depends on the few paths between the treated and the target variable and not on the whole graph.")

# ------------------------------------------------------------------ 7
h1("7. Results on Real Data")
h2("7.1 DREAM3")
dd = {}
for net in ("ecoli1", "ecoli2", "yeast1", "yeast2", "yeast3"):
    for meth in ("DYNOTEARS", "PCMCI+", "Rhino+g", "Rhino"):
        dd[(net, meth)] = d3[(d3.network == net) & (d3.method == meth)].iloc[0]
rows = []
for meth in ("cMLP", "cLSTM", "TCDF", "SRU", "eSRU", "DYNOTEARS", "PCMCI+", "Rhino+g", "Rhino"):
    row = [meth]
    for net in ("ecoli1", "ecoli2", "yeast1", "yeast2", "yeast3"):
        r = d3[(d3.network == net) & (d3.method == meth)].iloc[0]
        if str(r["variant"]).startswith("quoted") or meth in ("DYNOTEARS", "PCMCI+"):
            row.append(f"{r['mean']:.3f}")
        else:
            row.append(f"{r['mean']:.3f} \u00b1 {r['se']:.3f} (n={int(r['n'])}) [{r.paper_value:.3f}]")
    rows.append(row)
table("Table 12. DREAM3 AUROC of the summary graph. This run, mean \u00b1 standard error over runs (n), paper value in brackets",
      ["Method", "E. coli 1", "E. coli 2", "Yeast 1", "Yeast 2", "Yeast 3"], rows, [0.95, 1.1, 1.1, 1.1, 1.1, 1.1], size=7.5, bold_first=True,
      note="cMLP, cLSTM, TCDF, SRU and eSRU are single-run numbers that the paper quotes from [5]. DYNOTEARS and PCMCI+ are single runs. Rhino and Rhino+g use the hyperparameters printed in the paper.")
figure("fig7_dream3.png", "Fig. 7: DREAM3 AUROC. Coloured dots are this run with the 95 % interval, diamonds are the paper's values and grey squares are numbers quoted by the paper.", width=6.6)
para("**What happened.** Rhino and Rhino+g are clearly above DYNOTEARS and PCMCI+ on all five networks. For E. coli 1 the 95 % interval of Rhino (0.630 to 0.683) does not reach the values of DYNOTEARS (0.569) or PCMCI+ (0.540). "
     "Against the quoted Granger methods the picture is mixed. Rhino ties SRU and eSRU on E. coli 1 (0.657 against 0.657 and 0.660). It is slightly below SRU on E. coli 2 (0.656 against 0.666). "
     "It is above the best Granger method on Yeast 1 (0.634 against 0.627). On Yeast 2 and Yeast 3 Rhino+g is the best method (0.585 against 0.575, and 0.565 against 0.557) and Rhino itself is below them. "
     "These gaps are 0.003 to 0.010. The quoted numbers have no interval. So I cannot call any of these gaps real.")
para("**Against the paper.** On the networks with five runs my values are 0.01 to 0.03 below the paper's for both Rhino and Rhino+g (for example Rhino on E. coli 1: 0.657 against 0.685, with standard error 0.010 against 0.003). "
     "So I do not reproduce the printed numbers. I reproduce the ranking of the baselines and the pattern between Rhino and Rhino+g. "
     "Rhino is better on E. coli 1, E. coli 2 and Yeast 1. Rhino+g is better on Yeast 2 and Yeast 3. The paper has the same split. None of these differences is significant (Welch p between 0.04 and 0.76, and 0.20 or higher after Holm). "
     "I did not find the reason for the gap. Possible reasons are my train and validation split (assumption in Data/README.md), the hyperparameter tuning of the paper which I did not repeat, and different data preprocessing. None is tested.")
para("**Limits.** E. coli 2 and Yeast 2 with Rhino and Yeast 2 with Rhino+g have two runs and not five, because the other runs hit the time limit. The intervals for these cells are very wide (Fig. 7). "
     "The orientation F1 and SHD of the paper (Tables 6 and 7 of [1]) are not reproduced. The paper tunes the rounding threshold for these two metrics. I used the fixed value 0.5. At this threshold Rhino predicts many more edges than the truth "
     "and the values are not comparable. I therefore do not report them as a result. A run of the released configs on DREAM3 did not finish within the time budget.")
h2("7.2 Netsim")
nr = x_rl[(x_rl.task == "netsim")].set_index("variant")
def nrow(label, var, paper_auc, paper_f1, paper_shd):
    r = nr.loc[var]
    return [label, f"{r.auroc:.3f} \u00b1 {r.auroc_se:.3f}" if r.n > 1 else f"{r.auroc:.3f}", paper_auc,
            f"{r.of1:.3f} \u00b1 {r.of1_se:.3f}" if r.n > 1 else f"{r.of1:.3f}", paper_f1,
            f"{r.shd:.1f} \u00b1 {r.shd_se:.1f}" if r.n > 1 else f"{r.shd:.0f}", paper_shd]
rows = [nrow("Rhino, paper steps", "rhino_paper", "0.99 \u00b1 0.001", "0.551 \u00b1 0.048", "13.8 \u00b1 1.5"),
        nrow("Rhino, released config", "rhino_shipped", "0.99 \u00b1 0.001", "0.551 \u00b1 0.048", "13.8 \u00b1 1.5"),
        nrow("Rhino+g, paper steps", "rhino_g_paper", "0.974 \u00b1 0.002", "0.539 \u00b1 0.036", "10.4 \u00b1 1.08"),
        nrow("Rhino+g, released config", "rhino_g_shipped", "0.974 \u00b1 0.002", "0.539 \u00b1 0.036", "10.4 \u00b1 1.08"),
        nrow("Rhino+NoInst, paper steps", "rhino_noinst_paper", "0.93 \u00b1 0.006", "0.212 \u00b1 0.014", "29 \u00b1 1.5"),
        nrow("Rhino+NoInst, released config", "rhino_noinst_shipped", "0.93 \u00b1 0.006", "0.212 \u00b1 0.014", "29 \u00b1 1.5"),
        nrow("DYNOTEARS", "dynotears", "0.90", "0.341", "17"),
        nrow("PCMCI+", "pcmci_plus", "0.83 \u00b1 0", "0.41", "18"),
        nrow("VAR-LiNGAM", "varlingam", "0.84 \u00b1 0", "0.44", "18")]
table("Table 13. Netsim. This run (mean \u00b1 standard error over five runs) next to the paper (Tables 3 and 8)",
      ["Method and setting", "AUROC, this run", "AUROC, paper", "Orient. F1, this run", "Orient. F1, paper", "SHD, this run", "SHD, paper"], rows,
      [1.65, 0.95, 0.85, 0.95, 0.9, 0.8, 0.7], size=7.5, bold_first=True,
      note="Paper steps are the 5 augmented Lagrangian steps printed in the paper. The released config trains for many more steps. The paper gives one value per model in each table and does not say how many steps belong to which table.")
figure("fig8_netsim.png", "Fig. 8: Netsim AUROC of the summary graph. Coloured dots are this run with the 95 % interval, triangles are the released config, diamonds are the paper's values and grey squares are quoted by the paper.", width=5.0)
w = lambda a, b: x_rw[(x_rw.task == "netsim") & (x_rw.a == a) & (x_rw.b == b)].iloc[0]
para("**What happened.** With the settings printed in the paper (5 augmented Lagrangian steps) the AUROC of Rhino is 0.987 (paper 0.990). Rhino+g reaches 0.972 (paper 0.974) and Rhino+NoInst reaches 0.912 (paper 0.93). "
     "All three paper values lie inside my 95 % intervals. The baselines also match the paper: DYNOTEARS 0.896, PCMCI+ 0.830 and VAR-LiNGAM 0.836. This is the best reproduction in my study.")
para(f"**Ablations.** Removing the instantaneous effects costs 0.075 AUROC (Welch p {pe(w('rhino_paper','rhino_noinst_paper').p)}). This supports H3 on real data. Replacing the history-dependent noise by Gaussian noise costs 0.015 "
     f"(p = {w('rhino_paper','rhino_g_paper').p:.3f}, uncorrected). The paper also finds this effect to be small. With five runs per cell I regard the evidence as suggestive and not strong.")
para("**Training length.** With the released config, which trains for many more steps, the AUROC is lower: 0.931, 0.905 and 0.857. The loss against the paper steps is 0.056, 0.066 and 0.055 (Welch p between 0.002 and 0.012). "
     "The F1 and SHD go the other way. The released config gives F1 0.543 and SHD 15.6 for Rhino, which is close to the paper's 0.551 and 13.8. The paper steps give F1 0.287 and SHD 40.7. "
     "So the paper's AUROC (Table 3) and its F1 and SHD (Table 8) match two different training lengths in my runs. The paper does not say this. This is my reading of the numbers. I did not confirm it with the authors.")
para("**Where my numbers differ.** DYNOTEARS reaches F1 0.686 and SHD 6 in my run, but 0.341 and 17 in the paper. VAR-LiNGAM gets 0.296 and 29, against 0.44 and 18. PCMCI+ matches (0.410 and 18). "
     "I did not find the reason for DYNOTEARS. A different threshold for its weighted matrix may be the source, but I did not test it.")
h2("7.3 Training curves and probability quality")
f8 = x_f8.loc["rhino_shipped"]; f8g = x_f8.loc["rhino_g_shipped"]; f8n = x_f8.loc["rhino_noinst_shipped"]
figure("fig9_curves.png", "Fig. 9: Netsim training curves. Mean over five runs of the AUROC (a), the orientation F1 (b) and the validation log-likelihood (c) after each augmented Lagrangian step, with the released configs.")
para(f"**What happened.** For Rhino the AUROC peaks at step {int(f8.auroc_peak_step)} with {f8.auroc_peak:.3f} and then falls to {f8.auroc_final:.3f} at step {int(f8.steps) - 1}. "
     f"The F1 rises from {f8.f1_first:.3f} to {f8.f1_final:.3f}. The validation log-likelihood falls from {f8.ll_first:.1f} to {f8.ll_final:.1f}. Rhino+g and Rhino+NoInst show the same pattern "
     f"(AUROC {f8g.auroc_peak:.3f} to {f8g.auroc_final:.3f}, and {f8n.auroc_peak:.3f} to {f8n.auroc_final:.3f}). The best validation log-likelihood comes at step {int(f8.ll_best_step)} for Rhino.")
para("**Reading.** This is the pattern that the paper reports in its Fig. 8 and explains as overfitting. As training goes on, the edge probabilities move to 0 or 1. "
     "The rounded graph improves because more edges cross 0.5 in the right way. The ranking of the edges gets worse, because wrong edges also receive probabilities close to 1. "
     "The model becomes more confident and not more correct. The validation log-likelihood falls together with the AUROC, so it is a usable signal to stop training. "
     "For Rhino it would have chosen step 1, where the AUROC is 0.980. This is evidence on probability quality, but it is indirect.")
h2("Probability quality: what I did and did not measure")
para("A graph model should state how sure it is. Rhino does this through q(G). I measured three things about it: the AUROC of the edge probabilities, the training log-likelihood (Table 9) "
     "and the validation log-likelihood on Netsim (Fig. 9c). I did **not** measure the Brier score, the expected calibration error or a reliability diagram of the edge probabilities. "
     "The edge probability matrices were not part of the exported results, so I cannot compute them from the data I have. I list this as a gap and plan it for M4 (Section 13). "
     "I also did not report a held-out log-likelihood for the synthetic runs. The values in Table 9 are training values.")

# ------------------------------------------------------------------ 8 scorecard
h1("8. Robustness")
para("I studied robustness along five axes: the dimension (Sections 5.1 and 5.2), the graph type and the data mismatch with the model (Section 5.3), the model lag (Section 5.4), "
     "the sparsity weight (Section 5.5) and the training length (Section 7.2). The results in short are these.")
bullets(["**Dimension.** F1 falls for every method. The gain of Rhino over PCMCI+ falls from 0.12 to 0.05 and stops being significant at 20 nodes. The spread of Rhino grows.",
         "**Mismatch of the data with the model.** Rhino is the best method when the noise is history-dependent. It is not the best when the noise is not history-dependent and the graph is large (Table 8).",
         "**Model lag.** A lag that is too small loses 0.15 to 0.25 F1. A lag that is too large loses 0.05 to 0.08.",
         "**Sparsity weight.** 9 against 5 changes nothing measurable.",
         "**Training length.** It changes AUROC and F1 in opposite directions. The right stopping rule depends on the metric (Section 7.3).",
         "**Not tested.** Sample size (the number of series was fixed at 50), noise level, missing data and the graph density beyond the two families. I did not run these."])

# ------------------------------------------------------------------ 9 scorecard
h1("9. What Was Reproduced and What Was Not")
table("Table 14. Claims of the paper against my evidence",
      ["Claim of the paper", "My evidence", "Status"],
      [["Rhino is best or competitive on synthetic data", "Highest mean F1 at 5, 10, 20 nodes. Significant against PCMCI+ at 5 and 10 nodes only.", "Partly reproduced"],
       ["History-dependent noise helps", "Rhino above Rhino+g by 0.18 to 0.26 with such noise. No gain without it.", "Reproduced"],
       ["Rhino+s is close to Rhino", "Rhino+s is 0.23 to 0.32 below Rhino in paired F1.", "Not reproduced"],
       ["Rhino is robust to a longer lag, a shorter lag hurts (Table 1)", "Same pattern. A longer lag costs 0.05 to 0.08 F1. Absolute values differ.", "Reproduced in shape"],
       ["Most methods do better on ER than SF, DYNOTEARS is the exception", "Same for four methods. DYNOTEARS and also Rhino+g do better on SF at 10 and 20 nodes.", "Mostly reproduced"],
       ["Rhino and Rhino+g beat the other methods on DREAM3 (Table 2)", "Above DYNOTEARS and PCMCI+. About equal to the best Granger method. Values 0.01 to 0.03 below the paper.", "Partly reproduced"],
       ["Netsim AUROC 0.99 for Rhino (Table 3)", "0.987 with the paper steps. Paper value inside my interval.", "Reproduced"],
       ["Instantaneous effects matter on Netsim", "AUROC 0.987 against 0.912 without them.", "Reproduced"],
       ["AUROC and validation likelihood fall while F1 rises (Fig 8)", "Same pattern in three settings.", "Reproduced"],
       ["Treatment effect error is little related to discovery quality (Fig 2)", "No sign of a link. Weak positive correlation inside groups (0.15).", "Consistent"],
       ["DREAM3 orientation F1 and SHD (Tables 6 and 7)", "Not comparable. The paper tunes the threshold.", "Not reproduced"],
       ["Results at 40 nodes, PCMCI+ over one week at 40 nodes", "Not run.", "Not tested"]],
      [2.4, 3.1, 1.0], size=8.5)

# ------------------------------------------------------------------ 10
h1("10. Revised SOTA Position")
para("I follow the loop of the course: identify, understand, compare, validate, reposition.")
bullets(["**Identify.** The anchor is the set of methods in the base paper. The synthetic comparator is PCMCI+. The real-data comparators are the nonlinear Granger methods.",
         "**Understand.** Rhino models nonlinearity, instantaneous effects and history-dependent noise together. Table 1 shows that no other method does all three.",
         "**Compare.** Same data and same conditions for all methods, paired tests, five or more runs on real data.",
         "**Validate.** Most claims hold in shape. Several do not hold in size (DREAM3 values, Rhino+s). The 40-node results are untested.",
         "**Reposition.** The statement below."])
para("Rhino is the strongest of the six methods I ran when the data have history-dependent noise. This holds at 5, 10 and 20 nodes. Over all datasets of 20 nodes its advantage over PCMCI+ in F1 cannot be separated from zero, "
     "and it costs about 170 times more time. When the noise does not depend on history, Rhino has no advantage over its Gaussian variant or over PCMCI+, and PCMCI+ is better at 20 nodes. "
     "On real data it is clearly better than the linear baselines and about level with the best Granger methods. The gaps there are small and the Granger numbers have no interval. "
     "So my position is narrower than the claim of the paper. Rhino helps in a well defined region and it is not a general replacement. "
     "I did not review work after the paper, so I do not claim a position against newer methods.")

# ------------------------------------------------------------------ 11
h1("11. Limits and Open Points")
bullets(["**No 40-node results.** They were too expensive on the available machine. Table 1, Fig 1 and Fig 2 of the paper are therefore only checked up to 20 nodes.",
         "**The synthetic grid is my reading of the paper.** The paper says 160 datasets. The released generator writes 480. I used connection factor 2 and the same graph family for both graphs. I could not check this against the authors.",
         "**One model seed per synthetic dataset.** The intervals show spread over datasets and not over training seeds.",
         "**DREAM3 is incomplete.** Three cells have two runs and not five. The released configs did not finish. Orientation F1 and SHD are not reproduced.",
         "**Quoted baselines.** cMLP, cLSTM, TCDF, SRU and eSRU are not re-run. They have no uncertainty.",
         "**Probability quality.** No calibration measures (Section 7.3).",
         "**Assumptions not stated in the paper.** F1 on synthetic data (I report orientation and adjacency F1, both in the files), the Netsim subject numbering, the DREAM3 split and the Netsim lag. They are listed in Results/STATUS.md.",
         "**Problems in the released code.** The treatment effect flag needs a workaround, and the evaluation of the diagonal needs a flag on Netsim. Both are in Results/STATUS.md. Five early jobs failed because of a race in the logging library. They were run again.",
         "**SHD.** The SHD of the released code is not always equal to the sum of missed and extra edges. I did not trace why. I report it in the files and base my conclusions on F1.",
         "**Newer methods.** I did not survey work after the paper."])

# ------------------------------------------------------------------ 12
h1("12. Revisiting M1 and M2")
bullets(["**Problem and research question.** The research question is fixed in Section 1. M1 and M2 use the same wording.",
         "**Baselines.** The baseline set is DYNOTEARS, VAR-LiNGAM and PCMCI+, with the nonlinear Granger numbers quoted from the paper.",
         "**KPIs.** Orientation F1, adjacency F1, precision, recall, SHD, AUROC, treatment effect RMSE and run time. Calibration is planned for M4.",
         "**Assumptions.** Causal stationarity, causal sufficiency, a graph that is acyclic at time t, and the generator settings of Section 4.",
         "**Setup.** The code of the authors is used without edits. The setup was checked on a small case before the full runs."])

# ------------------------------------------------------------------ 13
h1("13. Reproducibility and Plan for M4")
para("All results come from the scripts in Code/scripts, which write the tables and figures in Results/. Nothing is typed by hand. Code/README.md gives the commands, the environment and the seeds. "
     "Code/environment/pip_freeze.txt lists the exact package versions. Each job has its own result file in Results/raw. Jobs that did not finish are in Results/failed_infra with their logs. "
     "The authors' code is not copied here. It is used at tag v0.0.0 without edits [15]. The extra statistics of this report (paired tests by group, bootstrap intervals, the precision and recall table, "
     "the treatment effect correlations and the Welch tests) are computed from Results/raw by Code/scripts/report_extra_stats.py and Code/scripts/report_real_stats.py.")
table("Table 15. Plan for M4 (may change as I learn more)",
      ["Item", "Planned work"],
      [["Calibration", "Re-run a subset, save the edge probabilities and report Brier score, expected calibration error and reliability diagrams."],
       ["Sample size", "Vary the number of series at 5 and 10 nodes and plot SHD and F1 against the sample size."],
       ["Missing runs", "The two missing DREAM3 seeds per cell, and the 40-node case if the budget allows."],
       ["Robustness", "Noise level and missing values for the best three methods."],
       ["SOTA", "A short check of work after the paper and the final position."]],
      [1.3, 5.2], size=9)

# ------------------------------------------------------------------ refs
h1("References")
refs = [
    "W. Gong, J. Jennings, C. Zhang, and N. Pawlowski, \u201cRhino: Deep Causal Temporal Relationship Learning with History-dependent Noise,\u201d in International Conference on Learning Representations (ICLR), 2023, arXiv:2210.14706.",
    "A. Hyv\u00e4rinen, K. Zhang, S. Shimizu, and P. O. Hoyer, \u201cEstimation of a structural vector autoregression model using non-Gaussianity,\u201d Journal of Machine Learning Research, vol. 11, no. 5, 2010.",
    "R. Pamfil et al., \u201cDYNOTEARS: Structure learning from time-series data,\u201d in International Conference on Artificial Intelligence and Statistics (AISTATS), PMLR, pp. 1595-1605, 2020.",
    "J. Runge, \u201cDiscovering contemporaneous and lagged causal relations in autocorrelated nonlinear time series datasets,\u201d in Conference on Uncertainty in Artificial Intelligence (UAI), PMLR, pp. 1388-1397, 2020.",
    "S. Khanna and V. Y. F. Tan, \u201cEconomy statistical recurrent units for inferring nonlinear Granger causality,\u201d arXiv:1911.09879, 2019.",
    "A. Tank, I. Covert, N. Foti, A. Shojaie, and E. Fox, \u201cNeural Granger causality for nonlinear time series,\u201d stat, vol. 1050, p. 16, 2018.",
    "M. Nauta, D. Bucur, and C. Seifert, \u201cCausal discovery with attention-based convolutional neural networks,\u201d Machine Learning and Knowledge Extraction, vol. 1, no. 1, p. 19, 2019.",
    "R. J. Prill et al., \u201cTowards a rigorous assessment of systems biology models: the DREAM3 challenges,\u201d PLoS ONE, vol. 5, no. 2, e9202, 2010.",
    "D. Marbach, T. Schaffter, C. Mattiussi, and D. Floreano, \u201cGenerating realistic in silico gene networks for performance assessment of reverse engineering methods,\u201d Journal of Computational Biology, vol. 16, no. 2, pp. 229-239, 2009.",
    "T. Geffner et al., \u201cDeep end-to-end causal inference,\u201d arXiv:2202.02195, 2022.",
    "X. Zheng, B. Aragam, P. Ravikumar, and E. P. Xing, \u201cDAGs with NO TEARS: Continuous optimization for structure learning,\u201d in Advances in Neural Information Processing Systems (NeurIPS), vol. 31, 2018.",
    "C. K. Assaad, E. Devijver, and E. Gaussier, \u201cSurvey and evaluation of causal discovery methods for time series,\u201d Journal of Artificial Intelligence Research, vol. 73, pp. 767-819, 2022.",
    "S. Holm, \u201cA simple sequentially rejective multiple test procedure,\u201d Scandinavian Journal of Statistics, vol. 6, no. 2, pp. 65-70, 1979.",
    "F. Wilcoxon, \u201cIndividual comparisons by ranking methods,\u201d Biometrics Bulletin, vol. 1, no. 6, pp. 80-83, 1945.",
    "Microsoft, causica (Rhino code), release v0.0.0, github.com/microsoft/causica/tree/v0.0.0."]
for i, rf in enumerate(refs, 1):
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.35); p.paragraph_format.first_line_indent = Inches(-0.35); p.paragraph_format.space_after = Pt(3)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; run(p, f"[{i}] {rf}", size=10)

doc.save(DOCX)
print("saved", DOCX)
