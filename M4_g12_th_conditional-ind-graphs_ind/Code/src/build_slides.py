"""Builds the M4 slide deck (pptx, native shapes) and the separate speaker notes (docx), in the format of the M1 slides:
maroon title slide with the university logo, white content slides, one bold lead line and one plain line on the left,
a simple visual on the right, small 'Fig.' captions, maroon and greys only.
Story: Rhino from scratch -> what the paper shows -> the gap -> our idea, why it is logical, why it matters, our plan.
No result of this project's own experiments is shown on the slides (they are in the report).
Figures: python make_slide_figures.py first.   Then:  python build_slides.py --pdf
"""
import os
import sys

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from report_lib import Report

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.normpath(os.path.join(HERE, "..", "..", "Results"))
FIG = os.path.join(RES, "figures")
LOGO = os.path.join(HERE, "assets", "au_logo.png")
PRES = os.environ.get("M4_PRES_OUT") or os.path.normpath(os.path.join(HERE, "..", "..", "Presentation"))
NAME = "M4_g12_th_conditional-ind-graphs_ind"
MAROON, BLACK, GREY = RGBColor(0x80, 0x1B, 0x19), RGBColor(0, 0, 0), RGBColor(0x66, 0x66, 0x66)
WHITE, LIGHT, PALE, DARKG = RGBColor(255, 255, 255), RGBColor(0xED, 0xED, 0xED), RGBColor(0xF6, 0xE9, 0xE8), RGBColor(0x40, 0x40, 0x40)
FONT = "Times New Roman"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
NOTES = []
FIGN = [0]


def tb(slide, x, y, w, h, text, size=18, bold=False, color=BLACK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    b = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = b.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = ln
        r.font.name, r.font.size, r.font.bold, r.font.italic = FONT, Pt(size), bold, italic
        r.font.color.rgb = color
    return b


def new_slide(title, notes):
    s = prs.slides.add_slide(BLANK)
    tb(s, 0.65, 0.3, 12.0, 0.8, title, 30, True, MAROON)
    n = len(prs.slides)
    tb(s, 12.2, 7.0, 0.8, 0.3, str(n), 10, False, GREY, PP_ALIGN.RIGHT)
    NOTES.append((title, notes))
    return s


def lead(s, bold, plain, extra=None, y=1.4, w=5.1, x=0.65):
    """M1 pattern: one bold line, then one plain line."""
    n = -(-len(bold) // 33)
    tb(s, x, y, w, 0.5 * n + 0.2, bold, 22, True)
    py = y + 0.45 * n + 0.35
    tb(s, x, py, w, 1.8, plain, 20)
    if extra:
        tb(s, x, py + 0.45 * (-(-len(plain) // 38)) + 0.45, w, 1.4, extra, 17, False, GREY, italic=True)


def lead_top(s, bold, plain):
    tb(s, 0.65, 1.3, 12.0, 0.6, bold, 22, True)
    tb(s, 0.65, 1.85, 12.0, 0.6, plain, 20)


def fig_caption(s, text, x, y, w, size=12):
    FIGN[0] += 1
    tb(s, x, y, w, 0.5, f"Fig. {FIGN[0]}: {text}", size, False, BLACK, PP_ALIGN.LEFT)


def box(s, x, y, w, h, text, fill=WHITE, line=BLACK, size=16, bold=False, color=BLACK, first_bold=False, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line
    sh.line.width = Pt(1.25)
    sh.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = 0.08
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.1)
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = ln
        r.font.name, r.font.size = FONT, Pt(size)
        r.font.bold = bold or (first_bold and i == 0)
        r.font.color.rgb = color
    return sh


def hl(s, x, y, w, h, text, **kw):
    """Highlighted box: pale fill, maroon outline (as in M1)."""
    return box(s, x, y, w, h, text, fill=PALE, line=MAROON, **kw)


def arrow(s, x1, y1, x2, y2, color=BLACK, w=1.75):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(w)
    tail = etree.SubElement(c.line._get_or_add_ln(), qn("a:tailEnd"))
    tail.set("type", "triangle")
    return c


def node(s, x, y, text, d=0.55):
    sh = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x - d / 2), Inches(y - d / 2), Inches(d), Inches(d))
    sh.fill.solid()
    sh.fill.fore_color.rgb = WHITE
    sh.line.color.rgb = MAROON
    sh.line.width = Pt(1.5)
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name, r.font.size, r.font.bold = FONT, Pt(13), True
    r.font.color.rgb = MAROON


def picture(s, fname, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(os.path.join(FIG, fname), Inches(x), Inches(y), **kw)


def table(s, data, x, y, colw, size=17, rowh=0.62):
    rows, cols = len(data), len(data[0])
    gt = s.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(sum(colw)), Inches(rowh * rows)).table
    for j, cw in enumerate(colw):
        gt.columns[j].width = Inches(cw)
    for i, r in enumerate(data):
        for j, v in enumerate(r):
            c = gt.cell(i, j)
            c.text = ""
            run = c.text_frame.paragraphs[0].add_run()
            run.text = str(v)
            run.font.name, run.font.size, run.font.bold = FONT, Pt(size), i == 0
            run.font.color.rgb = BLACK
            c.fill.solid()
            c.fill.fore_color.rgb = LIGHT if i == 0 else WHITE
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.04)
    return gt


def grid(s, x, y, n, cell, filled, color, label=None):
    for r in range(n):
        for c in range(n):
            sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + c * cell), Inches(y + r * cell), Inches(cell), Inches(cell))
            sh.fill.solid()
            sh.fill.fore_color.rgb = color if (r, c) in filled else WHITE
            sh.line.color.rgb = GREY
            sh.line.width = Pt(0.75)
            sh.shadow.inherit = False
    if label:
        tb(s, x - 0.2, y + n * cell + 0.05, n * cell + 0.4, 0.35, label, 13, True, BLACK, PP_ALIGN.CENTER)


