"""Small helpers to write a Word report (python-docx). Same layout as the M3 report builder."""
import os
import re

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


class Report:
    def __init__(self, fig_dir, font="Times New Roman", size=11):
        self.doc = Document()
        self.fig_dir = fig_dir
        s = self.doc.sections[0]
        s.page_width, s.page_height = Inches(8.5), Inches(11)
        s.left_margin = s.right_margin = Inches(1.0)
        s.top_margin = s.bottom_margin = Inches(0.9)
        st = self.doc.styles["Normal"]
        st.font.name, st.font.size = font, Pt(size)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), font)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.line_spacing = 1.0
        self.font = font
        self._add_page_number()

    def _add_page_number(self):
        p = self.doc.sections[0].footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run()
        for t, txt in (("begin", None), (None, "PAGE"), ("end", None)):
            if t:
                e = OxmlElement("w:fldChar")
                e.set(qn("w:fldCharType"), t)
            else:
                e = OxmlElement("w:instrText")
                e.set(qn("xml:space"), "preserve")
                e.text = txt
            r._r.append(e)

    def run(self, p, text, bold=False, italic=False, size=None, sub=False, sup=False):
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        r.font.name = self.font
        r._element.rPr.rFonts.set(qn("w:eastAsia"), self.font)
        if size:
            r.font.size = Pt(size)
        r.font.subscript, r.font.superscript = sub, sup
        return r

    def rich(self, p, text, size=None):
        """**bold**, __italic__, _{sub}, ^{sup} markers."""
        for tok in re.split(r"(\*\*.+?\*\*|__.+?__|_\{.+?\}|\^\{.+?\})", text):
            if tok.startswith("**"):
                self.run(p, tok[2:-2], bold=True, size=size)
            elif tok.startswith("__"):
                self.run(p, tok[2:-2], italic=True, size=size)
            elif tok.startswith("_{"):
                self.run(p, tok[2:-1], size=size, sub=True)
            elif tok.startswith("^{"):
                self.run(p, tok[2:-1], size=size, sup=True)
            else:
                self.run(p, tok, size=size)

    def para(self, text, align="j", after=6, size=None, keep=False):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        p.alignment = {"j": WD_ALIGN_PARAGRAPH.JUSTIFY, "c": WD_ALIGN_PARAGRAPH.CENTER, "l": WD_ALIGN_PARAGRAPH.LEFT}[align]
        p.paragraph_format.keep_with_next = keep
        self.rich(p, text, size)
        return p

    def title(self, text, size=18):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(4)
        self.run(p, text, bold=True, size=size)

    def h1(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(12), Pt(5)
        p.paragraph_format.keep_with_next = True
        self.run(p, text, bold=True, size=14)

    def h2(self, text):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(6), Pt(3)
        p.paragraph_format.keep_with_next = True
        self.run(p, text, bold=True, size=11.5)

    def bullets(self, items):
        for it in items:
            p = self.doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.2)
            p.paragraph_format.space_after = Pt(3)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            self.run(p, "•  ")
            self.rich(p, it)

    def eq(self, text, label=None):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(6)
        self.rich(p, text + (f"        ({label})" if label else ""))

    def pagebreak(self):
        self.doc.add_page_break()

    @staticmethod
    def _shade(cell, color):
        tcPr = cell._element.get_or_add_tcPr()
        s = OxmlElement("w:shd")
        s.set(qn("w:val"), "clear")
        s.set(qn("w:color"), "auto")
        s.set(qn("w:fill"), color)
        tcPr.append(s)

    @staticmethod
    def _borders(tbl):
        b = OxmlElement("w:tblBorders")
        for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
            x = OxmlElement(f"w:{e}")
            x.set(qn("w:val"), "single")
            x.set(qn("w:sz"), "4")
            x.set(qn("w:space"), "0")
            x.set(qn("w:color"), "444444")
            b.append(x)
        tbl._element.tblPr.append(b)

    def table(self, caption, header, rows, widths, size=8.5, note=None, bold_first=False):
        c = self.doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.space_after = Pt(3)
        c.paragraph_format.keep_with_next = True
        self.rich(c, caption, size=10)
        t = self.doc.add_table(rows=1, cols=len(header))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        self._borders(t)
        for i, h in enumerate(header):
            cell = t.rows[0].cells[i]
            cell.width = Inches(widths[i])
            self._shade(cell, "EDEDED")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            self.run(p, h, bold=True, size=size)
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r):
                cells[i].width = Inches(widths[i])
                p = cells[i].paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                self.run(p, str(v), bold=(bold_first and i == 0), size=size)
        for row in t.rows:
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(2)
        if note:
            n = self.doc.add_paragraph()
            n.paragraph_format.space_after = Pt(6)
            self.rich(n, note, size=9)

    def figure(self, fname, caption, width=6.3):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(os.path.join(self.fig_dir, fname), width=Inches(width))
        c = self.doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.space_after = Pt(8)
        self.rich(c, caption, size=10)

    def save(self, path):
        self.doc.save(path)
