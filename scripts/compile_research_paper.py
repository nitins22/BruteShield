"""
BruteShield — Academic Research Paper Generator (Full Academic Draft Edition)
------------------------------------------------------------------------------
Compiles BRUTESHIELD_RESEARCH_PAPER.docx and BRUTESHIELD_RESEARCH_PAPER.pdf
following standard IEEE transactions / conference academic paper structure:
 - Prominent academic draft status disclosure
 - Full mathematical derivations (Entropy, Isolation Forest c(n), GHASH, k-anonymity)
 - Architectural figures, tables, and LANL empirical benchmark results
 - Plagiarism & AI-Plagiarism report insertion placeholders (Appendices A & B)
 - Guide Evaluation & Signature Endorsement Form (Appendix C)
"""

import os
import sys
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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "final-submission")
PAPER_SUBDIR = os.path.join(DOCS_DIR, "research-paper")
DIAG_DIR = os.path.join(DOCS_DIR, "diagrams")

DOCX_OUT = os.path.join(ROOT_DIR, "BRUTESHIELD_RESEARCH_PAPER.docx")
PDF_OUT = os.path.join(ROOT_DIR, "BRUTESHIELD_RESEARCH_PAPER.pdf")

# Running Header/Footer canvas for Paper
class PaperNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(PaperNumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super(PaperNumberedCanvas, self).showPage()
        super(PaperNumberedCanvas, self).save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header
        self.drawString(54, 842 - 36, "RESEARCH PAPER DRAFT — BruteShield: Adaptive Anomaly Detection & Security Monitoring")
        self.drawRightString(595 - 54, 842 - 36, "IEEE Computer Society Format")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 842 - 42, 595 - 54, 842 - 42)

        # Running Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(595 - 54, 34, page_text)
        self.drawString(54, 34, "B.Tech CSE Capstone Research Draft | ABES Engineering College, Ghaziabad")
        self.line(54, 46, 595 - 54, 46)

        self.restoreState()


def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)


REFERENCES = [
    "[1] A. D. Kent, 'Comprehensive, Multi-Source Cyber-Security Events,' Los Alamos National Laboratory Technical Report, 2015. DOI: 10.17021/1179829.",
    "[2] F. T. Liu, K. M. Ting, and Z.-H. Zhou, 'Isolation Forest,' in Proc. Eighth IEEE Int. Conf. Data Mining (ICDM), Pisa, Italy, 2008, pp. 413–422. DOI: 10.1109/ICDM.2008.17.",
    "[3] B. Schölkopf, J. C. Platt, J. Shawe-Taylor, A. J. Smola, and R. C. Williamson, 'Estimating the Support of a High-Dimensional Distribution,' Neural Computation, vol. 13, no. 7, pp. 1443–1471, 2001. DOI: 10.1162/089976601750541816.",
    "[4] L. Breiman, 'Random Forests,' Machine Learning, vol. 45, no. 1, pp. 5–32, 2001. DOI: 10.1023/A:1010933404324.",
    "[5] C. E. Shannon, 'A Mathematical Theory of Communication,' Bell System Technical Journal, vol. 27, no. 3, pp. 379–423, 1948. DOI: 10.1002/j.1538-7305.1948.tb01338.x.",
    "[6] D. A. McGrew and J. Viega, 'The Galois/Counter Mode of Operation (GCM),' NIST Special Publication 800-38D, National Institute of Standards and Technology, Gaithersburg, MD, 2007. DOI: 10.6028/NIST.SP.800-38D.",
    "[7] C. Dwork, 'Differential Privacy,' in Automata, Languages and Programming (ICALP), Lecture Notes in Computer Science, vol. 4052, Springer, Berlin, Heidelberg, 2006, pp. 1–12. DOI: 10.1007/11787006_1.",
    "[8] J. E. Hopcroft and R. M. Karp, 'An n^(5/2) algorithm for maximum matchings in bipartite graphs,' SIAM Journal on Computing, vol. 2, no. 4, pp. 225–231, 1973. DOI: 10.1137/0202019.",
    "[9] T. Hunt, 'Have I Been Pwned: Pwned Passwords API v2 (k-Anonymity Mathematical Model),' Cloudflare Security Research, 2018. [Online]. Available: https://www.troyhunt.com/ive-just-launched-pwned-passwords-v2/.",
    "[10] OWASP Foundation, 'Application Security Verification Standard (ASVS) Version 5.0,' OWASP Community Standards, 2024. [Online]. Available: https://owasp.org/www-project-application-security-verification-standard/.",
    "[11] National Institute of Standards and Technology (NIST), 'Digital Identity Guidelines: Authentication and Lifecycle Management,' NIST SP 800-63B, 2020. DOI: 10.6028/NIST.SP.800-63b.",
    "[12] J. Viega, 'Cloud Security and Privacy: An Enterprise Perspective,' IEEE Security & Privacy, vol. 7, no. 4, pp. 80–84, 2009. DOI: 10.1109/MSP.2009.96."
]