# ============================================================ 1 title (maroon, logo, as M1)
s = prs.slides.add_slide(BLANK)
bg = s.background.fill
bg.solid()
bg.fore_color.rgb = MAROON
NOTES.append(("Title", "Good day. This is my final presentation for CSE 516. The base paper is Rhino, a deep model that learns causal graphs from time series. "
              "I will explain Rhino from scratch and what its paper shows. Then I will show a gap that the paper leaves open, and our own idea for closing it: why it is logical, why it matters, and our plan. "
              "I started the semester on uGLAD and moved to Rhino on 31 October, so M3 reproduced Rhino and this milestone asks a new question on top of it."))
s.shapes.add_picture(LOGO, Inches(4.42), Inches(1.0), width=Inches(4.49))
lines = ["Name: Het Patel", "Student ID: AU2440266", "Institute: Ahmedabad University", "Date: 12th November 2026", "Program: B.Tech CSE",
         "Domain: Rhino, deep temporal causal discovery", "Can a Deep Temporal Causal Posterior Be Trusted?"]
tb(s, 1.5, 2.9, 10.3, 3.0, lines, 17, False, WHITE, PP_ALIGN.CENTER)
tb(s, 2.5, 6.75, 8.3, 0.4, "B.Tech Computer Science Engineering, School of Engineering and Applied Sciences", 10, False, WHITE, PP_ALIGN.CENTER)

# ============================================================ 2 agenda
s = new_slide("What This Talk Covers", "The path is: basics of temporal causal discovery, the Rhino model, what its paper shows, a gap the paper leaves open, and our idea and plan. "
              "I show no experimental results of our own idea in this talk. They are in the report.")
tb(s, 0.65, 1.3, 11, 0.6, "Five parts, from the base paper to our own plan.", 20)
names = ["Rhino\nBasics", "Rhino\nModel", "Paper\nResults", "The\nGap", "Our\nPlan"]
for i, nm in enumerate(names):
    x = 0.65 + i * 2.5
    if i == 0:
        box(s, x, 3.0, 2.1, 1.1, nm.split("\n"), fill=MAROON, line=MAROON, size=16, bold=True, color=WHITE)
    else:
        box(s, x, 3.0, 2.1, 1.1, nm.split("\n"), size=16, bold=True)
    if i < 4:
        arrow(s, x + 2.1, 3.55, x + 2.5, 3.55, MAROON)

# ============================================================ 3 time series
s = new_slide("What We Want To Learn", "We observe several variables over time, for example gene expression or signals from brain regions. We want to know which variable drives which, and after how many time steps. "
              "The answer is a graph. Black arrows are lagged effects: X1 yesterday affects X2 today. Maroon arrows are instantaneous effects inside one time step. As a tensor the graph has one matrix for lag zero and one for each lag up to L.")
lead(s, "Who drives whom, and after how long.", "The data are several variables over time. The result is a graph.")
cx = [6.9, 8.8, 10.7]
ry = [2.4, 3.5, 4.6]
for c, lb in zip(cx, ["t-2", "t-1", "t"]):
    tb(s, c - 0.6, 1.6, 1.2, 0.4, "time " + lb, 14, True, BLACK, PP_ALIGN.CENTER)
    for i, y in enumerate(ry, 1):
        node(s, c, y, f"X{i}")
for y in ry:
    arrow(s, cx[0] + 0.3, y, cx[1] - 0.3, y)
    arrow(s, cx[1] + 0.3, y, cx[2] - 0.3, y)
arrow(s, cx[0] + 0.28, ry[0] + 0.1, cx[1] - 0.28, ry[1] - 0.1)
arrow(s, cx[1] + 0.28, ry[2] - 0.1, cx[2] - 0.28, ry[1] + 0.1)
arrow(s, cx[2] + 0.5, ry[0] + 0.2, cx[2] + 0.5, ry[1] - 0.2, MAROON, 2.5)
arrow(s, cx[2] + 0.5, ry[1] + 0.2, cx[2] + 0.5, ry[2] - 0.2, MAROON, 2.5)
fig_caption(s, "Black, lagged edges. Maroon, instantaneous edges (no cycle allowed).", 6.4, 5.5, 6.4)

