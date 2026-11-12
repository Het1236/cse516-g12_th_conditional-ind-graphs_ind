"""LaTeX backend with the same calls as report_lib.Report, in the layout of an ICLR paper (the style of the Rhino paper):
thick rule above a small-caps title, 5.5 in Times text, small-caps section heads, centred ABSTRACT, booktabs tables, author-year citations.
No package outside a standard MiKTeX install is needed (natbib is replaced by a small citation converter).
"""
import os
import re
import shutil
import subprocess
import unicodedata

# author-year labels for the numbered reference list of build_report.py
CITE = {
    1: ("Gong et al.", "2023"), 2: ("Hyvärinen et al.", "2010"), 3: ("Pamfil et al.", "2020"), 4: ("Runge", "2020"),
    5: ("Khanna & Tan", "2019"), 6: ("Tank et al.", "2018"), 7: ("Nauta et al.", "2019"), 8: ("Holm", "1979"),
    9: ("Assaad et al.", "2022"), 10: ("Zheng et al.", "2018"), 11: ("Newton et al.", "2004"),
    12: ("Benjamini & Hochberg", "1995"), 13: ("Jabbari et al.", "2017"), 14: ("Lorch et al.", "2022"),
    15: ("Guillen Pegueroles et al.", "2018"), 16: ("Angelopoulos et al.", "2021"), 17: ("Wilcoxon", "1945"),
    18: ("Guo et al.", "2017"), 19: ("Naeini et al.", "2015"), 20: ("Shan & Zhou", "2026"), 21: ("Microsoft", "2022"),
}

PREAMBLE = r"""\documentclass[10pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{mathptmx}
\usepackage{amsmath,amssymb}
\usepackage{graphicx,booktabs,array,enumitem,xcolor,fancyhdr,titlesec,caption,microtype}
\usepackage[paperwidth=8.5in,paperheight=11in,textwidth=5.5in,textheight=9in,top=1in,headsep=0.25in,headheight=12pt]{geometry}
\setlength{\parindent}{0pt}
\setlength{\emergencystretch}{3em}
\setlength{\parskip}{5.5pt}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.15}
\titleformat{\section}{\large\scshape}{\thesection}{0.6em}{}
\titleformat{name=\section,numberless}{\large\scshape}{}{0em}{}
\titleformat{\subsection}{\normalsize\bfseries}{\thesubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{12pt plus 3pt minus 2pt}{5pt plus 1pt}
\titlespacing*{\subsection}{0pt}{8pt plus 2pt minus 1pt}{3pt plus 1pt}
\captionsetup{font=small,labelfont=bf,labelsep=colon,justification=justified}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small CSE 516 Major Project, Milestone 4 (Ahmedabad University)}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}}
\setlist[itemize]{leftmargin=1.4em,itemsep=2pt,topsep=2pt,parsep=0pt}
\begin{document}
"""