# ===========================================================================
# 1. GENERATE RESEARCH PAPER DOCX
# ===========================================================================
def generate_paper_docx():
    print("[*] Generating BRUTESHIELD_RESEARCH_PAPER.docx...")
    doc = Document()

    for s in doc.sections:
        s.page_width = Mm(210)
        s.page_height = Mm(297)
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    def add_p(text, space_after=6, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.LEFT, size=10):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = 'Times New Roman'
        run.font.size = Pt(size)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(15, 23, 42)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.italic = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(30, 41, 59)
        return p

    # Status Banner
    p_stat = doc.add_paragraph()
    p_stat.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_stat.paragraph_format.space_after = Pt(8)
    r_stat = p_stat.add_run("RESEARCH PAPER DRAFT — NOT YET SUBMITTED TO OR ACCEPTED BY ANY PEER-REVIEWED JOURNAL OR CONFERENCE\nPrepared for Academic Evaluation & B.Tech Capstone Project Defence (Academic Year 2025–2026)")
    r_stat.font.name = 'Times New Roman'
    r_stat.font.size = Pt(9)
    r_stat.font.bold = True
    r_stat.font.color.rgb = RGBColor(185, 28, 28)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("BruteShield: A Modular Machine Learning-Based Framework for Authentication Attack Detection and Adaptive Security Monitoring")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(16)
    r_title.bold = True

    # Authors
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_after = Pt(12)
    r_auth = p_auth.add_run(
        "[STUDENT INPUT REQUIRED: Student Name 1]*, [STUDENT INPUT REQUIRED: Student Name 2]*, [STUDENT INPUT REQUIRED: Guide Name]†\n"
        "*Department of Computer Science & Engineering, ABES Engineering College, Ghaziabad, India\n"
        "†Department of Computer Science & Engineering, ABES Engineering College, Ghaziabad, India\n"
        "Email: [STUDENT INPUT REQUIRED: student@example.edu.in]"
    )
    r_auth.font.name = 'Times New Roman'
    r_auth.font.size = Pt(9.5)

    # Abstract Box
    p_abs = doc.add_paragraph()
    p_abs.paragraph_format.space_after = Pt(6)
    r_lbl = p_abs.add_run("Abstract—")
    r_lbl.bold = True
    r_lbl.italic = True
    r_lbl.font.name = 'Times New Roman'
    r_abs = p_abs.add_run(
        "Authentication mechanisms form the foundational security perimeter of modern web applications, yet remain severely vulnerable "
        "to automated credential stuffing, distributed brute-force, and low-and-slow password spraying attacks. Traditional threshold-based counters "
        "(e.g., locking an account after five consecutive failures within 60 seconds) are easily circumvented by adversaries who introduce deliberate "
        "inter-attempt delays or distribute attempts horizontally across multiple user identities. In this paper, we present BruteShield, a modular application-layer "
        "security framework combining real-time behavioral feature extraction with unsupervised machine learning anomaly detection. BruteShield extracts a "
        "six-dimensional statistical feature vector across a 900-second sliding observation window, evaluating attempt frequency, target diversity, and temporal spacing. "
        "An unsupervised Isolation Forest classifier scores incoming authentication events, mapping borderline anomaly scores to arithmetic CAPTCHA friction challenges "
        "before escalating confirmed repeat offenders through an adaptive cooldown ladder (60s to 3600s). The framework incorporates client-side Shannon entropy calculation, "
        "Have I Been Pwned (HIBP) k-anonymity breach verification, an authenticated zero-knowledge AES-256-GCM credential vault, and an unauthenticated honeypot trap with credential masking. "
        "Evaluated on synthetic benchmark scenarios and a verified 2.31-day empirical slice (21.26 million authentication events) of the Los Alamos National Laboratory (LANL) "
        "cybersecurity dataset, BruteShield detected 100% of stealthy low-and-slow proxy attacks that completely bypassed conventional Fail2ban threshold counters. "
        "We discuss the critical trade-offs between precision and ROC-AUC under extreme class imbalance and analyze the operational necessity of graduated friction responses."
    )
    r_abs.font.name = 'Times New Roman'
    r_abs.font.size = Pt(9)

    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.space_after = Pt(14)
    r_kw_lbl = p_kw.add_run("Keywords—")
    r_kw_lbl.bold = True
    r_kw_lbl.italic = True
    r_kw_lbl.font.name = 'Times New Roman'
    r_kw = p_kw.add_run("Authentication Security, Brute-Force Detection, Isolation Forest, Sliding-Window Telemetry, k-Anonymity, AES-256-GCM, LANL Cyber Dataset, Base Rate Fallacy.")
    r_kw.font.name = 'Times New Roman'
    r_kw.font.size = Pt(9)

    # Section I
    add_h1("I. INTRODUCTION")
    add_p(
        "Web application authentication interfaces represent the primary defense boundary of modern enterprise infrastructure, yet remain the most frequently "
        "attacked surface in cyberspace. Automated botnets, residential proxy pools, and leaked credential databases allow adversaries to execute large-scale attacks "
        "with minimal overhead. Authentication attacks predominantly fall into three categories:\n"
        "• High-Frequency Brute Force: Rapid submission of password guesses targeting a single account.\n"
        "• Credential Stuffing: Automated replay of leaked username/password combinations across multiple unrelated services.\n"
        "• Password Spraying & Low-and-Slow Attacks: Testing a single high-probability password horizontally across thousands of accounts, or spacing attempts "
        "by several minutes to stay beneath per-account and per-IP lockout thresholds.\n\n"
        "Traditional perimeter defenses (such as Fail2ban or simple login failure counters) rely on static rules: e.g., if 5 failures occur in 60 seconds, block the source IP. "
        "This approach fails against adversaries who space requests at 70-second intervals or spray across multiple accounts. Furthermore, enforcing account lockouts "
        "creates a severe Denial-of-Service (DoS) vulnerability: an unauthenticated attacker can lock out legitimate users simply by submitting incorrect passwords.\n\n"
        "To overcome these limitations, we present BruteShield, an application-layer defense engine and live Security Operations Center (SOC) monitoring platform. "
        "BruteShield models authentication traffic as a continuous stream, extracting a 6-dimensional temporal feature vector across an indexed 900-second sliding window. "
        "Traffic is scored using an unsupervised Isolation Forest model. Borderline anomalies are routed to arithmetic CAPTCHA challenges, while confirmed malicious attacks "
        "trigger an exponential IP cooldown ladder (60s -> 300s -> 900s -> 3600s)."
    )

    # Section II
    add_h1("II. RELATED WORK & PROBLEM FORMULATION")
    add_p(
        "Authentication security has traditionally relied on signature and threshold rules. Liu et al. [2] introduced Isolation Forest, proving that anomalies "
        "in multi-dimensional space are naturally isolated closer to the root in random binary search trees with linear time complexity O(n). Schölkopf et al. [3] "
        "developed One-Class Support Vector Machines (OC-SVM) for boundary estimation, though with quadratic computational complexity. In cryptographic storage, "
        "McGrew and Viega [6] specified Galois/Counter Mode (AES-GCM), combining CTR confidentiality with GHASH integrity over GF(2^128). Hunt [9] demonstrated "
        "k-anonymity breach lookup using SHA-1 prefix bucketing. In cybersecurity dataset benchmarking, Kent [1] published the multi-source LANL Cyber1 dataset.\n\n"
        "Let authentication requests be defined as a_i = (t_i, ip_i, u_i, s_i) where t_i in R^+, ip_i is IP, u_i is username, and s_i in {0,1} is success/failure. "
        "While conventional threshold counters evaluate scalar counts over narrow windows W = 60s, BruteShield maps traffic history into a vector space Psi: A^k -> R^6 "
        "over W_obs = 900s, computing total attempts, failure count, distinct usernames, mean inter-arrival gap, minimum burst gap, and failure ratio."
    )

    # Section III
    add_h1("III. PROPOSED BRUTESHIELD ARCHITECTURE")
    add_p(
        "BruteShield operates as a defense-in-depth architecture across five tiers:\n"
        "1. Client Layer: Real-time Shannon entropy calculation (H(s) = -sum p(c) log2 p(c)), enforcing E_total >= 45 bits, and dynamic arithmetic CAPTCHAs.\n"
        "2. Gateway & Proxy: Nginx terminating TLS 1.3, enforcing perimeter rate limits and injecting strict security headers.\n"
        "3. WSGI Application Layer: Production Waitress/Gunicorn WSGI executing Flask application factory with session fixation protection.\n"
        "4. ML Anomaly Intelligence: Sliding-window feature extractor, scikit-learn Isolation Forest model, and cooldown escalation state machine.\n"
        "5. Persistence Storage: SQLite relational database operating with Write-Ahead Logging (WAL) and exclusive file locking."
    )
    # Embed Fig 1
    fig1_path = os.path.join(DIAG_DIR, "fig1_system_architecture.png")
    if os.path.exists(fig1_path):
        doc.add_picture(fig1_path, width=Inches(6.0))
        p_c = doc.add_paragraph("Fig. 1. BruteShield modular system architecture and defense-in-depth topology.")
        p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_c.runs[0].font.name = 'Times New Roman'
        p_c.runs[0].font.size = Pt(8.5)
        p_c.runs[0].font.italic = True

    # Section IV
    add_h1("IV. MATHEMATICAL FORMULATION & FEATURE ENGINEERING")
    add_p(
        "A. Six-Dimensional Sliding-Window Feature Vector\n"
        "For an incoming attempt from IP address i at time t_curr, BruteShield queries all audit records within [t_curr - 900, t_curr]. The feature vector is:\n"
        "    X = [N_tot, N_fail, U_dist, Delta_t_avg, Delta_t_min, R_fail]\n"
        "where N_tot is total attempts, N_fail is failed attempts, U_dist is unique usernames targeted, Delta_t_avg is mean inter-arrival interval, "
        "Delta_t_min is minimum burst interval, and R_fail = N_fail / N_tot.\n\n"
        "B. Isolation Forest Anomaly Scoring\n"
        "For dataset size n, average binary search tree path length is c(n) = 2*(ln(n-1) + 0.5772156649) - (2*(n-1)/n). Anomaly score is defined as:\n"
        "    s(X, n) = 2^{ - (E(h(X)) / c(n)) }\n"
        "where E(h(X)) is expected path depth across trees. s -> 1 indicates severe anomaly; s ~ 0.5 indicates borderline traffic.\n\n"
        "C. Authenticated Galois/Counter Mode (AES-256-GCM) Cryptography\n"
        "User credentials stored in the vault are protected with AES-256-GCM AEAD encryption: C_i = P_i (+) CIPH_K(IV || cnt_i). "
        "Authentication is computed via universal polynomial hashing over GF(2^128): GHASH_H(X_1, ..., X_m) = sum X_j * H^{m-j+1}. "
        "Any byte tampering causes immediate InvalidTag rejection before plaintext disclosure."
    )

    # Section V
    add_h1("V. EMPIRICAL RESULTS & BENCHMARK EVALUATION")
    add_p(
        "A. Synthetic Attack Simulation Benchmark (Phase 1 Baseline)\n"
        "In controlled experiments with 300 normal users and 190 simulated attack vectors (fast brute force, stuffing, and low-and-slow pacing), "
        "BruteShield's ML model achieved 96.5% overall accuracy, 94.8% precision, and 96.3% recall, vs. 83.5% accuracy and 57.9% recall for Fail2ban. "
        "On low-and-slow attacks (12–60s delay), BruteShield caught 100% of attack bursts while Fail2ban caught 0%.\n\n"
        "B. LANL Enterprise Cybersecurity Dataset Benchmark (Phase 2B)\n"
        "To test temporal generalization under enterprise conditions, BruteShield was evaluated on the LANL Cyber1 dataset [1]. "
        "We parsed the verified Days 0 to 2.31 empirical slice (199,687s), filtering 16,050,924 LogOff records and retaining 21,255,459 authentication records. "
        "10 ground-truth red-team attacks occurred within this slice, matched 1-to-1 via bipartite matching (+0 Hopcroft-Karp discrepancy). "
        "Table I details performance across 30,137 evaluation windows."
    )

    # Table I
    t_lanl = doc.add_table(rows=4, cols=11)
    t_lanl.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_headers = ["Model", "TP", "FP", "FN", "TN", "Prec", "Recall", "F1", "FPR", "AP", "ROC-AUC"]
    for c, h in enumerate(table_headers):
        t_lanl.rows[0].cells[c].paragraphs[0].text = h
        t_lanl.rows[0].cells[c].paragraphs[0].runs[0].font.bold = True
        t_lanl.rows[0].cells[c].paragraphs[0].runs[0].font.name = 'Times New Roman'
        t_lanl.rows[0].cells[c].paragraphs[0].runs[0].font.size = Pt(8)
        set_cell_background(t_lanl.rows[0].cells[c], "CBD5E1")

    lanl_rows = [
        ["Isolation Forest", "3", "2,134", "1", "27,999", "0.0014", "0.7500", "0.0028", "0.0708", "0.0023", "0.8026"],
        ["One-Class SVM", "2", "436", "2", "29,697", "0.0046", "0.5000", "0.0090", "0.0145", "0.0036", "0.9382"],
        ["Random Forest", "1", "3,166", "3", "26,967", "0.0003", "0.2500", "0.0006", "0.1051", "0.0008", "0.8967"]
    ]
    for r_idx, row_vals in enumerate(lanl_rows, 1):
        for c_idx, val in enumerate(row_vals):
            cell = t_lanl.rows[r_idx].cells[c_idx]
            cell.paragraphs[0].text = val
            cell.paragraphs[0].runs[0].font.name = 'Times New Roman'
            cell.paragraphs[0].runs[0].font.size = Pt(8)
            if r_idx % 2 == 1:
                set_cell_background(cell, "F1F5F9")

    p_tbl_cap = doc.add_paragraph("TABLE I. LANL EXPERIMENT A: COMPARATIVE PERFORMANCE ON DAYS 0–2.31 (30,137 WINDOWS)")
    p_tbl_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tbl_cap.runs[0].font.name = 'Times New Roman'
    p_tbl_cap.runs[0].font.size = Pt(8)
    p_tbl_cap.runs[0].font.bold = True

    # Section VI
    add_h1("VI. CRITICAL DISCUSSION: THE BASE RATE FALLACY & GRADUATED FRICTION")
    add_p(
        "A vital academic insight from Table I is the sharp divergence between ROC-AUC and Precision. OC-SVM achieved 0.9382 ROC-AUC and Isolation Forest "
        "achieved 0.8026, yet precision was below 0.5% (0.0046 and 0.0014). This is the classic 'Base Rate Fallacy' caused by extreme class imbalance: "
        "with only 4 positive attack windows out of 30,137 total windows (0.013% prevalence), even an outstanding FPR of 1.45% produces 436 false alarms against 2 true positives.\n\n"
        "In a real-world enterprise setting, an automated defense that immediately terminates accounts or IPs upon anomaly detection would generate 436 wrongful lockouts. "
        "This empirical reality justifies BruteShield's graduated friction ladder: routing borderline scores into arithmetic CAPTCHA challenges preserves legitimate "
        "human access while completely halting automated bots."
    )

    # Section VII
    add_h1("VII. THREATS TO VALIDITY & LIMITATIONS")
    add_p(
        "1. Dataset Scope: Due to computational constraints, empirical benchmarking was performed strictly on the Days 0 to 2.31 slice (199,687s). "
        "Full 58-day evaluation remains future work.\n"
        "2. Telemetry Modality: LANL records enterprise Active Directory Kerberos/NTLM authentication, which lacks web HTTP cookie dynamics.\n"
        "3. Storage Concurrency: SQLite WAL mode provides excellent single-node concurrency but serializes writes; distributed deployments require PostgreSQL/Redis."
    )

    # Section VIII
    add_h1("VIII. CONCLUSION & FUTURE WORK")
    add_p(
        "BruteShield demonstrates that lightweight temporal sliding-window feature engineering paired with unsupervised Isolation Forest modeling provides an effective, "
        "defensible defense against automated authentication threats, catching 100% of low-and-slow proxy attacks that evaded Fail2ban. The system is validated "
        "with 75 automated tests, zero Bandit SAST flaws, and zero dependency CVEs. Future work will explore deep recurrent sequence models (LSTM) and distributed cloud clusters."
    )

    # References
    add_h1("REFERENCES")
    for r in REFERENCES:
        p_ref = doc.add_paragraph(r)
        p_ref.paragraph_format.space_after = Pt(3)
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.runs[0].font.name = 'Times New Roman'
        p_ref.runs[0].font.size = Pt(8.5)
    doc.add_page_break()

    # Appendices
    add_h1("APPENDIX A: RESEARCH PAPER SIMILARITY / PLAGIARISM REPORT (FIRST PAGE)").alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_p(
        "====================================================================================================\n"
        "MANDATORY UNIVERSITY SUBMISSION REQUIREMENT:\n"
        "ATTACH FIRST PAGE OF OFFICIAL RESEARCH PAPER SIMILARITY REPORT HERE\n"
        "====================================================================================================\n\n"
        "In compliance with Dr. A.P.J. Abdul Kalam Technical University (AKTU) / ABES Engineering College submission guidelines, "
        "the research paper draft must undergo formal computerized similarity screening.\n\n"
        "INSTITUTIONAL SIMILARITY SPECIFICATIONS:\n"
        "• Maximum Permissible Similarity Index: Less than 10% (< 10%)\n"
        "• Approved Verification Platforms: Turnitin / iThenticate / DrillBit\n"
        "• Document Scanned: BRUTESHIELD_RESEARCH_PAPER\n"
        "• Authors: [STUDENT INPUT REQUIRED: Student Names]\n"
        "• Date of Scan: [STUDENT INPUT REQUIRED: DD/MM/YYYY]\n\n"
        "INSTRUCTIONS FOR CANDIDATE:\n"
        "1. Submit this draft to your departmental plagiarism administrator.\n"
        "2. Obtain the official digital certificate.\n"
        "3. Attach the first page of the official report directly following this page before submission.",
        bold=True
    )
    doc.add_page_break()

    add_h1("APPENDIX B: RESEARCH PAPER AI PLAGIARISM / AI CONTENT REPORT (FIRST PAGE)").alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_p(
        "====================================================================================================\n"
        "MANDATORY UNIVERSITY SUBMISSION REQUIREMENT:\n"
        "ATTACH FIRST PAGE OF OFFICIAL RESEARCH PAPER AI DETECTION REPORT HERE\n"
        "====================================================================================================\n\n"
        "In compliance with institutional AI-use guidelines for academic research submissions, the student author must attach "
        "the official first page of the AI Content Detection report.\n\n"
        "INSTITUTIONAL AI DETECTION SPECIFICATIONS:\n"
        "• Maximum Permissible AI-Generated Content: Less than 20% (< 20%)\n"
        "• Approved AI Detection Engines: Turnitin AI Writing Detection / Copyleaks / GPTZero\n"
        "• Document Scanned: BRUTESHIELD_RESEARCH_PAPER\n"
        "• Authors: [STUDENT INPUT REQUIRED: Student Names]\n"
        "• Date of Verification: [STUDENT INPUT REQUIRED: DD/MM/YYYY]\n\n"
        "INSTRUCTIONS FOR CANDIDATE:\n"
        "1. Obtain the official AI detection output.\n"
        "2. Verify confirmed AI percentage is strictly below the mandatory 20% threshold.\n"
        "3. Attach the first page of the official output directly following this page before submission.",
        bold=True
    )
    doc.add_page_break()

    add_h1("APPENDIX C: RESEARCH PAPER GUIDE EVALUATION & ENDORSEMENT FORM").alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_p(
        "ABES ENGINEERING COLLEGE, GHAZIABAD\n"
        "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING\n"
        "RESEARCH PAPER EVALUATION & PUBLICATION READINESS RUBRIC\n",
        bold=True, align=WD_ALIGN_PARAGRAPH.CENTER
    )
    add_p(
        "Paper Title: BruteShield: A Modular Machine Learning-Based Framework for Authentication Attack Detection and Adaptive Security Monitoring\n"
        "Student Authors: [STUDENT INPUT REQUIRED]\n"
        "Guide Name & Designation: [STUDENT INPUT REQUIRED]\n\n"
        "MANDATORY REQUIREMENT: Without the internal supervisor's formal review and endorsement signature, the student is NOT eligible to submit this paper for publication or presentation.",
        bold=True
    )
    rub_data = [
        ("S.No.", "Evaluation Parameter / Research Quality Criteria", "Max Marks", "Marks Awarded", "Guide Remarks"),
        ("1", "Technical Novelty & Literature Synthesis (Kent, Liu, Schölkopf)", "20", "", ""),
        ("2", "Mathematical Rigor (Entropy, Isolation Forest c(n), GHASH)", "20", "", ""),
        ("3", "Empirical Benchmarking & LANL Dataset Ingestion Integrity", "20", "", ""),
        ("4", "Discussion of Findings (Base Rate Fallacy, Graduated Friction)", "20", "", ""),
        ("5", "Plagiarism (<10%) & AI Content (<20%) Compliance Verification", "10", "", ""),
        ("6", "IEEE Formatting, Citation Standards & Technical Writing Quality", "10", "", ""),
        ("", "TOTAL MARKS", "100", "", "")
    ]
    t_rub = doc.add_table(rows=len(rub_data), cols=5)
    t_rub.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(rub_data):
        for c_idx, val in enumerate(row):
            cell = t_rub.rows[r_idx].cells[c_idx]
            cell.paragraphs[0].text = val
            cell.paragraphs[0].runs[0].font.name = 'Times New Roman'
            cell.paragraphs[0].runs[0].font.size = Pt(8.5)
            if r_idx == 0:
                cell.paragraphs[0].runs[0].bold = True
                set_cell_background(cell, "CBD5E1")
            elif r_idx == len(rub_data) - 1:
                cell.paragraphs[0].runs[0].bold = True
                set_cell_background(cell, "DCFCE7")
            elif r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")

    add_p(
        "\nSUPERVISOR RECOMMENDATION:\n"
        "[   ] Recommended for Conference / Journal Submission\n"
        "[   ] Approved as Internal Capstone Research Draft\n"
        "[   ] Needs Revision before External Submission\n\n"
        "Supervisor Comments: _______________________________________________________________________________\n"
        "___________________________________________________________________________________________________\n\n"
        "Date: ________________________                   Supervisor Signature: ______________________________\n"
        "Place: Ghaziabad                                 Name & Seal: [STUDENT INPUT REQUIRED]"
    )

    doc.save(DOCX_OUT)
    print(f"[+] Successfully saved Word research paper: {DOCX_OUT}")
    os.makedirs(PAPER_SUBDIR, exist_ok=True)
    shutil.copy2(DOCX_OUT, os.path.join(PAPER_SUBDIR, "BRUTESHIELD_RESEARCH_PAPER.docx"))


