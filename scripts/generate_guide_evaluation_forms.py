"""
BruteShield — Standalone Guide Evaluation Forms Generator
---------------------------------------------------------
Generates standalone DOCX and PDF evaluation and approval sheets for:
 1. Project Report: GUIDE_EVALUATION_PROJECT_REPORT.docx / .pdf
 2. Research Paper: GUIDE_EVALUATION_RESEARCH_PAPER.docx / .pdf
"""

import os
import shutil
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "final-submission")
REPORT_DIR = os.path.join(DOCS_DIR, "project-report")
PAPER_DIR = os.path.join(DOCS_DIR, "research-paper")

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(PAPER_DIR, exist_ok=True)

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

# ---------------------------------------------------------------------------
# 1. PROJECT REPORT EVALUATION FORM
# ---------------------------------------------------------------------------
def generate_report_eval_docx():
    path = os.path.join(REPORT_DIR, "GUIDE_EVALUATION_PROJECT_REPORT.docx")
    doc = Document()
    for s in doc.sections:
        s.page_width = Mm(210)
        s.page_height = Mm(297)
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_inst.add_run("ABES ENGINEERING COLLEGE, GHAZIABAD\nDEPARTMENT OF COMPUTER SCIENCE & ENGINEERING\nB.TECH FINAL YEAR CAPSTONE PROJECT EVALUATION FORM\nACADEMIC YEAR: 2025–2026")
    r.bold = True
    r.font.size = Pt(12)

    p_info = doc.add_paragraph()
    p_info.paragraph_format.space_before = Pt(12)
    p_info.paragraph_format.space_after = Pt(10)
    p_info.add_run("Project Title: ").bold = True
    p_info.add_run("BruteShield: An Adaptive Cybersecurity Defense Engine & SOC Monitoring Platform\n")
    p_info.add_run("Student Team: ").bold = True
    p_info.add_run("[STUDENT INPUT REQUIRED: Student Names & Roll Nos]\n")
    p_info.add_run("Internal Guide: ").bold = True
    p_info.add_run("[STUDENT INPUT REQUIRED: Guide Name & Designation]\n")
    p_info.add_run("Submission Date: ").bold = True
    p_info.add_run("[STUDENT INPUT REQUIRED: DD/MM/YYYY]\n\n")
    r_mand = p_info.add_run("MANDATORY FACULTY CLEARANCE MANDATE: Without the internal supervisor's formal evaluation and endorsement signature, the candidate is NOT permitted to appear for the external viva voce examination.")
    r_mand.bold = True
    r_mand.italic = True

    rubric_data = [
        ("S.No.", "Evaluation Parameter / Criteria", "Max Marks", "Marks Awarded", "Faculty Remarks"),
        ("1", "Technical Depth, Architecture & Implementation (Flask, SQLite WAL, WSGI)", "20", "", ""),
        ("2", "Machine Learning Anomaly Detection & LANL Empirical Benchmark (Days 0–2.31)", "20", "", ""),
        ("3", "Security Hardening, OWASP ASVS Compliance & Test Regression (75/75 Passed)", "20", "", ""),
        ("4", "Project Report Quality, Formatting & Spiral Binding Compliance (>= 30 Pages)", "20", "", ""),
        ("5", "Plagiarism (<10% Similarity) & AI Detection (<20% AI Content) Compliance", "10", "", ""),
        ("6", "Viva Voce Technical Preparedness & Live System Demonstration", "10", "", ""),
        ("", "TOTAL MARKS AWARDED", "100", "", "")
    ]
    t = doc.add_table(rows=len(rubric_data), cols=5)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(rubric_data):
        for c_idx, val in enumerate(row):
            cell = t.rows[r_idx].cells[c_idx]
            cell.paragraphs[0].text = val
            if r_idx == 0:
                cell.paragraphs[0].runs[0].bold = True
                set_cell_background(cell, "CBD5E1")
            elif r_idx == len(rubric_data) - 1:
                cell.paragraphs[0].runs[0].bold = True
                set_cell_background(cell, "DCFCE7")
            elif r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")

    p_rec = doc.add_paragraph()
    p_rec.paragraph_format.space_before = Pt(14)
    p_rec.add_run("GUIDE RECOMMENDATION & CLEARANCE FOR EXTERNAL EXAMINATION:\n").bold = True
    p_rec.add_run("[   ] RECOMMENDED for Final University Oral Examination (Viva Voce)\n")
    p_rec.add_run("[   ] PROVISIONALLY RECOMMENDED (Minor revisions to be verified before viva)\n")
    p_rec.add_run("[   ] NOT RECOMMENDED (Requires substantial technical revision)\n\n")
    p_rec.add_run("Guide Detailed Observations:\n___________________________________________________________________________________________________\n___________________________________________________________________________________________________\n\n")

    sig_t = doc.add_table(rows=2, cols=3)
    sig_t.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_t.rows[0].cells[0].paragraphs[0].text = "______________________\n[STUDENT INPUT REQUIRED]\nInternal Supervisor / Guide\nDate: _______________"
    sig_t.rows[0].cells[1].paragraphs[0].text = "______________________\n[STUDENT INPUT REQUIRED]\nProject Coordinator\nDate: _______________"
    sig_t.rows[0].cells[2].paragraphs[0].text = "______________________\n[STUDENT INPUT REQUIRED]\nHead of Department (CSE)\nDate: _______________"

    doc.save(path)
    print(f"[+] Successfully generated DOCX: {path}")