# ============================================================ 4 three features
s = new_slide("Why It Is Hard", "The Rhino paper names three features of real time series. Effects are non-linear. With slow sampling, everything between two measurements is folded into one time step, which creates instantaneous effects. "
              "And the noise is history dependent: its spread depends on the past. The paper's examples are a stock price after an announcement and student marks.")
lead(s, "Real series have three awkward features.", "Older methods handle one or two of them. Rhino aims at all three.")
for i, (h, b) in enumerate([("Non-linear effects", "An announcement acts on a price in a curved way."), ("Instantaneous effects", "Slow sampling folds a day of events into one step."),
                            ("History-dependent noise", "A student with recent good marks scores with little variation.")]):
    box(s, 6.4, 1.5 + i * 1.7, 6.3, 1.4, [h, b], size=17, first_bold=True)

# ============================================================ 5 older methods
s = new_slide("What Older Methods Miss", "Granger-type methods, including the neural ones, assume no instantaneous effects and a fixed noise distribution. Functional methods like VAR-LiNGAM and DYNOTEARS handle instantaneous effects but are linear with fixed noise. "
              "Constraint-based PCMCI+ handles history-dependent noise but only finds an equivalence class of graphs, needs faithfulness, and is slow at high dimension. All of this is from the Rhino paper.")
lead_top(s, "No earlier family covers all three features.", "Rhino is built to close this niche, with a proof that the graph is identifiable.")
table(s, [["Family", "Examples", "What it misses"],
          ["Granger causality (incl. deep)", "cMLP, cLSTM, TCDF, SRU", "No instantaneous effects, fixed noise"],
          ["Functional models", "VAR-LiNGAM, DYNOTEARS", "Linear, fixed noise"],
          ["Constraint based", "PCMCI+", "Equivalence class only, slow for many nodes"],
          ["Rhino", "this paper", "Non-linear, instantaneous, history-dependent noise"]], 0.65, 2.9, [3.9, 3.6, 4.5], 17, 0.7)

# ============================================================ 6 equation
s = new_slide("Rhino In One Equation", "Rhino is a structural equation model. Variable i at time t is a mean part f plus a noise part g. f is a neural network of the lagged and instantaneous parents. "
              "g is a conditional spline flow that reshapes a simple Gaussian noise, and its shape depends on the lagged parents. So the history changes not only the mean but also the spread and shape of the noise. The graph decides which parents each function may use.")
lead(s, "A mean part plus a noise part.", "The graph decides which parents each part may use.")
hl(s, 6.4, 1.5, 6.3, 1.1, "X(i,t)  =  f( parents )  +  g( lagged parents, noise )", size=19, bold=True)
arrow(s, 7.9, 2.6, 7.9, 3.5, MAROON)
arrow(s, 11.2, 2.6, 11.2, 3.5, MAROON)
box(s, 6.4, 3.5, 3.1, 1.9, ["f: neural network", "non-linear lagged and instantaneous effects"], size=15, first_bold=True)
box(s, 9.6, 3.5, 3.1, 1.9, ["g: spline flow", "noise shaped by the history"], size=15, first_bold=True)
fig_caption(s, "Rhino's structural equation model.", 6.4, 5.65, 6.3)

# ============================================================ 7 noise
s = new_slide("History-Dependent Noise", "On the horizontal axis is the value of a parent in the past. On the vertical axis is the part of the variable that its mean does not explain. "
              "On the left the noise has the same spread whatever the past is. On the right the spread grows with the past value. A fixed-noise model cannot represent this, and Rhino's spline flow can. These are simulated points for illustration.")
lead(s, "g lets the noise change with the past.", "On the right the spread grows with the past value. A fixed-noise model cannot do this.")
picture(s, "slide_noise.png", 6.2, 1.7, w=6.7)
fig_caption(s, "Simulated illustration of fixed and history-dependent noise.", 6.2, 4.4, 6.7)

# ============================================================ 8 switches
s = new_slide("The Graph Is A Set Of Switches", "Concretely, the graph is a stack of matrices. G0 holds the instantaneous edges and must be acyclic. G1 to GL hold the lagged edges and may have any pattern, because time orders them. "
              "A filled cell switches a parent on inside f and g. So learning the graph means learning which cells are on. The number of cells grows like L plus one times D squared.")