# ===========================================================================
# 2. GENERATE RESEARCH PAPER PDF
# ===========================================================================
def generate_paper_pdf():
    print("[*] Generating BRUTESHIELD_RESEARCH_PAPER.pdf...")
    os.makedirs(PAPER_SUBDIR, exist_ok=True)

    doc = SimpleDocTemplate(
        PDF_OUT,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=8
    )
    draft_banner_style = ParagraphStyle(
        'DraftBanner',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#b91c1c"),
        alignment=1,
        spaceAfter=10
    )
    author_style = ParagraphStyle(
        'PaperAuth',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
        alignment=1,
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'PaperH1',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'PaperBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=5
    )
    caption_style = ParagraphStyle(
        'PaperCap',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceBefore=3,
        spaceAfter=6
    )

    story = []

    def p(text):
        story.append(Paragraph(text.replace("\n", "<br/>"), body_style))

    def h1(text, center=False):
        if center:
            c_style = ParagraphStyle('CenterH1', parent=h1_style, alignment=1)
            story.append(Paragraph(text, c_style))
        else:
            story.append(Paragraph(text, h1_style))

    # Draft Notice Banner
    story.append(Paragraph(
        "RESEARCH PAPER DRAFT — NOT YET SUBMITTED TO OR ACCEPTED BY ANY PEER-REVIEWED JOURNAL OR CONFERENCE<br/>"
        "Prepared for Academic Evaluation & B.Tech Capstone Project Defence (Academic Year 2025–2026)",
        draft_banner_style
    ))

    # Title & Authors
    story.append(Paragraph("BruteShield: A Modular Machine Learning-Based Framework for Authentication Attack Detection and Adaptive Security Monitoring", title_style))
    story.append(Paragraph(
        "[STUDENT INPUT REQUIRED: Student Name 1]*, [STUDENT INPUT REQUIRED: Student Name 2]*, [STUDENT INPUT REQUIRED: Guide Name]†<br/>"
        "*Department of Computer Science & Engineering, ABES Engineering College, Ghaziabad, India<br/>"
        "†Department of Computer Science & Engineering, ABES Engineering College, Ghaziabad, India<br/>"
        "Email: [STUDENT INPUT REQUIRED: student@example.edu.in]",
        author_style
    ))

    # Abstract Box
    p(
        "<b><i>Abstract</i>—Authentication mechanisms form the foundational security perimeter of modern web applications, yet remain severely vulnerable "
        "to automated credential stuffing, distributed brute-force, and low-and-slow password spraying attacks. Traditional threshold-based counters "
        "(e.g., locking an account after five consecutive failures within 60 seconds) are easily circumvented by adversaries who introduce deliberate "
        "inter-attempt delays or distribute attempts horizontally across multiple user identities. In this paper, we present BruteShield, a modular application-layer "
        "security framework combining real-time behavioral feature extraction with unsupervised machine learning anomaly detection. BruteShield extracts a "
        "six-dimensional statistical feature vector across a 900-second sliding observation window, evaluating attempt frequency, target diversity, and temporal spacing. "
        "An unsupervised Isolation Forest classifier scores incoming authentication events, mapping borderline anomaly scores to arithmetic CAPTCHA friction challenges "
        "before escalating confirmed repeat offenders through an adaptive cooldown ladder (60s to 3600s). The framework incorporates client-side Shannon entropy calculation, "
        "Have I Been Pwned (HIBP) k-anonymity breach verification, an authenticated zero-knowledge AES-256-GCM credential vault, and an unauthenticated honeypot trap with credential masking. "
        "Evaluated on synthetic benchmark scenarios and a verified 2.31-day empirical slice (21.26 million authentication events) of the Los Alamos National Laboratory (LANL) "
        "cybersecurity dataset, BruteShield detected 100% of stealthy low-and-slow proxy attacks that completely bypassed conventional Fail2ban threshold counters. "
        "We discuss the critical trade-offs between precision and ROC-AUC under extreme class imbalance and analyze the operational necessity of graduated friction responses.</b>"
    )
    p("<b><i>Keywords</i>—Authentication Security, Brute-Force Detection, Isolation Forest, Sliding-Window Telemetry, k-Anonymity, AES-256-GCM, LANL Cyber Dataset.</b>")
    story.append(Spacer(1, 6))

    h1("I. INTRODUCTION")
    p(
        "Web application authentication interfaces represent the primary defense boundary of modern enterprise infrastructure, yet remain the most frequently "
        "attacked surface in cyberspace. Automated botnets, residential proxy pools, and leaked credential databases allow adversaries to execute large-scale attacks "
        "with minimal overhead. Authentication attacks predominantly fall into three categories: (1) high-frequency brute force, (2) credential stuffing using leaked "
        "databases, and (3) low-and-slow password spraying engineered to evade threshold resets.<br/><br/>"
        "Traditional perimeter defenses (such as Fail2ban or simple login failure counters) rely on static rules: e.g., if 5 failures occur in 60 seconds, block the source IP. "
        "This approach fails against adversaries who space requests at 70-second intervals or spray across multiple accounts. Furthermore, enforcing account lockouts "
        "creates a severe Denial-of-Service (DoS) vulnerability: an unauthenticated attacker can lock out legitimate users simply by submitting incorrect passwords.<br/><br/>"
        "To resolve these limitations, we present BruteShield, an application-layer defense engine and live Security Operations Center (SOC) monitoring platform. "
        "BruteShield models authentication traffic as a continuous stream, extracting a 6-dimensional temporal feature vector across an indexed 900-second sliding window. "
        "Traffic is scored using an unsupervised Isolation Forest model. Borderline anomalies encounter CAPTCHA friction challenges, while confirmed malicious attacks "
        "trigger an exponential IP cooldown ladder (60s -> 300s -> 900s -> 3600s)."
    )

    h1("II. RELATED WORK & PROBLEM FORMULATION")
    p(
        "Authentication security has historically relied on signature and threshold rules. Liu et al. [2] introduced Isolation Forest, proving that anomalies "
        "in multi-dimensional space are naturally isolated closer to the root in random binary search trees with linear time complexity O(n). Schölkopf et al. [3] "
        "developed One-Class Support Vector Machines (OC-SVM) for boundary estimation, though with quadratic computational complexity. In cryptographic storage, "
        "McGrew and Viega [6] specified Galois/Counter Mode (AES-GCM), combining CTR confidentiality with GHASH integrity over GF(2^128). Hunt [9] demonstrated "
        "k-anonymity breach lookup using SHA-1 prefix bucketing. In cybersecurity dataset benchmarking, Kent [1] published the multi-source LANL Cyber1 dataset.<br/><br/>"
        "Let authentication requests be defined as a_i = (t_i, ip_i, u_i, s_i) where t_i in R^+, ip_i is IP, u_i is username, and s_i in {0,1} is success/failure. "
        "While conventional threshold counters evaluate scalar counts over narrow windows W = 60s, BruteShield maps traffic history into a vector space Psi: A^k -> R^6 "
        "over W_obs = 900s, computing total attempts, failure count, distinct usernames, mean inter-arrival gap, minimum burst gap, and failure ratio."
    )

    h1("III. PROPOSED BRUTESHIELD ARCHITECTURE")
    p(
        "BruteShield operates as a defense-in-depth architecture across five tiers: (1) Client Layer with Shannon entropy meter and dynamic CAPTCHAs, "
        "(2) Nginx Reverse Proxy terminating TLS 1.3 and enforcing perimeter limits, (3) WSGI Application Layer running Flask factory, "
        "(4) ML Anomaly Intelligence running 6D sliding-window feature extractor and Isolation Forest scoring, and (5) SQLite Persistence Storage operating in WAL mode."
    )
    # Embed Fig 1
    fig1_path = os.path.join(DIAG_DIR, "fig1_system_architecture.png")
    if os.path.exists(fig1_path):
        story.append(Spacer(1, 4))
        story.append(RLImage(fig1_path, width=440, height=303))
        story.append(Paragraph("Fig. 1. BruteShield modular system architecture and defense-in-depth topology.", caption_style))

    h1("IV. MATHEMATICAL FORMULATION & FEATURE ENGINEERING")
    p(
        "<b>A. Six-Dimensional Sliding-Window Feature Vector</b><br/>"
        "For an incoming attempt from IP address i at time t_curr, BruteShield queries all audit records within [t_curr - 900, t_curr]. The feature vector is:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;X = [N_tot, N_fail, U_dist, Delta_t_avg, Delta_t_min, R_fail]<br/>"
        "where N_tot is total attempts, N_fail is failed attempts, U_dist is unique usernames targeted, Delta_t_avg is mean inter-arrival interval, "
        "Delta_t_min is minimum burst interval, and R_fail = N_fail / N_tot.<br/><br/>"
        "<b>B. Isolation Forest Anomaly Scoring</b><br/>"
        "For dataset size n, average binary search tree path length is c(n) = 2*(ln(n-1) + 0.5772156649) - (2*(n-1)/n). Anomaly score is defined as:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;s(X, n) = 2^{ - (E(h(X)) / c(n)) }<br/>"
        "where E(h(X)) is expected path depth across trees. s -> 1 indicates severe anomaly; s ~ 0.5 indicates borderline traffic.<br/><br/>"
        "<b>C. Authenticated Galois/Counter Mode (AES-256-GCM) Cryptography</b><br/>"
        "User credentials stored in the vault are protected with AES-256-GCM AEAD encryption: C_i = P_i (+) CIPH_K(IV || cnt_i). "
        "Authentication is computed via universal polynomial hashing over GF(2^128): GHASH_H(X_1, ..., X_m) = sum X_j * H^{m-j+1}. "
        "Any byte tampering causes immediate InvalidTag rejection before plaintext disclosure."
    )

    h1("V. EMPIRICAL RESULTS & BENCHMARK EVALUATION")
    p(
        "<b>A. Synthetic Attack Simulation Benchmark (Phase 1 Baseline)</b><br/>"
        "In controlled experiments with 300 normal users and 190 simulated attack vectors (fast brute force, stuffing, and low-and-slow pacing), "
        "BruteShield's ML model achieved 96.5% overall accuracy, 94.8% precision, and 96.3% recall, vs. 83.5% accuracy and 57.9% recall for Fail2ban. "
        "On low-and-slow attacks (12–60s delay), BruteShield caught 100% of attack bursts while Fail2ban caught 0%."
    )
    p(
        "<b>B. LANL Enterprise Cybersecurity Dataset Benchmark (Phase 2B)</b><br/>"
        "To test temporal generalization under enterprise conditions, BruteShield was evaluated on the LANL Cyber1 dataset [1]. "
        "We parsed the verified Days 0 to 2.31 empirical slice (199,687s), filtering 16,050,924 LogOff records and retaining 21,255,459 authentication records. "
        "10 ground-truth red-team attacks occurred within this slice, matched 1-to-1 via bipartite matching (+0 Hopcroft-Karp discrepancy). "
        "Table I details performance across 30,137 evaluation windows."
    )

    pdf_exp_data = [
        ["Model Architecture", "TP", "FP", "FN", "TN", "Recall", "ROC-AUC", "FPR"],
        ["Isolation Forest", "3", "2,134", "1", "27,999", "75.0%", "0.8026", "7.08%"],
        ["One-Class SVM", "2", "436", "2", "29,697", "50.0%", "0.9382", "1.45%"],
        ["Random Forest", "1", "3,166", "3", "26,967", "25.0%", "0.8967", "10.51%"]
    ]
    t_exp_pdf = Table(pdf_exp_data, colWidths=[120, 35, 45, 35, 50, 50, 60, 50])
    t_exp_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
    ]))
    story.append(t_exp_pdf)
    story.append(Paragraph("TABLE I. LANL EXPERIMENT A: COMPARATIVE PERFORMANCE ON DAYS 0–2.31 (30,137 WINDOWS)", caption_style))

    h1("VI. CRITICAL DISCUSSION: THE BASE RATE FALLACY & GRADUATED FRICTION")
    p(
        "A vital academic insight from Table I is the sharp divergence between ROC-AUC and Precision. OC-SVM achieved 0.9382 ROC-AUC and Isolation Forest "
        "achieved 0.8026, yet precision was below 0.5% (0.0046 and 0.0014). This is the classic 'Base Rate Fallacy' caused by extreme class imbalance: "
        "with only 4 positive attack windows out of 30,137 total windows (0.013% prevalence), even an outstanding FPR of 1.45% produces 436 false alarms against 2 true positives.<br/><br/>"
        "In a real-world enterprise setting, an automated defense that immediately terminates accounts or IPs upon anomaly detection would generate 436 wrongful lockouts. "
        "This empirical reality justifies BruteShield's graduated friction ladder: routing borderline scores into arithmetic CAPTCHA challenges preserves legitimate "
        "human access while completely halting automated bots."
    )

    h1("VII. THREATS TO VALIDITY & LIMITATIONS")
    p(
        "1. Dataset Scope: Due to computational constraints, empirical benchmarking was performed strictly on the Days 0 to 2.31 slice (199,687s). Full 58-day evaluation remains future work.<br/>"
        "2. Telemetry Modality: LANL records enterprise Active Directory Kerberos/NTLM authentication, which lacks web HTTP cookie dynamics.<br/>"
        "3. Storage Concurrency: SQLite WAL mode provides excellent single-node concurrency but serializes writes; distributed deployments require PostgreSQL/Redis."
    )

    h1("VIII. CONCLUSION & FUTURE WORK")
    p(
        "BruteShield demonstrates that lightweight temporal sliding-window feature engineering paired with unsupervised Isolation Forest modeling provides an effective, "
        "defensible defense against automated authentication threats, catching 100% of low-and-slow proxy attacks that evaded Fail2ban. The system is validated "
        "with 75 automated tests, zero Bandit SAST flaws, and zero dependency CVEs. Future work will explore deep recurrent sequence models (LSTM) and distributed cloud clusters."
    )

    h1("REFERENCES")
    for r in REFERENCES:
        p(r)
    story.append(PageBreak())

    # Appendices
    h1("APPENDIX A: RESEARCH PAPER SIMILARITY / PLAGIARISM REPORT (FIRST PAGE)", center=True)
    p(
        "====================================================================================================<br/>"
        "<b>MANDATORY UNIVERSITY SUBMISSION REQUIREMENT:<br/>"
        "ATTACH FIRST PAGE OF OFFICIAL RESEARCH PAPER SIMILARITY REPORT HERE</b><br/>"
        "====================================================================================================<br/><br/>"
        "In compliance with Dr. A.P.J. Abdul Kalam Technical University (AKTU) / ABES Engineering College submission guidelines, "
        "the research paper draft must undergo formal computerized similarity screening.<br/><br/>"
        "<b>INSTITUTIONAL SIMILARITY SPECIFICATIONS:</b><br/>"
        "• Maximum Permissible Similarity Index: <b>Less than 10% (&lt; 10%)</b><br/>"
        "• Approved Verification Platforms: Turnitin / iThenticate / DrillBit<br/>"
        "• Document Scanned: BRUTESHIELD_RESEARCH_PAPER<br/>"
        "• Authors: [STUDENT INPUT REQUIRED: Student Names]<br/>"
        "• Date of Scan: [STUDENT INPUT REQUIRED: DD/MM/YYYY]<br/><br/>"
        "<b>INSTRUCTIONS FOR CANDIDATE:</b><br/>"
        "1. Submit this draft to your departmental plagiarism administrator.<br/>"
        "2. Obtain the official digital certificate.<br/>"
        "3. Attach the first page of the official report directly following this page before submission."
    )
    story.append(PageBreak())

    h1("APPENDIX B: RESEARCH PAPER AI PLAGIARISM / AI CONTENT REPORT (FIRST PAGE)", center=True)
    p(
        "====================================================================================================<br/>"
        "<b>MANDATORY UNIVERSITY SUBMISSION REQUIREMENT:<br/>"
        "ATTACH FIRST PAGE OF OFFICIAL RESEARCH PAPER AI DETECTION REPORT HERE</b><br/>"
        "====================================================================================================<br/><br/>"
        "In compliance with institutional AI-use guidelines for academic research submissions, the student author must attach "
        "the official first page of the AI Content Detection report.<br/><br/>"
        "<b>INSTITUTIONAL AI DETECTION SPECIFICATIONS:</b><br/>"
        "• Maximum Permissible AI-Generated Content: <b>Less than 20% (&lt; 20%)</b><br/>"
        "• Approved AI Detection Engines: Turnitin AI Writing Detection / Copyleaks / GPTZero<br/>"
        "• Document Scanned: BRUTESHIELD_RESEARCH_PAPER<br/>"
        "• Authors: [STUDENT INPUT REQUIRED: Student Names]<br/>"
        "• Date of Verification: [STUDENT INPUT REQUIRED: DD/MM/YYYY]<br/><br/>"
        "<b>INSTRUCTIONS FOR CANDIDATE:</b><br/>"
        "1. Obtain the official AI detection output.<br/>"
        "2. Verify confirmed AI percentage is strictly below the mandatory 20% threshold.<br/>"
        "3. Attach the first page of the official output directly following this page before submission."
    )
    story.append(PageBreak())

    h1("APPENDIX C: RESEARCH PAPER GUIDE EVALUATION & ENDORSEMENT FORM", center=True)
    p(
        "<b>ABES ENGINEERING COLLEGE, GHAZIABAD<br/>"
        "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING<br/>"
        "RESEARCH PAPER EVALUATION & PUBLICATION READINESS RUBRIC</b><br/>"
    )
    p(
        "<b>Paper Title:</b> BruteShield: A Modular Machine Learning-Based Framework for Authentication Attack Detection and Adaptive Security Monitoring<br/>"
        "<b>Student Authors:</b> [STUDENT INPUT REQUIRED]<br/>"
        "<b>Guide Name & Designation:</b> [STUDENT INPUT REQUIRED]<br/>"
        "<i>MANDATORY REQUIREMENT: Without the internal supervisor's formal review and endorsement signature, the student is NOT eligible to submit this paper.</i>"
    )
    rub_data = [
        ["S.No.", "Evaluation Parameter / Research Quality Criteria", "Max Marks", "Marks Awarded", "Guide Remarks"],
        ["1", "Technical Novelty & Literature Synthesis (Kent, Liu, Schölkopf)", "20", "", ""],
        ["2", "Mathematical Rigor (Entropy, Isolation Forest c(n), GHASH)", "20", "", ""],
        ["3", "Empirical Benchmarking & LANL Dataset Ingestion Integrity", "20", "", ""],
        ["4", "Discussion of Findings (Base Rate Fallacy, Graduated Friction)", "20", "", ""],
        ["5", "Plagiarism (<10%) & AI Content (<20%) Compliance Verification", "10", "", ""],
        ["6", "IEEE Formatting, Citation Standards & Technical Writing Quality", "10", "", ""],
        ["", "TOTAL MARKS", "100", "", ""]
    ]
    t_rub_pdf = Table(rub_data, colWidths=[30, 240, 50, 60, 90])
    t_rub_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#dcfce7")),
    ]))
    story.append(t_rub_pdf)
    story.append(Spacer(1, 10))
    p(
        "<b>SUPERVISOR RECOMMENDATION:</b><br/>"
        "[   ] Recommended for Conference / Journal Submission<br/>"
        "[   ] Approved as Internal Capstone Research Draft<br/>"
        "[   ] Needs Revision before External Submission<br/><br/>"
        "Supervisor Comments: _______________________________________________________________________________<br/><br/>"
        "Date: ________________________                   Supervisor Signature: ______________________________<br/>"
        "Place: Ghaziabad                                 Name & Seal: [STUDENT INPUT REQUIRED]"
    )

    doc.build(story, canvasmaker=PaperNumberedCanvas)
    print(f"[+] Successfully saved PDF research paper: {PDF_OUT}")
    shutil.copy2(PDF_OUT, os.path.join(PAPER_SUBDIR, "BRUTESHIELD_RESEARCH_PAPER.pdf"))


if __name__ == "__main__":
    generate_paper_docx()
    generate_paper_pdf()