def generate_report_eval_pdf():
    path = os.path.join(REPORT_DIR, "GUIDE_EVALUATION_PROJECT_REPORT.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('RptTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=12, leading=15, alignment=1, textColor=colors.HexColor("#0f172a"))
    body_style = ParagraphStyle('RptBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor("#1e293b"))

    story = []
    story.append(Paragraph("<b>ABES ENGINEERING COLLEGE, GHAZIABAD<br/>DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING<br/>B.TECH FINAL YEAR CAPSTONE PROJECT EVALUATION FORM (2025–2026)</b>", title_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>Project Title:</b> BruteShield: An Adaptive Cybersecurity Defense Engine & SOC Monitoring Platform<br/>"
        "<b>Student Team:</b> [STUDENT INPUT REQUIRED: Student Names & Roll Nos]<br/>"
        "<b>Internal Guide:</b> [STUDENT INPUT REQUIRED: Guide Name & Designation]<br/>"
        "<b>Submission Date:</b> [STUDENT INPUT REQUIRED: DD/MM/YYYY]<br/><br/>"
        "<b><i>MANDATORY FACULTY CLEARANCE MANDATE: Without the internal supervisor's formal evaluation and endorsement signature, the candidate is NOT permitted to appear for the external viva voce examination.</i></b>",
        body_style
    ))
    story.append(Spacer(1, 10))

    rubric_data = [
        ["S.No.", "Evaluation Parameter / Criteria", "Max Marks", "Marks Awarded", "Faculty Remarks"],
        ["1", "Technical Depth, Architecture & Implementation Completeness", "20", "", ""],
        ["2", "Machine Learning Pipeline & LANL Empirical Benchmark (Days 0–2.31)", "20", "", ""],
        ["3", "Security Hardening, OWASP ASVS Compliance & Test Regression (75/75)", "20", "", ""],
        ["4", "Project Report Quality, Formatting & Spiral Binding Compliance (>= 30 Pgs)", "20", "", ""],
        ["5", "Plagiarism (<10% Similarity) & AI Detection (<20% AI Content) Compliance", "10", "", ""],
        ["6", "Viva Voce Technical Preparedness & Live System Demonstration", "10", "", ""],
        ["", "TOTAL MARKS AWARDED", "100", "", ""]
    ]
    t = Table(rubric_data, colWidths=[30, 240, 55, 65, 95])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#dcfce7")),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "<b>GUIDE RECOMMENDATION & CLEARANCE FOR EXTERNAL EXAMINATION:</b><br/>"
        "[   ] <b>RECOMMENDED</b> for Final University Oral Examination (Viva Voce)<br/>"
        "[   ] <b>PROVISIONALLY RECOMMENDED</b> (Minor revisions to be verified before viva)<br/>"
        "[   ] <b>NOT RECOMMENDED</b> (Requires substantial technical revision)<br/><br/>"
        "Guide Observations: ________________________________________________________________________________<br/>"
        "___________________________________________________________________________________________________",
        body_style
    ))
    story.append(Spacer(1, 25))

    sig_data = [
        ["______________________\n[STUDENT INPUT REQUIRED]\nInternal Supervisor / Guide\nDate: _______________",
         "______________________\n[STUDENT INPUT REQUIRED]\nProject Coordinator\nDate: _______________",
         "______________________\n[STUDENT INPUT REQUIRED]\nHead of Department (CSE)\nDate: _______________"]
    ]
    t_sig = Table(sig_data, colWidths=[160, 160, 160])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_sig)

    doc.build(story)
    print(f"[+] Successfully generated PDF: {path}")


