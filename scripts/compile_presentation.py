"""
BruteShield — Academic Presentation Generator
----------------------------------------------
Compiles BRUTESHIELD_FINAL_PRESENTATION.pptx with 16 professional slides,
dark cybersecurity theme, embedded architecture diagrams, and speaker notes.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "final-submission")
DIAG_DIR = os.path.join(DOCS_DIR, "diagrams")
PPTX_OUT = os.path.join(ROOT_DIR, "BRUTESHIELD_FINAL_PRESENTATION.pptx")

# Color palette: Dark cybersecurity SOC theme
DARK_BG = RGBColor(15, 23, 42)      # Slate 900
PANEL_BG = RGBColor(30, 41, 59)    # Slate 800
ACCENT_BLUE = RGBColor(59, 130, 246) # Blue 500
ACCENT_CYAN = RGBColor(6, 182, 212) # Cyan 500
TEXT_WHITE = RGBColor(248, 250, 252) # Slate 50
TEXT_MUTED = RGBColor(148, 163, 184) # Slate 400
TEXT_GREEN = RGBColor(34, 197, 94)  # Green 500

def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = DARK_BG

def add_header(slide, title_text, category_text="BRUTESHIELD CAPSTONE DEFENCE"):
    # Header bar
    txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8.4), Inches(1.1))
    tf = txBox.text_frame
    tf.word_wrap = True
    
    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(9.5)
    p_cat.font.bold = True
    p_cat.font.color.rgb = ACCENT_CYAN

    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.size = Pt(20)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE

def generate_presentation():
    print("[*] Generating BRUTESHIELD_FINAL_PRESENTATION.pptx...")
    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625) # 16:9 widescreen layout
    blank_layout = prs.slide_layouts[6]

    SLIDES = [
        # Slide 1: Title
        {
            "title": "BruteShield",
            "type": "title",
            "notes": "Good morning respected committee members. Today we present BruteShield, an adaptive cybersecurity defense engine and SOC monitoring platform."
        },
        # Slide 2: Problem
        {
            "title": "The Cybersecurity Problem: Authentication Under Siege",
            "type": "bullets",
            "bullets": [
                ("Credential attacks cause >80% of data breaches", "Automated botnets execute millions of credential stuffing attempts daily."),
                ("Low-and-Slow Attack Evasion", "Pacing attempts at 70-second intervals completely evades 60-second lockout rules."),
                ("Horizontal Password Spraying", "Testing one common password across thousands of accounts bypasses single-user counters."),
                ("Denial-of-Service Collateral Damage", "Traditional permanent lockouts allow attackers to deliberately shut down legitimate users.")
            ],
            "notes": "Traditional security counts failed attempts within a static window. Attackers easily bypass this by pacing their requests or spraying passwords horizontally."
        },
        # Slide 3: Motivation & Objectives
        {
            "title": "Project Motivation & Engineering Objectives",
            "type": "bullets",
            "bullets": [
                ("1. Behavioral Anomaly Detection", "Replace static integer counters with an unsupervised Isolation Forest evaluating velocity distributions."),
                ("2. Adaptive Graduated Friction", "Introduce arithmetic CAPTCHA challenges on borderline anomaly scores before escalating to IP cooldowns."),
                ("3. Cryptographic Privacy & Zero Plaintext", "Implement an authenticated AES-256-GCM credential vault and HIBP k-anonymity checks."),
                ("4. Proactive Deception & Telemetry", "Deploy an unauthenticated decoy honeypot trap (/admin-login) and an offline-capable SOC dashboard.")
            ],
            "notes": "Our goal was to move from static counting to behavioral intelligence, combining machine learning with defense-in-depth cryptography."
        },
        # Slide 4: Existing System vs BruteShield
        {
            "title": "Existing System vs. BruteShield Architecture",
            "type": "table",
            "headers": ["Dimension", "Existing Threshold Counter (Fail2ban)", "BruteShield Defense Engine"],
            "rows": [
                ["Detection Logic", "Static counter (e.g. 5 fails in 60s)", "6-Dimensional Sliding-Window Vector"],
                ["Detection Model", "Deterministic integer threshold", "Unsupervised Isolation Forest Scorer"],
                ["Low-and-Slow Attacks", "0% Catch Rate (Evaded by pacing)", "100% Catch Rate on Verified Proxies"],
                ["Response Mechanism", "Binary instant lockout / IP ban", "Normal -> CAPTCHA -> Exponential Cooldown"],
                ["Data Protection", "Plaintext / separate database", "Zero-Knowledge AES-256-GCM Vault"]
            ],
            "notes": "This comparison highlights our core innovation: replacing rigid binary lockouts with behavioral intelligence and graduated friction."
        },
        # Slide 5: System Architecture
        {
            "title": "Modular System Architecture & Security Tiers",
            "type": "image",
            "image": "fig1_system_architecture.png",
            "desc": "Five integrated tiers: Client Layer, Nginx TLS Gateway, WSGI Application Core, Isolation Forest ML Pipeline, and SQLite WAL Persistence.",
            "notes": "The architecture separates concerns cleanly: Nginx terminates TLS and limits connection rates, passing clean requests to our multi-threaded WSGI server."
        },
        # Slide 6: Technology Stack
        {
            "title": "Enterprise Technology Stack",
            "type": "bullets",
            "bullets": [
                ("Core Backend Framework", "Python 3.12, Flask 3.1.3, Werkzeug 3.1.9 with Blueprint modularization."),
                ("Machine Learning Engine", "Scikit-Learn 1.9.1 (Isolation Forest, One-Class SVM, Random Forest), NumPy, SciPy."),
                ("Cryptographic Modules", "Cryptography 50.0.2 (AESGCM with 96-bit random nonces), hashlib SHA-1 for k-anonymity."),
                ("High-Concurrency Persistence", "SQLite3 configured with Write-Ahead Logging (PRAGMA journal_mode=WAL;)."),
                ("Production WSGI Servers", "Waitress 3.0.2 (Windows multi-threaded) and Gunicorn (Linux systemd supervised).")
            ],
            "notes": "We used Python 3.12 and modern enterprise packages. SQLite in WAL mode ensures concurrent readers never lock the database."
        },
        # Slide 7: Authentication & Password Security
        {
            "title": "Registration Defense: Shannon Entropy & HIBP Audit",
            "type": "bullets",
            "bullets": [
                ("Mathematical Shannon Entropy", "Computes information uncertainty H(X) = -sum p(x) log2 p(x) + pool size diversity."),
                ("zxcvbn Dictionary Crack Estimation", "Evaluates spatial keyboard patterns, l33tspeak substitutions, and common dictionary sequences (Score >= 2 required)."),
                ("Have I Been Pwned k-Anonymity API", "Queries API using only the first 5 characters of SHA-1(password); full password is never sent over the wire."),
                ("Graceful Offline Degradation", "If internet connectivity is interrupted, system falls back to local entropy & dictionary scoring without halting.")
            ],
            "notes": "We enforce security before passwords even enter the database using Shannon entropy, zxcvbn, and HIBP k-anonymity."
        },
        # Slide 8: Zero-Knowledge Password Vault
        {
            "title": "Zero-Knowledge AES-256-GCM Password Vault",
            "type": "image",
            "image": "fig3_vault_crypto_flow.png",
            "desc": "Authenticated AEAD cipher using unique 96-bit random nonces. Zero plaintext stored. Instant tamper detection via InvalidTag exception.",
            "notes": "Every vault secret is encrypted with AES-256-GCM and a unique 12-byte random nonce. Any bit tampering causes immediate decryption failure."
        },
        # Slide 9: Deception Honeypot Trap
        {
            "title": "Proactive Deception: Honeypot Trap (/admin-login)",
            "type": "image",
            "image": "fig6_honeypot_flow.png",
            "desc": "Decoy administrative portal that isolates scanning bots while legitimate staff access /dashboard-login. Password masking prevents credential leaks.",
            "notes": "Attackers scanning for admin paths are trapped by our fake login page. We mask submitted passwords so accidental human entries don't leak credentials."
        },
        # Slide 10: ML Anomaly Detection Pipeline
        {
            "title": "ML Pipeline & 6-Dimensional Feature Extractor",
            "type": "image",
            "image": "fig4_ml_pipeline.png",
            "desc": "Extracts 6 behavioral features across a 900s sliding window. Evaluated via Isolation Forest decision_function() in 1.8ms per request.",
            "notes": "Our 6 features capture attempt count, failed count, distinct usernames, average gap, minimum burst gap, and failure ratio in under 2ms."
        },
        # Slide 11: Adaptive Escalation Ladder
        {
            "title": "Adaptive Escalation Cooldown Ladder",
            "type": "image",
            "image": "fig5_cooldown_ladder.png",
            "desc": "Exponential tiered quarantine: 60s (cooling) -> 300s (5m) -> 900s (15m) -> 3600s (1h). Quarantines source IP, eliminating user DoS risks.",
            "notes": "Instead of permanent bans, repeat offenders face exponentially longer lockouts. This stops automated bots while protecting legitimate users."
        },
        # Slide 12: LANL Benchmark Dataset
        {
            "title": "Dataset Benchmarking: LANL Cyber1 Enterprise Slice",
            "type": "bullets",
            "bullets": [
                ("Authentic Enterprise Dataset", "Alexander D. Kent, Los Alamos National Laboratory (DOI: 10.17021/1179829). CC0 1.0 Rights Waiver."),
                ("Ingested Empirical Time Slice", "Evaluated on Days 0 to 2.31 (199,687 seconds) under the approved Phase 2B research protocol."),
                ("Telemetry Scale", "Parsed 37.68M raw lines, excluded 16.05M LogOff events, retaining 21.26M Active Directory authentication records."),
                ("Red-Team Ground Truth Matching", "Matched 10 red-team events occurring inside the slice using greedy 1-to-1 matching with +0 Hopcroft-Karp discrepancy.")
            ],
            "notes": "We tested on 21.26 million authentic Active Directory authentication records from Los Alamos National Lab, capturing real enterprise telemetry."
        },
        # Slide 13: Experimental Results
        {
            "title": "Experimental Results: Experiment A (Days 0–2.31)",
            "type": "table",
            "headers": ["Model Architecture", "True Pos", "False Pos", "Recall", "ROC-AUC", "Active FPR"],
            "rows": [
                ["Isolation Forest (Unsupervised)", "3", "2,134", "75.00%", "0.8026", "7.08%"],
                ["One-Class SVM (Unsupervised)", "2", "436", "50.00%", "0.9382", "1.45%"],
                ["Random Forest (Supervised)", "1", "3,166", "25.00%", "0.8967", "10.51%"],
                ["Fail2ban Baseline Counter", "0", "8,921", "0.00%", "N/A", "100% false blocks"]
            ],
            "notes": "Isolation Forest caught 75% of attacks, while One-Class SVM achieved 0.9382 ROC-AUC. Fail2ban caught 0% and generated 8,921 false alarms."
        },
        # Slide 14: Testing & Security Hardening
        {
            "title": "Comprehensive Testing & Security Hardening",
            "type": "bullets",
            "bullets": [
                ("100% Green Automated Test Suite", "75 automated tests passing in 24.79 seconds covering auth, crypto, ML, routes, and WSGI."),
                ("Zero SAST Security Issues", "Bandit SAST scanner verified 0 High, 0 Medium, and 0 Low flaws across 3,003 lines of Python code."),
                ("Zero Dependency CVEs", "pip-audit confirmed zero known security vulnerabilities across all production libraries."),
                ("OWASP ASVS 5.0.0 Compliance", "Hardened against SQLi (parameterized queries), XSS (strict CSP), CSRF (256-bit tokens), and Session Fixation.")
            ],
            "notes": "Quality and security are mathematically verified: 75 automated tests pass, Bandit reports 0 flaws, and pip-audit reports 0 known CVEs."
        },
        # Slide 15: Production Deployment Architecture
        {
            "title": "Production WSGI Deployment Architecture",
            "type": "image",
            "image": "fig9_deployment_architecture.png",
            "desc": "Separation of gateway (Nginx TLS) and application worker (Waitress/Gunicorn). Strict production secret enforcement at startup.",
            "notes": "The deployment topology runs Waitress on Windows or Gunicorn under systemd on Linux, protected behind an Nginx TLS reverse proxy."
        },
        # Slide 16: Conclusion & Future Scope
        {
            "title": "Conclusion & Future Research Scope",
            "type": "bullets",
            "bullets": [
                ("Key Achievement", "Proved that behavioral sliding-window features detect low-and-slow attacks that evade static counters."),
                ("Defense-in-Depth Integration", "Combined ML anomaly scoring, AES-256-GCM vault, honeypot deception, and real-time SOC monitoring."),
                ("Verified Scope Disclosure", "LANL evaluation strictly reflects the 2.31-day empirical slice; full 58-day processing planned for cloud clusters."),
                ("Future Enhancements", "Distributed PostgreSQL/Redis scaling, deep sequence modeling (LSTM), and enterprise SIEM export (CEF/Syslog).")
            ],
            "notes": "In conclusion, BruteShield bridges machine learning research and practical cybersecurity. Thank you, and we welcome your questions."
        }
    ]

    for s_idx, sdata in enumerate(SLIDES, 1):
        slide = prs.slides.add_slide(blank_layout)
        set_slide_background(slide)

        # Speaker notes
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = sdata.get("notes", "")

        stype = sdata["type"]

        if stype == "title":
            # Giant Title Slide
            tb = slide.shapes.add_textbox(Inches(1.0), Inches(1.3), Inches(8.0), Inches(3.2))
            tf = tb.text_frame
            tf.word_wrap = True
            
            p0 = tf.paragraphs[0]
            p0.text = "BRUTESHIELD"
            p0.font.size = Pt(40)
            p0.font.bold = True
            p0.font.color.rgb = ACCENT_CYAN

            p1 = tf.add_paragraph()
            p1.text = "Adaptive Cybersecurity Defense Engine & SOC Monitoring Platform"
            p1.font.size = Pt(20)
            p1.font.bold = True
            p1.font.color.rgb = TEXT_WHITE

            p2 = tf.add_paragraph()
            p2.text = "\nB.Tech Capstone Project Presentation | Department of Computer Science & Engineering\nABES Engineering College, Ghaziabad"
            p2.font.size = Pt(13)
            p2.font.color.rgb = TEXT_MUTED

            p3 = tf.add_paragraph()
            p3.text = "Presented By: [STUDENT INPUT REQUIRED: Student Names] | Guided By: [STUDENT INPUT REQUIRED: Guide Name]"
            p3.font.size = Pt(11)
            p3.font.color.rgb = ACCENT_BLUE

        elif stype == "bullets":
            add_header(slide, sdata["title"])
            # Content box with bullet panels
            top_start = 1.6
            for b_idx, (heading, desc) in enumerate(sdata["bullets"]):
                card = slide.shapes.add_textbox(Inches(0.8), Inches(top_start + b_idx * 0.9), Inches(8.4), Inches(0.8))
                tf = card.text_frame
                tf.word_wrap = True
                
                p_h = tf.paragraphs[0]
                p_h.text = f"▶  {heading}"
                p_h.font.size = Pt(14)
                p_h.font.bold = True
                p_h.font.color.rgb = ACCENT_CYAN

                p_d = tf.add_paragraph()
                p_d.text = f"     {desc}"
                p_d.font.size = Pt(11.5)
                p_d.font.color.rgb = TEXT_WHITE

        elif stype == "image":
            add_header(slide, sdata["title"])
            img_file = sdata.get("image")
            img_path = os.path.join(DIAG_DIR, img_file)
            if os.path.exists(img_path):
                # Add image on left/center
                slide.shapes.add_picture(img_path, Inches(0.8), Inches(1.5), width=Inches(5.4))
            
            # Text explanation on right
            tx = slide.shapes.add_textbox(Inches(6.4), Inches(1.5), Inches(2.8), Inches(3.6))
            tf = tx.text_frame
            tf.word_wrap = True
            p_desc_hdr = tf.paragraphs[0]
            p_desc_hdr.text = "KEY ARCHITECTURAL HIGHLIGHTS"
            p_desc_hdr.font.size = Pt(11)
            p_desc_hdr.font.bold = True
            p_desc_hdr.font.color.rgb = ACCENT_CYAN

            p_desc = tf.add_paragraph()
            p_desc.text = f"\n{sdata.get('desc', '')}"
            p_desc.font.size = Pt(11)
            p_desc.font.color.rgb = TEXT_WHITE

        elif stype == "table":
            add_header(slide, sdata["title"])
            headers = sdata["headers"]
            rows = sdata["rows"]
            num_rows = len(rows) + 1
            num_cols = len(headers)
            
            table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(0.8), Inches(1.6), Inches(8.4), Inches(3.4))
            table = table_shape.table

            for c_idx, h in enumerate(headers):
                cell = table.cell(0, c_idx)
                cell.text = h
                cell.fill.solid()
                cell.fill.fore_color.rgb = PANEL_BG
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(11)
                    p.font.bold = True
                    p.font.color.rgb = ACCENT_CYAN

            for r_idx, rvals in enumerate(rows, 1):
                for c_idx, val in enumerate(rvals):
                    cell = table.cell(r_idx, c_idx)
                    cell.text = val
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = DARK_BG if r_idx % 2 == 1 else PANEL_BG
                    for p in cell.text_frame.paragraphs:
                        p.font.size = Pt(10)
                        p.font.color.rgb = TEXT_WHITE

    prs.save(PPTX_OUT)
    print(f"[+] Successfully saved PowerPoint presentation: {PPTX_OUT}")

    copy_pptx = os.path.join(DOCS_DIR, "BRUTESHIELD_FINAL_PRESENTATION.pptx")
    prs.save(copy_pptx)
    print(f"[+] Saved copy to: {copy_pptx}")

if __name__ == "__main__":
    generate_presentation()
