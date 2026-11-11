"""Small helpers shared by every report builder: python-docx document setup and PDF export."""
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

STUDENT_NAME = "Zaid Bin Naveed"
ROLL_NUMBER = "23K-0028"
COURSE = "Agentic AI (AI4015) - Assignment Beta - Fall 2026"


def new_document(title, subtitle=None, margins_cm=2.0, base_pt=11):
    doc = Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Cm(margins_cm)
        section.left_margin = section.right_margin = Cm(margins_cm)
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(base_pt)
    style.paragraph_format.space_after = Pt(4)

    heading = doc.add_heading(title, level=0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta = doc.add_paragraph(f"{STUDENT_NAME}  |  Roll No. {ROLL_NUMBER}\n{COURSE}")
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if subtitle:
        sub = doc.add_paragraph(subtitle)
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return doc


def para(doc, text, bold=False, italic=False, size=None, color=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold, run.italic = bold, italic
    if size:
        run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)
    return p


def rich(doc, parts):
    """Paragraph from (text, style) pairs where style is a subset of 'b', 'i'."""
    p = doc.add_paragraph()
    for text, style in parts:
        run = p.add_run(text)
        run.bold = "b" in style
        run.italic = "i" in style
    return p


def math(doc, text):
    """A working line set in a monospaced font so aligned steps stay readable."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(9.5)
    return p


def bullet(doc, text):
    return doc.add_paragraph(text, style="List Bullet")


def placeholder(doc, text):
    """Visibly marked text the student must replace after running the code themselves."""
    return para(doc, f"[PLACEHOLDER - {text}]", bold=True, color=(0xC0, 0x00, 0x00))


def table(doc, header, rows, font_pt=9, col_widths_cm=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, text in zip(t.rows[0].cells, header):
        cell.text = ""
        run = cell.paragraphs[0].add_run(str(text))
        run.bold = True
        run.font.size = Pt(font_pt)
    for row in rows:
        cells = t.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = ""
            cell.paragraphs[0].add_run(str(value)).font.size = Pt(font_pt)
    if col_widths_cm:
        for row in t.rows:
            for cell, w in zip(row.cells, col_widths_cm):
                cell.width = Cm(w)
    doc.add_paragraph()
    return t


def _soffice():
    found = shutil.which("soffice")
    if found:
        return found
    for base in (r"C:\Program Files\LibreOffice", r"C:\Program Files (x86)\LibreOffice"):
        candidate = Path(base) / "program" / "soffice.exe"
        if candidate.exists():
            return str(candidate)
    return None


def save_with_pdf(doc, docx_path):
    """Save the .docx and export a PDF next to it (LibreOffice if installed, otherwise MS Word via docx2pdf)."""
    docx_path = Path(docx_path)
    doc.save(docx_path)
    soffice = _soffice()
    try:
        if soffice:
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(docx_path.parent), str(docx_path)],
                           check=True, capture_output=True, timeout=300)
        else:
            from docx2pdf import convert
            convert(str(docx_path), str(docx_path.with_suffix(".pdf")))
    except Exception as exc:  # no converter available: keep the .docx
        print(f"PDF export skipped for {docx_path.name}: {exc}")
    return docx_path