# ---------------------------------------------------------------------------
# 2. RESEARCH PAPER EVALUATION FORM
# ---------------------------------------------------------------------------
def generate_paper_eval_docx():
    path = os.path.join(PAPER_DIR, "GUIDE_EVALUATION_RESEARCH_PAPER.docx")
    doc = Document()
    for s in doc.sections:
        s.page_width = Mm(210)
        s.page_height = Mm(297)
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_inst.add_run("ABES ENGINEERING COLLEGE, GHAZIABAD\nDEPARTMENT OF COMPUTER SCIENCE & ENGINEERING\nRESEARCH PAPER EVALUATION & ENDORSEMENT FORM\nACADEMIC YEAR: 2025–2026")
    r.bold = True
    r.font.size = Pt(12)

    p_info = doc.add_paragraph()
    p_info.paragraph_format.space_before = Pt(12)
    p_info.paragraph_format.space_after = Pt(10)
    p_info.add_run("Paper Title: ").bold = True
    p_info.add_run("BruteShield: A Modular Machine Learning-Based Framework for Authentication Attack Detection and Adaptive Security Monitoring\n")
    p_info.add_run("Student Authors: ").bold = True
    p_info.add_run("[STUDENT INPUT REQUIRED: Student Names & Roll Nos]\n")
    p_info.add_run("Research Supervisor: ").bold = True
    p_info.add_run("[STUDENT INPUT REQUIRED: Guide Name & Designation]\n")
    p_info.add_run("Review Date: ").bold = True
    p_info.add_run("[STUDENT INPUT REQUIRED: DD/MM/YYYY]\n\n")
    r_mand = p_info.add_run("MANDATORY SUPERVISOR ENDORSEMENT: Without the supervisor's formal review and signature, this paper draft cannot be submitted for peer-reviewed publication or presented at conference venues.")
    r_mand.bold = True
    r_mand.italic = True

    rubric_data = [
        ("S.No.", "Evaluation Parameter / Research Quality Criteria", "Max Marks", "Marks Awarded", "Supervisor Remarks"),
        ("1", "Technical Novelty & Related Work Synthesis (Kent, Liu, Schölkopf)", "20", "", ""),
        ("2", "Mathematical Rigor (Entropy, Isolation Forest c(n), GHASH GF(2^128))", "20", "", ""),
        ("3", "Empirical Evaluation & LANL Cyber1 Slice Ingestion Integrity", "20", "", ""),
        ("4", "Critical Discussion (Base Rate Fallacy, Graduated Friction Justification)", "20", "", ""),
        ("5", "Plagiarism (<10% Similarity) & AI Detection (<20% AI Content) Compliance", "10", "", ""),
        ("6", "IEEE Formatting, Citation Standards & Academic Writing Quality", "10", "", ""),
        ("", "TOTAL MARKS AWARDED", "100", "", "")
    ]
    t = doc.add_table(rows=len(rubric_data), cols=5)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(rubric_data):
        for c_idx, val in enumerate(row):
            cell = t.rows[r_idx].cells[c_idx]
            cell.paragraphs[0].text = val
            if r_idx == 0:
                cell.paragraphs[0].runs[0].bold = True
                set_cell_background(cell, "CBD5E1")
            elif r_idx == len(rubric_data) - 1:
                cell.paragraphs[0].runs[0].bold = True
                set_cell_background(cell, "DCFCE7")
            elif r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")

    p_rec = doc.add_paragraph()
    p_rec.paragraph_format.space_before = Pt(14)
    p_rec.add_run("SUPERVISOR RECOMMENDATION & PUBLICATION CLEARANCE:\n").bold = True
    p_rec.add_run("[   ] RECOMMENDED for Peer-Reviewed Conference / Journal Submission\n")
    p_rec.add_run("[   ] APPROVED as Institutional B.Tech Capstone Research Draft\n")
    p_rec.add_run("[   ] REVISION REQUIRED prior to external submission\n\n")
    p_rec.add_run("Supervisor Detailed Remarks:\n___________________________________________________________________________________________________\n___________________________________________________________________________________________________\n\n")

    sig_p = doc.add_paragraph()
    sig_p.paragraph_format.space_before = Pt(20)
    sig_p.add_run("Supervisor Signature: _________________________________          Date: ________________________\n")
    sig_p.add_run("Supervisor Name & Seal: [STUDENT INPUT REQUIRED]                 Department: CSE, ABES-EC")

    doc.save(path)
    print(f"[+] Successfully generated DOCX: {path}")