lead(s, "A filled cell turns one parent on.", "Learning the graph means learning which cells are on.")
grid(s, 6.4, 2.2, 5, 0.38, {(0, 1), (1, 2), (3, 2), (2, 4)}, MAROON, "G0: instant. (DAG)")
grid(s, 8.6, 2.2, 5, 0.38, {(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (0, 3)}, DARKG, "G1: lag 1")
grid(s, 10.8, 2.2, 5, 0.38, {(0, 0), (2, 2), (4, 4), (3, 1)}, DARKG, "G2: lag 2")
fig_caption(s, "The graph as one matrix per lag.", 6.4, 4.6, 6.4)

# ============================================================ 9 learning
s = new_slide("Learning A Distribution", "Rhino takes a Bayesian view. A prior over graphs rewards sparsity and punishes cycles in the instantaneous part, with a NOTEARS-style penalty. The likelihood of the data given a graph comes from the model on the previous slide. "
              "The true posterior over graphs is intractable, so Rhino learns an approximation q of G by maximising the evidence lower bound. Gradients go through graph samples with the Gumbel-softmax trick, and the acyclicity penalty is tightened step by step with an augmented Lagrangian.")
lead(s, "Rhino learns a distribution over graphs.", "Not one graph. It trains q(G) to explain the data while staying sparse and acyclic.")
for i, (h, b) in enumerate([("Prior p(G)", "sparse, acyclic"), ("Likelihood", "from f and g"), ("q(G)", "learned")]):
    (hl if i == 2 else box)(s, 6.4 + i * 2.15, 1.6, 2.0, 1.2, [h, b], size=15, first_bold=True)
    arrow(s, 7.4 + i * 2.15, 2.8, 9.55, 3.5, MAROON if i == 2 else BLACK)
hl(s, 6.4, 3.5, 6.3, 1.1, "ELBO = E_q[ log p(X|G) + log p(G) ] + entropy of q", size=16, bold=True)
tb(s, 6.4, 4.8, 6.3, 0.9, ["Acyclicity penalty, tightened by an augmented Lagrangian.", "Gumbel-softmax gives gradients through graph samples."], 14, False, GREY)
fig_caption(s, "The training objective of Rhino.", 6.4, 5.8, 6.3)

# ============================================================ 10 output
s = new_slide("What Rhino Outputs", "After training, one can read the probability of every possible edge entry. The paper then reads the result in two ways: it ranks the entries and computes the AUROC, or it rounds at one half to get one graph and computes the F1. "
              "In the released code an instantaneous pair is one three-way choice: edge one way, edge the other way, or none. A lagged entry is an independent yes or no. The values drawn here are illustrative.")
lead(s, "Every possible edge gets a probability.", "The paper ranks them (AUROC) or rounds at 0.5 (F1).")
vals = [[0.02, 0.97, 0.05], [0.03, 0.10, 0.91], [0.88, 0.04, 0.01]]
for r in range(3):
    for c in range(3):
        v = vals[r][c]
        shade = RGBColor(int(255 - 127 * v), int(255 - 226 * v), int(255 - 230 * v))
        box(s, 6.4 + c * 0.95, 1.9 + r * 0.8, 0.9, 0.75, f"{v:.2f}", fill=shade, size=15, shape=MSO_SHAPE.RECTANGLE, color=WHITE if v > 0.6 else BLACK)
arrow(s, 9.4, 3.3, 10.0, 3.3, MAROON)
box(s, 10.1, 2.2, 2.6, 0.95, ["Rank entries", "AUROC"], size=15, first_bold=True)
box(s, 10.1, 3.4, 2.6, 0.95, ["Round at 0.5", "one graph, F1"], size=15, first_bold=True)
fig_caption(s, "Edge probabilities (illustrative values).", 6.4, 4.5, 6.3)

# ============================================================ 11 identifiability
s = new_slide("Why The Target Is Well Defined", "A model is identifiable if two different graphs cannot produce the same data distribution. Without that, a learned graph would be arbitrary. The paper proves Rhino is identifiable under conditions on f and g. "
              "Theorem 2, from Geffner et al., says that with infinite data and no misspecification the optimum is the true graph. The paper itself says that in practice one gets an approximate posterior at a local optimum. That caveat matters for us.")
lead(s, "In theory the true graph is unique.", "The paper proves Rhino is identifiable. In practice training stops at a local optimum.")
for i, (h, b) in enumerate([("Conditions", "smooth functions, f non-linear, noise not degenerate"), ("Theorem 1", "two graphs cannot give the same likelihood"),
                            ("Theorem 2", "with infinite data the best fit is the true graph")]):
    (hl if i == 1 else box)(s, 6.6, 1.5 + i * 1.75, 5.9, 1.2, [h, b], size=16, first_bold=True)
    if i < 2:
        arrow(s, 9.55, 2.7 + i * 1.75, 9.55, 3.25 + i * 1.75, MAROON)

# ============================================================ 12 how paper tests
s = new_slide("How The Paper Tests Rhino", "The paper uses three benchmarks. Synthetic data: 160 datasets, five per setting, and 75 percent were made to mismatch Rhino's own configuration. "
              "DREAM3 is a gene expression benchmark with five networks of one hundred genes and 21 time points. Netsim is simulated fMRI with fifteen brain regions and 200 time steps. In every case the score compares with a known true graph.")
lead_top(s, "Three benchmarks, always scored against a known graph.", "F1 on synthetic data, AUROC on DREAM3 and Netsim.")
for i, (h, b) in enumerate([("Synthetic", ["160 datasets", "5 to 40 nodes, lag 2", "75% mismatched to Rhino"]), ("DREAM3 genes", ["5 networks, 100 genes", "21 time points", "AUROC"]),
                            ("Netsim brain", ["fMRI, 15 regions", "200 time steps", "AUROC"])]):
    box(s, 0.65 + i * 4.1, 3.0, 3.8, 2.3, [h] + b, size=17, first_bold=True)
fig_caption(s, "Baselines: VAR-LiNGAM, PCMCI+, DYNOTEARS, cMLP, cLSTM, TCDF, SRU, eSRU.", 0.65, 5.6, 12)

# ============================================================ 13 synthetic
s = new_slide("Paper Result 1: Synthetic Data", "On synthetic data Rhino gets the best or close to the best F1 for the full temporal graph, especially in low dimension. History-dependent noise helps the lagged graph (Rhino against Rhino+g). "
              "PCMCI+ is strong but gives only equivalence classes and exceeded the one-week limit at forty nodes. DYNOTEARS is weaker because it is linear. The figure is the paper's lag experiment, Table 1: a lag that is too short hurts a lot, a lag that is too long costs little.")
lead(s, "Best or close to best on synthetic data.", "Especially in low dimension. A lag that is too long costs little.")
picture(s, "slide_lag.png", 6.4, 1.5, w=6.2)
fig_caption(s, "Paper, Table 1: temporal F1 by model lag (true lag is 2).", 6.4, 5.45, 6.4)

# ============================================================ 14 dream3
s = new_slide("Paper Result 2: DREAM3", "On DREAM3 the paper reports the AUROC of the summary graph. Rhino or its Gaussian-noise variant has the highest AUROC on all five networks, ahead of the best Granger method shown here, eSRU. "
              "Margins are clear on the E. coli and first yeast networks and small on the other two. DYNOTEARS and PCMCI+ are close to chance. Values are from Table 2 of the paper.")
lead(s, "On gene networks Rhino has the top AUROC.", "Rhino or Rhino+g wins all five networks, by small margins on two.")
picture(s, "slide_dream3.png", 6.0, 1.7, w=7.0)
fig_caption(s, "Paper, Table 2: AUROC of the summary graph (subset of methods).", 6.0, 4.55, 7.0)

# ============================================================ 15 netsim
s = new_slide("Paper Result 3: Netsim", "On Netsim the paper reports a Rhino AUROC of 0.99, which is nearly perfect, against at most 0.93 for the baselines. The variant without instantaneous effects drops to 0.93, so modelling them matters here. "
              "The Gaussian-noise variant gets 0.974, so history-dependent noise also helps. Values are from Table 3 of the paper.")
lead(s, "On brain connectivity the AUROC is 0.99.", "Without instantaneous effects it drops to 0.93.")
picture(s, "slide_netsim.png", 6.4, 1.5, w=6.0)
fig_caption(s, "Paper, Table 3: AUROC of the summary graph.", 6.4, 4.95, 6.0)

# ============================================================ 16 M3
s = new_slide("What Our M3 Run Confirmed", "In M3 I ran the authors' code. Most claims were reproduced: history-dependent noise helps, robustness to a longer lag, and Netsim AUROC 0.987 against the paper's 0.99. "
              "One claim was only partly reproduced and one was not: Rhino+s close to Rhino. Note the last row. Nobody, neither the paper nor my M3 work, tested whether the probabilities themselves can be trusted.")
lead_top(s, "We reproduced the accuracy story.", "Nobody tested whether the probabilities can be trusted.")
table(s, [["Claim of the paper", "M3 reproduction"],
          ["History-dependent noise helps", "Reproduced"],
          ["Robust to a longer lag, a shorter lag hurts", "Reproduced in shape"],
          ["Netsim AUROC 0.99", "0.987 with the paper's steps"],
          ["Best or competitive on synthetic data", "Partly reproduced"],
          ["Rhino+s close to Rhino", "Not reproduced"],
          ["Probabilities are well calibrated", "Never tested"]], 0.65, 2.7, [6.5, 5.5], 17, 0.58)

# ============================================================ 17 measures vs needs
s = new_slide("What The Paper Measures", "The paper's measures, AUROC and F1, answer one question: how well does the output agree with a known true graph? "
              "A real user has no true graph. They will follow up the top edges one by one, in the lab or in the clinic, and ask how many will turn out to be wrong. That question can be answered only if the probabilities mean what they say.")
lead(s, "The paper checks accuracy against a known graph.", "A real user has no true graph. They ask: how many of these edges are wrong?")
box(s, 6.6, 1.7, 5.9, 1.5, ["The paper measures", "AUROC and F1, with a known true graph"], size=17, first_bold=True)
arrow(s, 9.55, 3.2, 9.55, 3.9, MAROON)
hl(s, 6.6, 3.9, 5.9, 1.5, ["A user asks", "How many edges on my list are wrong?"], size=17, first_bold=True)
fig_caption(s, "Accuracy is not the same as trust.", 6.6, 5.6, 5.9)

# ============================================================ 18 calibration
s = new_slide("What A Trustworthy Probability Is", "The word is calibration. A forecast is calibrated if, among all cases where it says 0.9, about nine in ten happen. For edges: among entries with probability 0.9, about 90 percent should be real. "
              "The picture is a schematic, not data. The dashed line is calibrated. The maroon curve is overconfident: when it says 0.99, the real frequency is much lower. A ranking can be perfect while the probabilities are overconfident.")
lead(s, "A probability should match how often it is right.", "Among edges scored 0.9, about 9 in 10 should be real. This is called calibration.")
picture(s, "slide_reliability_schematic.png", 7.0, 1.3, h=4.5)
fig_caption(s, "Schematic, not data.", 7.0, 5.85, 5.0)

# ============================================================ 19 warning sign
s = new_slide("A Warning Sign", "The Rhino paper shows, in its Figure 8, that during training the AUROC and the validation likelihood fall while the F1 rises, and it explains this as overfitting. I reproduced the same pattern in M3 in three settings. "
              "On Netsim the AUROC peaks at 0.989 and falls to 0.939, the validation log-likelihood falls from minus 31.5 to minus 76.1, and the F1 rises from 0.088 to 0.538. The model becomes more decided without becoming more right.")
lead(s, "Training made Rhino more decided, not more right.", "Netsim, M3 reproduction of the paper's Fig. 8, from the best step to the last.")
box(s, 6.6, 1.5, 5.9, 1.3, ["AUROC falls", "0.989 to 0.939"], size=17, first_bold=True)
box(s, 6.6, 3.0, 5.9, 1.3, ["Validation log-likelihood falls", "-31.5 to -76.1"], size=17, first_bold=True)
hl(s, 6.6, 4.5, 5.9, 1.3, ["F1 of the rounded graph rises", "0.088 to 0.538"], size=17, first_bold=True)

# ============================================================ 20 reasons
s = new_slide("Why We Suspect The Probabilities", "These are reasons to suspect a problem, and the study tests whether they matter. One: the training objective rewards likelihood, not the quality of edge probabilities. Two: the posterior is a product of independent factors, so it ignores dependence between edges. "
              "Three: long training with sparsity and acyclicity penalties can push the logits to extremes. Four: the posterior comes from one training run on small data and nobody checks it against truth. None of these is established.")
lead(s, "Four reasons to suspect them.", "These are hypotheses that we test. They are not claims.")
for i, t in enumerate(["The objective rewards likelihood, not good probabilities", "Independent factors ignore dependence between edges",
                       "Long training can push logits to extremes", "One run on small data, never checked against truth"]):
    box(s, 6.4 + (i % 2) * 3.2, 1.6 + (i // 2) * 2.0, 3.05, 1.75, t, size=15)

# ============================================================ 21 our idea
s = new_slide("Our Idea", "This is our own formulation, and it is not a new discovery algorithm. We take Rhino as given and ask whether its edge probabilities can be used to select edges with a stated error budget. "
              "Given the probabilities and a budget alpha, choose an edge set that finds as many true edges as possible while the expected share of wrong edges stays at most alpha. At use time no true graph is available. Labels are used only on calibration datasets. We call it selective temporal causal discovery.")
lead(s, "Ask for an error budget, then choose the edges.", "Keep the share of wrong edges below a budget alpha, and still find as many true edges as possible.")
box(s, 6.6, 1.5, 5.9, 1.2, ["Given", "edge probabilities p and a budget alpha"], size=16, first_bold=True)
arrow(s, 9.55, 2.7, 9.55, 3.2, MAROON)
box(s, 6.6, 3.2, 5.9, 1.2, ["Choose", "an edge set S with as many true edges as possible"], size=16, first_bold=True)
arrow(s, 9.55, 4.4, 9.55, 4.9, MAROON)
hl(s, 6.6, 4.9, 5.9, 1.2, ["Subject to", "expected share of wrong edges <= alpha"], size=16, first_bold=True)
fig_caption(s, "Selective temporal causal discovery.", 6.6, 6.25, 5.9)

# ============================================================ 22 logical
s = new_slide("Why It Is Logical", "Here is the central identity. For any selected set S, the share of wrong edges equals the error the posterior promises plus the overconfidence on that set. Both sides are one minus a mean, so the difference is the mean of p minus the mean of the truth. "
              "The proof is one line. It tells us a posterior fails exactly where it is overconfident on what it selects. If the posterior is calibrated, the Bayesian false discovery rule controls the expected error. The bar is an illustration with made-up proportions.")
lead(s, "One identity explains when a posterior fails.", "Wrong share = promised error + overconfidence. If the probabilities are calibrated, the overconfidence is zero.")
hl(s, 6.4, 1.6, 6.3, 1.2, "wrong share  =  promised error  +  overconfidence", size=17, bold=True)
box(s, 6.8, 3.4, 3.0, 0.8, "promised", fill=LIGHT, line=GREY, size=15, shape=MSO_SHAPE.RECTANGLE)
box(s, 9.8, 3.4, 2.3, 0.8, "overconfidence", fill=MAROON, line=MAROON, size=15, color=WHITE, bold=True, shape=MSO_SHAPE.RECTANGLE)
tb(s, 6.4, 4.4, 6.3, 0.9, "promised error = mean of (1 - p) over the chosen edges", 14, False, GREY)
fig_caption(s, "Illustration with made-up proportions.", 6.4, 5.2, 6.3)

# ============================================================ 23 matters
s = new_slide("Why It Matters", "Think of a gene network with a hundred candidate edges. Every edge you follow costs an experiment. If the probabilities are trustworthy, you can choose a budget, for example at most one in ten wrong, and get the longest list that respects it. "
              "If they are not, you cannot choose how many edges to follow, and you are misled without knowing it.")
lead(s, "Every edge you follow costs an experiment.", "A budget turns a probability graph into a decision.")
for i in range(10):
    if i == 6:
        box(s, 6.4 + i * 0.64, 1.6, 0.55, 0.55, "x", fill=MAROON, line=MAROON, size=13, color=WHITE, bold=True, shape=MSO_SHAPE.RECTANGLE)
    else:
        box(s, 6.4 + i * 0.64, 1.6, 0.55, 0.55, "ok", size=12, shape=MSO_SHAPE.RECTANGLE)
fig_caption(s, "Ten chosen edges, one wrong: budget 0.1.", 6.4, 2.3, 6.3)
hl(s, 6.4, 3.3, 3.1, 2.2, ["With trustworthy p", "choose alpha and get the longest list within it"], size=15, first_bold=True)
box(s, 9.6, 3.3, 3.1, 2.2, ["Without it", "no way to choose how many edges to follow"], size=15, first_bold=True)

# ============================================================ 24 plan
s = new_slide("Our Plan", "Our method has three steps and trains nothing. We keep the finished Rhino models from M3. Step one reads the exact edge probabilities from the saved weights. Step two calibrates them, with a temperature or a cutoff learned on other datasets that have a known graph. "
              "Step three selects the edge set with the Bayesian false discovery rule. The selection itself costs a sort.")
lead(s, "A thin layer on a frozen Rhino.", "No retraining. Labels are used only on calibration datasets.")
box(s, 6.6, 1.35, 5.9, 0.9, "Rhino (frozen, from M3)", fill=LIGHT, line=GREY, size=15, bold=True)
for i, (h, b) in enumerate([("1. Exact probabilities", "read from the saved logits"), ("2. Calibrate", "temperature or a cutoff learned on other datasets"), ("3. Select", "Bayesian false discovery rule")]):
    y = 2.6 + i * 1.3
    arrow(s, 9.55, y - 0.35, 9.55, y, MAROON)
    (hl if i == 2 else box)(s, 6.6, y, 5.9, 0.95, [h, b], size=15, first_bold=True)

# ============================================================ 25 KPIs
s = new_slide("How We Will Judge It", "The KPIs match the layers of the problem. The key one is the realised share of wrong edges against the budget, because it tests the promise directly, exactly where the user reads the list. "
              "Brier score, log-loss and expected calibration error measure probability quality, but average over all entries. Power matters because control without power is empty. AUROC and F1 keep the link to the paper.")
lead_top(s, "The key KPI is realised error against the budget.", "Plus probability quality, power, and accuracy for the link to the paper.")
table(s, [["KPI", "Why"],
          ["Realised share of wrong edges against budget", "Is the promise true?"],
          ["Brier, log-loss, calibration error", "Quality of the probabilities"],
          ["Power (share of true edges found)", "The price of control"],
          ["AUROC, F1", "Link to the paper"]], 0.65, 2.9, [6.8, 5.2], 18, 0.7)

# ============================================================ 26 expect
s = new_slide("What We Expect", "This is the claim we test. The horizontal axis is the budget we promise, the vertical axis is the share of wrong edges we get. On the diagonal the promise is kept. Above it there are more wrong edges than promised. "
              "We expect the raw posterior to land above it. We expect a repair to bring it near the diagonal for moderate budgets, at a price in power, and we expect no transfer to real data to be guaranteed. The learned cutoff was added after we saw the first repair, so it is exploratory. This is a schematic of the target, not a result.")
lead(s, "Control at moderate budgets, at a price in power.", "Raw Rhino should break its budget. A repair should help. Real data may not transfer.",
     "The learned cutoff was added after we saw the first repair, so it is exploratory.")
picture(s, "slide_target.png", 7.0, 1.3, h=4.5)
fig_caption(s, "Schematic of the target, not a result.", 7.0, 5.85, 5.0)

# ============================================================ 27 benefits and costs
s = new_slide("Benefits And Costs", "The benefit is that a user gets an error budget in the units they care about, without changing or retraining the model, at a cost of seconds. The costs are real. It needs labelled graphs from similar data. "
              "The guarantee is an average over datasets, not for one dataset. Calibration cannot repair a weak ranking. A budget that is too strict selects nothing. We measure each of these costs and report them.")
lead(s, "A useful but limited tool.", "We state both sides.")
hl(s, 6.4, 1.6, 3.1, 3.2, ["Benefits", "A budget in the user's units", "No retraining", "Seconds of compute"], size=17, first_bold=True)
box(s, 9.6, 1.6, 3.1, 3.2, ["Costs", "Needs labelled graphs", "Average guarantee only", "Cannot fix a weak ranking", "Strict budgets select nothing"], size=17, first_bold=True)

# ============================================================ 28 positioning
s = new_slide("Baselines And Positioning", "Our baselines are the practice the paper suggests, the raw posterior with a threshold or with the Bayesian FDR rule, and the standard temperature fix. The oracle threshold is a ceiling that uses the truth. The state-of-the-art anchor is Rhino from Microsoft Research. "
              "Related work on calibration of causal graphs exists for static graphs, and MMPC-p controls false discovery for time series with p-values. I did not find an audit of the posterior of a deep temporal causal model, but my search was short and I claim no priority. We do not claim a better discovery algorithm.")
lead_top(s, "Not a better algorithm. A trust check of Rhino.", "Baselines are what the paper suggests and the standard fix.")
for i, (h, b) in enumerate([("Raw posterior", "round at 0.5 or Bayesian FDR"), ("Temperature scaling", "the standard fix"), ("Learned cutoff", "our direct repair"), ("Oracle", "uses the truth, a ceiling")]):
    (hl if i == 2 else box)(s, 0.65 + i * 3.05, 3.4, 2.85, 1.6, [h, b], size=16, first_bold=True)
fig_caption(s, "Rhino (Microsoft Research, ICLR 2023) is the anchor and is not changed.", 0.65, 5.3, 12)

# ============================================================ 29 summary
s = new_slide("Summary", "To summarise. Rhino is a strong accuracy method that gives a probability for every edge. The paper and my reproduction measure accuracy against a known graph, and no one tested whether the probabilities can be trusted. "
              "Our idea is error-controlled edge selection. It follows from one identity, it matters because every edge costs an experiment, and our plan is a thin layer on a frozen Rhino. The full evidence is in the report. Thank you.")
lead(s, "Rhino ranks edges well. Can its probabilities be trusted?", "That is our question. The plan on the previous slides is how we answer it.")
box(s, 6.6, 1.6, 5.9, 1.3, ["Base paper", "strong accuracy, a probability for every edge"], size=16, first_bold=True)
box(s, 6.6, 3.2, 5.9, 1.3, ["The gap", "accuracy is measured, trust is not"], size=16, first_bold=True)
hl(s, 6.6, 4.8, 5.9, 1.3, ["Our idea", "error-controlled edge selection, a thin layer on Rhino"], size=16, first_bold=True)

# ============================================================ 30 references
s = new_slide("References", "These are the main references.")
refs = [
    "[1] W. Gong, J. Jennings, C. Zhang, N. Pawlowski, \"Rhino: Deep Causal Temporal Relationship Learning with History-dependent Noise,\" ICLR, 2023.",
    "[2] C. Geffner et al., \"Deep End-to-end Causal Inference,\" arXiv:2202.02195, 2022.",
    "[3] J. Runge, \"Discovering contemporaneous and lagged causal relations in autocorrelated nonlinear time series datasets,\" UAI, 2020.",
    "[4] R. Pamfil et al., \"DYNOTEARS: Structure Learning from Time-Series Data,\" AISTATS, 2020.",
    "[5] A. Hyvarinen, K. Zhang, S. Shimizu, P. Hoyer, \"Estimation of a Structural Vector Autoregression Model Using Non-Gaussianity,\" JMLR, 2010.",
    "[6] X. Zheng, B. Aragam, P. Ravikumar, E. Xing, \"DAGs with NO TEARS: Continuous Optimization for Structure Learning,\" NeurIPS, 2018.",
    "[7] C. Guo, G. Pleiss, Y. Sun, K. Weinberger, \"On Calibration of Modern Neural Networks,\" ICML, 2017.",
    "[8] M. Newton et al., \"Detecting differential gene expression with a semiparametric hierarchical mixture method,\" Biostatistics, 2004.",
    "[9] Y. Benjamini, Y. Hochberg, \"Controlling the False Discovery Rate,\" J. R. Stat. Soc. B, 1995.",
]
for i, r in enumerate(refs):
    tb(s, 0.65, 1.3 + i * 0.58, 12.0, 0.55, r, 13)

# ============================================================ save
pptx_path = os.path.join(PRES, NAME + "_Slides.pptx")
os.makedirs(PRES, exist_ok=True)
prs.save(pptx_path)
print("saved", pptx_path, len(prs.slides), "slides")

rep = Report(FIG)
rep.title("Speaker notes, M4 final presentation", 16)
rep.para("Het Patel (AU2440266). One block per slide. Numbers of the base paper are from its Tables 1 to 3; schematic figures are marked on the slides.", "c", 10, 10)
for i, (t, txt) in enumerate(NOTES, 1):
    rep.h2(f"Slide {i}. {t}")
    rep.para(txt, "j", 6, 11)
notes_docx = os.path.join(PRES, NAME + "_Speaker_Notes.docx")
rep.save(notes_docx)
print("saved", notes_docx)

if "--pdf" in sys.argv:
    from docx2pdf import convert
    convert(notes_docx, os.path.join(PRES, NAME + "_Speaker_Notes.pdf"))
    import win32com.client
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(pptx_path, WithWindow=False)
    pres.SaveAs(os.path.join(PRES, NAME + "_Slides.pdf"), 32)
    pres.Close()
    print("pdfs written")
