#!/usr/bin/env python3
"""
build_documents.py — Build a tailored resume and cover letter (.docx + .pdf)
from a per-company content file.

The content file is plain JSON written fresh for each job from workHistory.md
and the job description. This script only handles layout; it never adds or
changes wording.

Usage:
  python scripts/build_documents.py Job_Applications/ADIGlobalDistribution/content.json

Formatting follows evaluate_and_generate.md and guardrails.md:
  - Arial, navy body text, blue accents, gray contact/dates
  - Single column, no text boxes, no floating elements, no multi-column sections
  - Right-aligned dates with a tab stop at 6.5" (9360 twips)
"""

import json
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

NAVY = RGBColor(0x1A, 0x1A, 0x2E)
BLUE = RGBColor(0x25, 0x63, 0xEB)
GRAY = RGBColor(0x6B, 0x72, 0x80)
FONT = "Arial"

NAME = "Eric Howes"
CONTACT = "Orem, UT  |  (801) 367-6743  |  howesfamilyhomes@gmail.com  |  linkedin.com/in/eric-howes-utah"
FILE_PREFIX = "Howes_Eric"


# ---------- low-level helpers ----------

def set_base_style(doc, size_pt):
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(size_pt)
    style.font.color.rgb = NAVY
    # Make Arial apply to East Asian text slots too, so Word doesn't swap fonts.
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)


def set_margins(doc, top, bottom, left, right):
    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        section.top_margin = Inches(top)
        section.bottom_margin = Inches(bottom)
        section.left_margin = Inches(left)
        section.right_margin = Inches(right)


def add_run(paragraph, text, size=None, bold=False, italic=False, color=NAVY):
    run = paragraph.add_run(text)
    run.font.name = FONT
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    if size:
        run.font.size = Pt(size)
    return run


def add_bottom_rule(paragraph, color_hex="2563EB", size_eighths=8):
    """Draw a horizontal line under a paragraph using a paragraph border (not a shape)."""
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size_eighths))
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color_hex)
    borders.append(bottom)
    p_pr.append(borders)


def add_header_block(doc, title_line=None):
    name = doc.add_paragraph()
    add_run(name, NAME.upper(), size=20, bold=True)

    if title_line:
        title = doc.add_paragraph()
        add_run(title, title_line, size=11, bold=True, color=BLUE)

    contact = doc.add_paragraph()
    add_run(contact, CONTACT, size=9, color=GRAY)
    contact.paragraph_format.space_after = Pt(6)
    add_bottom_rule(contact)


def add_section_heading(doc, text):
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(10)
    heading.paragraph_format.space_after = Pt(4)
    add_run(heading, text.upper(), size=10.5, bold=True, color=BLUE)
    add_bottom_rule(heading, size_eighths=4)


def add_bullet(doc, text):
    bullet = doc.add_paragraph(style="List Bullet")
    bullet.paragraph_format.space_after = Pt(2)
    bullet.paragraph_format.left_indent = Inches(0.25)
    add_run(bullet, text)


# ---------- resume ----------

def build_resume(content, out_path):
    doc = Document()
    set_base_style(doc, 10)
    set_margins(doc, top=0.5, bottom=0.5, left=0.75, right=0.75)

    add_header_block(doc, content["title_line"])

    add_section_heading(doc, "Professional Summary")
    summary = doc.add_paragraph()
    add_run(summary, content["summary"])

    if content.get("skills"):
        add_section_heading(doc, "Core Skills")
        skills = doc.add_paragraph()
        add_run(skills, "  |  ".join(content["skills"]))

    add_section_heading(doc, "Professional Experience")
    for role in content["roles"]:
        header = doc.add_paragraph()
        header.paragraph_format.space_before = Pt(6)
        header.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
        header.paragraph_format.keep_with_next = True
        add_run(header, role["title"], bold=True)
        add_run(header, "  |  ")
        add_run(header, role["company"], bold=True, color=BLUE)
        add_run(header, "\t" + role["dates"], color=GRAY)

        location = doc.add_paragraph()
        location.paragraph_format.keep_with_next = True
        add_run(location, role["location"], size=9, color=GRAY)

        if role.get("scope"):
            scope = doc.add_paragraph()
            scope.paragraph_format.space_after = Pt(2)
            scope.paragraph_format.keep_with_next = True
            add_run(scope, role["scope"], italic=True)

        for text in role["bullets"]:
            add_bullet(doc, text)

    if content.get("earlier"):
        add_section_heading(doc, "Earlier Experience")
        for text in content["earlier"]:
            add_bullet(doc, text)

    add_section_heading(doc, "Education & Certifications")
    for text in content["education"]:
        line = doc.add_paragraph()
        line.paragraph_format.space_after = Pt(2)
        add_run(line, text)

    doc.save(out_path)


# ---------- cover letter ----------

def build_cover_letter(content, out_path):
    letter = content["cover_letter"]

    doc = Document()
    set_base_style(doc, 11)
    set_margins(doc, top=1, bottom=1, left=1, right=1)

    add_header_block(doc)

    for text in [letter["date"], "", "Hiring Manager", letter["company"], "",
                 "Re: " + letter["role"], ""]:
        line = doc.add_paragraph()
        add_run(line, text)

    for text in letter["paragraphs"]:
        body = doc.add_paragraph()
        body.paragraph_format.space_after = Pt(10)
        body.paragraph_format.line_spacing = 1.1
        add_run(body, text)

    closing = doc.add_paragraph()
    add_run(closing, "Sincerely,")
    signature = doc.add_paragraph()
    signature.paragraph_format.space_before = Pt(6)
    add_run(signature, NAME)

    doc.save(out_path)


# ---------- conversion ----------

def convert_to_pdf(docx_path):
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir",
         str(docx_path.parent), str(docx_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return docx_path.with_suffix(".pdf")


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/build_documents.py <path to content.json>")

    content_path = Path(sys.argv[1])
    content = json.loads(content_path.read_text())
    folder = content_path.parent
    company = content["company_key"]

    resume_path = folder / f"{FILE_PREFIX}_Resume_{company}.docx"
    letter_path = folder / f"{FILE_PREFIX}_CoverLetter_{company}.docx"

    build_resume(content, resume_path)
    build_cover_letter(content, letter_path)

    for path in (resume_path, letter_path):
        pdf = convert_to_pdf(path)
        print(f"Built {path.name} and {pdf.name}")


if __name__ == "__main__":
    main()