def _plain(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


class LatexReport:
    def __init__(self, fig_dir, out_dir, name):
        self.fig_dir, self.out_dir, self.name = fig_dir, out_dir, name
        self.body = []
        self.figs = set()
        self.fig_scale = 1.0

    # ------------------------------------------------------------------ text conversion
    @staticmethod
    def cite_convert(t):
        """[n], [n, m], [n, Section 3] -> (Author, Year); 'X et al. [n]' -> 'X et al. (Year)'. Math is protected before this call."""
        t = re.sub(r"et al\. \[(\d+)\]", lambda m: f"et al. ({CITE[int(m.group(1))][1]})", t)

        def rep(m):
            nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
            note = m.group(2)
            labs = "; ".join(f"{CITE[n][0]}, {CITE[n][1]}" for n in nums)
            return f"({labs}{', ' + note if note else ''})"
        return re.sub(r"\[(\d+(?:\s*,\s*\d+)*)(?:,\s*([A-Za-z][^\]]*))?\]", rep, t)

    @staticmethod
    def esc(s):
        out = []
        for ch in s:
            out.append({"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}.get(ch, ch))
        s = "".join(out)
        s = s.replace("±", r"$\pm$").replace("<=", r"$\le$").replace(">=", r"$\ge$").replace(" - ", r" $-$ ")
        s = re.sub(r'"(.*?)"', r"``\1''", s)
        s = re.sub(r"(?<![\w])'(?=\w)", "`", s)
        s = re.sub(r"\balpha\b", r"$\\alpha$", s)
        s = re.sub(r"\btau\b", r"$\\tau$", s)
        s = re.sub(r"\beps\b", r"$\\varepsilon$", s)
        s = re.sub(r"\blambda\\_s\b", r"$\\lambda_s$", s)
        return s

    def tx(self, t):
        """Plain markup (**bold**, __italic__, X_{sub}, ^{sup}, $math$) to LaTeX."""
        maths = []

        def keep(m):
            maths.append(m.group(0))
            return f"\x00{len(maths) - 1}\x00"
        t = re.sub(r"\$[^$]+\$", keep, t)
        t = self.cite_convert(t)
        parts = re.split(r"(\*\*.+?\*\*|__.+?__|[A-Za-z]_\{[^}]*\}|_\{[^}]*\}|\^\{[^}]*\})", t)
        res = []
        for p in parts:
            if p.startswith("**") and p.endswith("**") and len(p) > 4:
                res.append(r"\textbf{" + self.tx_inner(p[2:-2]) + "}")
            elif p.startswith("__") and p.endswith("__") and len(p) > 4:
                res.append(r"\textit{" + self.tx_inner(p[2:-2]) + "}")
            elif re.fullmatch(r"[A-Za-z]_\{[^}]*\}", p):
                res.append("$" + p[0] + "_{" + self.math_words(p[3:-1]) + "}$")
            elif p.startswith("_{"):
                res.append(r"\textsubscript{" + self.esc(p[2:-1]) + "}")
            elif p.startswith("^{"):
                res.append(r"\textsuperscript{" + self.esc(p[2:-1]) + "}")
            else:
                res.append(self.esc(p))
        out = "".join(res)
        return re.sub(r"\x00(\d+)\x00", lambda m: maths[int(m.group(1))], out)

    def tx_inner(self, t):
        return self.tx(t)

    @staticmethod
    def math_words(s):
        return s.replace("alpha", r"\alpha").replace("eps", r"\varepsilon").replace("tau", r"\tau")

    # ------------------------------------------------------------------ API (same names as report_lib.Report)
    def front(self, title, authors, lines):
        b = self.body
        b.append(r"\thispagestyle{plain}")
        b.append(r"\noindent\rule{\textwidth}{4pt}\par\vspace{0.2in}")
        b.append(r"{\fontsize{17}{21}\selectfont\scshape\raggedright " + self.tx(title) + r"\par}\vspace{0.22in}")
        b.append(r"{\bfseries " + self.tx(authors) + r"}\par\vspace{2pt}")
        for ln in lines:
            b.append(self.tx(ln) + r"\par")
        b.append(r"\vspace{0.12in}")

    def abstract(self, text):
        b = self.body
        b.append(r"\begin{center}{\large\scshape Abstract}\end{center}\vspace{-6pt}")
        b.append(r"\begin{list}{}{\setlength{\leftmargin}{0.5in}\setlength{\rightmargin}{0.5in}\setlength{\topsep}{0pt}}\item[]")
        b.append(r"\small " + self.tx(text))
        b.append(r"\end{list}")

    def h1(self, text):
        m = re.match(r"^(\d+)\.\s+(.*)$", text)
        if m:
            self.body.append(r"\section{" + self.tx(m.group(2)) + "}")
        else:
            self.body.append(r"\section*{" + self.tx(text) + "}")

    def h2(self, text):
        m = re.match(r"^(\d+\.\d+)\s+(.*)$", text)
        if m:
            self.body.append(r"\subsection{" + self.tx(m.group(2)) + "}")
        else:
            self.body.append(r"\subsection*{" + self.tx(text) + "}")

    def para(self, text, align="j", after=6, size=None, keep=False):
        self.body.append(self.tx(text) + "\n")

    def bullets(self, items):
        self.body.append(r"\begin{itemize}")
        for it in items:
            self.body.append(r"\item " + self.tx(it))
        self.body.append(r"\end{itemize}")

    def eq(self, text, label=None, tex=None):
        self.body.append(r"\begin{equation}" + (tex if tex else self.tx(text)) + r"\end{equation}")

    def _caption(self, cap):
        m = re.match(r"^(Table [A-Z]?\d+)[.:]\s*(.*)$", cap) or re.match(r"^(Fig\.? \d+)[.:]\s*(.*)$", cap)
        if m:
            lab = m.group(1).replace("Fig.", "Figure")
            return r"\textbf{" + lab + r":} " + self.tx(m.group(2))
        return self.tx(cap)

    def table(self, caption, header, rows, widths, size=8.5, note=None, bold_first=False):
        n = len(header)
        scale = (5.5 - n * 0.09) / sum(widths)
        spec = "".join(r">{\raggedright\arraybackslash}p{%.2fin}" % (w * scale) for w in widths)
        fs = r"\footnotesize" if size >= 8 else r"\scriptsize"
        b = self.body
        b.append(r"\begin{table}[!ht]\centering")
        b.append(r"\captionsetup{type=table}\caption*{" + self._caption(caption) + "}")
        b.append(fs)
        b.append(r"\begin{tabular}{" + spec + "}\\toprule")
        b.append(" & ".join(r"\textbf{" + self.tx(h) + "}" for h in header) + r" \\ \midrule")
        for r in rows:
            b.append(" & ".join(self.tx(str(v)) for v in r) + r" \\")
        b.append(r"\bottomrule\end{tabular}")
        if note:
            b.append(r"\par\vspace{3pt}{\footnotesize " + self.tx(note) + "}")
        b.append(r"\end{table}")

    def figure(self, fname, caption, width=6.3):
        self.figs.add(fname)
        frac = min(1.0, width / 6.5)
        b = self.body
        b.append(r"\begin{figure}[!ht]\centering")
        b.append(r"\includegraphics[width=%.2f\textwidth]{figures/%s}" % (frac, fname))
        b.append(r"\captionsetup{type=figure}\caption*{" + self._caption(caption) + "}")
        b.append(r"\end{figure}")

    def references(self, refs):
        def surname(r):
            first = re.split(r",| et al\.| and ", r)[0]
            return _plain(first.split()[-1])
        items = sorted(refs, key=surname)
        fix = {"Hyvarinen": "Hyvärinen", "Scholkopf": "Schölkopf", "Candes": "Candès"}
        self.body.append(r"\section*{References}")
        self.body.append(r"\begingroup\small\setlength{\parskip}{3pt}")
        for r in items:
            for a, bb in fix.items():
                r = r.replace(a, bb)
            self.body.append(r"\hangindent=0.2in\hangafter=1\noindent " + self.tx(r) + r"\par")
        self.body.append(r"\endgroup")

    def appendix(self):
        self.body.append(r"\appendix")

    def pagebreak(self):
        self.body.append(r"\clearpage")

    def save(self, _unused=None):
        latex_dir = os.path.join(self.out_dir, "latex")
        os.makedirs(os.path.join(latex_dir, "figures"), exist_ok=True)
        for f in self.figs:
            shutil.copy(os.path.join(self.fig_dir, f), os.path.join(latex_dir, "figures", f))
        tex = os.path.join(latex_dir, self.name + ".tex")
        with open(tex, "w", encoding="utf8") as fh:
            fh.write(PREAMBLE + "\n".join(self.body) + "\n\\end{document}\n")
        ok = True
        for _ in range(2):
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "--disable-installer", self.name + ".tex"], cwd=latex_dir,
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                ok = False
                errs = [ln for ln in r.stdout.splitlines() if ln.startswith("!") or "Error" in ln][:8]
                print("pdflatex problems:", *errs, sep="\n  ")
                break
        pdf = os.path.join(latex_dir, self.name + ".pdf")
        if os.path.isfile(pdf):
            shutil.copy(pdf, os.path.join(self.out_dir, self.name + ".pdf"))
        print("latex ok" if ok else "latex had errors", tex)
        return tex