def generate_paper_eval_pdf():
    path = os.path.join(PAPER_DIR, "GUIDE_EVALUATION_RESEARCH_PAPER.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('PapTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=12, leading=15, alignment=1, textColor=colors.HexColor("#0f172a"))
    body_style = ParagraphStyle('PapBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor("#1e293b"))

    story = []
    story.append(Paragraph("<b>ABES ENGINEERING COLLEGE, GHAZIABAD<br/>DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING<br/>RESEARCH PAPER EVALUATION & ENDORSEMENT FORM (2025–2026)</b>", title_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>Paper Title:</b> BruteShield: A Modular Machine Learning-Based Framework for Authentication Attack Detection and Adaptive Security Monitoring<br/>"
        "<b>Student Authors:</b> [STUDENT INPUT REQUIRED: Student Names & Roll Nos]<br/>"
        "<b>Research Supervisor:</b> [STUDENT INPUT REQUIRED: Guide Name & Designation]<br/>"
        "<b>Review Date:</b> [STUDENT INPUT REQUIRED: DD/MM/YYYY]<br/><br/>"
        "<b><i>MANDATORY SUPERVISOR ENDORSEMENT: Without the supervisor's formal review and signature, this paper draft cannot be submitted for peer-reviewed publication or presented at conference venues.</i></b>",
        body_style
    ))
    story.append(Spacer(1, 10))

    rubric_data = [
        ["S.No.", "Evaluation Parameter / Research Quality Criteria", "Max Marks", "Marks Awarded", "Supervisor Remarks"],
        ["1", "Technical Novelty & Related Work Synthesis (Kent, Liu, Schölkopf)", "20", "", ""],
        ["2", "Mathematical Rigor (Entropy, Isolation Forest c(n), GHASH GF(2^128))", "20", "", ""],
        ["3", "Empirical Evaluation & LANL Cyber1 Slice Ingestion Integrity", "20", "", ""],
        ["4", "Critical Discussion (Base Rate Fallacy, Graduated Friction)", "20", "", ""],
        ["5", "Plagiarism (<10% Similarity) & AI Detection (<20% AI Content) Compliance", "10", "", ""],
        ["6", "IEEE Formatting, Citation Standards & Academic Writing Quality", "10", "", ""],
        ["", "TOTAL MARKS AWARDED", "100", "", ""]
    ]
    t = Table(rubric_data, colWidths=[30, 240, 55, 65, 95])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#dcfce7")),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "<b>SUPERVISOR RECOMMENDATION & PUBLICATION CLEARANCE:</b><br/>"
        "[   ] <b>RECOMMENDED</b> for Peer-Reviewed Conference / Journal Submission<br/>"
        "[   ] <b>APPROVED</b> as Institutional B.Tech Capstone Research Draft<br/>"
        "[   ] <b>REVISION REQUIRED</b> prior to external submission<br/><br/>"
        "Supervisor Remarks: ________________________________________________________________________________<br/>"
        "___________________________________________________________________________________________________",
        body_style
    ))
    story.append(Spacer(1, 25))

    story.append(Paragraph(
        "Supervisor Signature: _________________________________          Date: ________________________<br/>"
        "Supervisor Name & Seal: [STUDENT INPUT REQUIRED]                 Department: CSE, ABES-EC",
        body_style
    ))

    doc.build(story)
    print(f"[+] Successfully generated PDF: {path}")

if __name__ == "__main__":
    generate_report_eval_docx()
    generate_report_eval_pdf()
    generate_paper_eval_docx()
    generate_paper_eval_pdf()
