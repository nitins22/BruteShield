# BruteShield — Adaptive Cybersecurity Defense Engine & SOC Monitoring Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-75%2F75%20Passing-brightgreen.svg)](tests/)
[![Security Audit](https://img.shields.io/badge/OWASP-ASVS%205.0.0%20Verified-blueviolet.svg)](SECURITY_AUDIT.md)
[![Vulnerabilities](https://img.shields.io/badge/Vulnerabilities-0%20Known%20(pip--audit)-success.svg)](DEPENDENCY_AUDIT.md)
[![SAST](https://img.shields.io/badge/SAST-Bandit%200%20Flaws-success.svg)](SECURITY_AUDIT.md)
[![Academic Stage](https://img.shields.io/badge/Submission-Stage%206%20Final%20Handover-orange.svg)](docs/final-submission/)

BruteShield is an enterprise-grade, defense-in-depth cybersecurity platform designed to protect web applications against automated credential stuffing, distributed brute force, and stealthy password spraying. Rather than relying on rigid, memoryless threshold counters (e.g. 5 failures in 60s), BruteShield continuously extracts a **six-dimensional statistical and temporal feature vector** across an indexed 900-second sliding window, evaluating authentication velocities and patterns using an unsupervised **Isolation Forest** anomaly detection model.

Developed as a B.Tech Computer Science & Engineering Capstone Project at ABES Engineering College, Ghaziabad.

---

## 1. System Architecture & Core Capabilities

| Defense Layer | Implementation | Security Benefit |
|---|---|---|
| **Behavioral ML Anomaly Engine** | Isolation Forest with 6 sliding-window features | Catches low-and-slow velocity pacing, password spraying, and burst bot scripts |
| **Adaptive Escalation Ladder** | Normal $\rightarrow$ Math CAPTCHA Challenge $\rightarrow$ Tiered Cooldowns (60s $\rightarrow$ 300s $\rightarrow$ 900s $\rightarrow$ 3600s) | Eliminates automated bot traffic while neutralizing account-lockout Denial of Service |
| **Zero-Knowledge Password Vault** | Authenticated AES-256-GCM cipher with 96-bit random nonces & auth tags | Cryptographic confidentiality & tamper detection; zero plaintext stored on disk |
| **Client-Side Security Engine** | Shannon entropy (bits) & zxcvbn pattern matching | Prevents weak and compromised passwords from entering the system at registration |
| **Breach Audit (k-Anonymity)** | Have I Been Pwned API via 5-char SHA-1 prefix matching | Audits compromised passwords without disclosing user credentials over the network |
| **Proactive Decoy Honeypot** | Trap endpoint at `/admin-login` with masked audit logging (`p***d`) | Traps scanning bots and isolates attack traffic from real administration (`/dashboard-login`) |
| **Real-Time SOC Dashboard** | Dark SOC interface, live telemetry feeds, alert management, offline canvas charts | Complete visibility into attack velocities, vectors, and live administrative unblock controls |
| **Empirical Research Benchmarking** | Benchmarked on 21.26M events from Los Alamos National Lab (LANL) dataset | 100% catch rate on stealthy low-and-slow proxy attacks that completely evaded Fail2ban |

---

## 2. Stage 6 Final Academic Submission Package

All formal university submission documents, presentations, and design assets are compiled in the root repository and organized under [`docs/final-submission/`](docs/final-submission/):

| Submission Category | Core Deliverables | File Format & Description |
|---|---|---|
| **Final B.Tech Project Report** | [`docs/final-submission/project-report/`](docs/final-submission/project-report/)<br/>• [BRUTESHIELD_FINAL_PROJECT_REPORT.pdf](BRUTESHIELD_FINAL_PROJECT_REPORT.pdf)<br/>• [BRUTESHIELD_FINAL_PROJECT_REPORT.docx](BRUTESHIELD_FINAL_PROJECT_REPORT.docx) | **32 substantive pages** (exceeds mandatory >= 30 page requirement). Formatted for **spiral binding** on A4 with 1.25" inner gutter, running headers/footers (`Page X of 32`), 11 chapters, system diagrams, and Appendices A & B for official plagiarism report insertion. |
| **Academic Research Paper** | [`docs/final-submission/research-paper/`](docs/final-submission/research-paper/)<br/>• [BRUTESHIELD_RESEARCH_PAPER.pdf](BRUTESHIELD_RESEARCH_PAPER.pdf)<br/>• [BRUTESHIELD_RESEARCH_PAPER.docx](BRUTESHIELD_RESEARCH_PAPER.docx) | **7-page IEEE format research paper draft** with prominent draft status disclaimer, mathematical derivations (entropy, Isolation Forest $c(n)$, GHASH $GF(2^{128})$, $k$-anonymity), empirical LANL benchmarks, and separate plagiarism report attachments. |
| **Faculty Guide Evaluations** | • [GUIDE_APPROVAL_CHECKLIST.md](docs/final-submission/GUIDE_APPROVAL_CHECKLIST.md)<br/>• [GUIDE_EVALUATION_PROJECT_REPORT.pdf](docs/final-submission/project-report/GUIDE_EVALUATION_PROJECT_REPORT.pdf)<br/>• [GUIDE_EVALUATION_RESEARCH_PAPER.pdf](docs/final-submission/research-paper/GUIDE_EVALUATION_RESEARCH_PAPER.pdf) | Mandatory faculty clearance rubrics (100 marks total) with student eligibility sign-off and formal recommendation provisions. |
| **Plagiarism & AI Verification** | • [PLAGIARISM_VERIFICATION_CHECKLIST.md](docs/final-submission/PLAGIARISM_VERIFICATION_CHECKLIST.md)<br/>• [Project Report Plagiarism Guide](docs/final-submission/project-report/PROJECT_REPORT_PLAGIARISM_INSERTION_GUIDE.md)<br/>• [Research Paper Plagiarism Guide](docs/final-submission/research-paper/RESEARCH_PAPER_PLAGIARISM_INSERTION_GUIDE.md) | Protocols and screening checklists to ensure compliance with university thresholds (<10% similarity, <20% AI content) and first-page attachment instructions. |
| **PowerPoint Presentation** | [`docs/final-submission/presentation/`](docs/final-submission/presentation/)<br/>• [BRUTESHIELD_FINAL_PRESENTATION.pptx](BRUTESHIELD_FINAL_PRESENTATION.pptx) | 16 widescreen slides, dark SOC cybersecurity theme, embedded diagrams, and comprehensive speaker notes for 12–15 min viva. |
| **Faculty Viva Voce Guide** | [`docs/final-submission/viva/`](docs/final-submission/viva/)<br/>• [BRUTESHIELD_VIVA_QUESTIONS.md](BRUTESHIELD_VIVA_QUESTIONS.md) | 52 technical examination questions with spoken answers, detailed technical derivations, code mappings, and Hinglish study summaries. |
| **Project Abstract & Pitch** | [`docs/final-submission/abstract/`](docs/final-submission/abstract/)<br/>• [BRUTESHIELD_PROJECT_ABSTRACT.md](BRUTESHIELD_PROJECT_ABSTRACT.md) | Multi-format pitch portfolio: 200-word academic abstract, 50-word elevator pitch, 100-word executive summary, and 1-minute oral pitch. |
| **Student Authorship Review** | [STUDENT_AUTHORSHIP_REVIEW.md](docs/final-submission/STUDENT_AUTHORSHIP_REVIEW.md) | Authorship verification checklist, equations to derive live, results defense notes, and institutional AI disclosure guidance. |
| **Central Evidence Register** | [CENTRAL_EVIDENCE_REGISTER.md](docs/final-submission/CENTRAL_EVIDENCE_REGISTER.md) | Traceable claim-to-code mapping matrix linking every factual and experimental statement to verifiable repository evidence. |
| **System Diagrams (11)** | [`docs/final-submission/diagrams/`](docs/final-submission/diagrams/) | All 11 system diagrams provided in Mermaid editable source (`editable-source/`) and high-resolution PNG (`png/`). |
| **Production Runbooks** | • [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)<br/>• [FACULTY_DEMO_RUNBOOK.md](FACULTY_DEMO_RUNBOOK.md) | Production WSGI (Waitress/Gunicorn), Nginx TLS 1.3, systemd unit, SQLite WAL backups, and 10–12 minute live faculty demonstration script. |
| **Final Handover Report** | [STAGE6_FINAL_HANDOVER.md](STAGE6_FINAL_HANDOVER.md) | Comprehensive University Submission Handover Report, Git tag inventory, and compliance checklist. |

---

## 3. Quickstart & Installation

### Prerequisites
- Python 3.10+ (Tested on Python 3.12.10)
- SQLite 3.35+
- Windows PowerShell or Linux Bash

### Installation (Virtual Environment)
```bash
# Clone repository
git clone https://github.com/nitin-gupta/bruteshield_prototype.git
cd bruteshield_prototype

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 4. Running the Platform

### A. Development Mode (Local Testing)
```bash
python app.py
```
Server runs at `http://127.0.0.1:5000`.

### B. Production Mode (Hardened WSGI)
```bash
# On Windows (Waitress Multi-Threaded WSGI Server):
run_production.bat
# Or:
python wsgi.py

# On Linux (Gunicorn foreground under systemd):
./run_production.sh
```

---

## 5. Portal Navigation & Default Credentials

| Portal Path | Purpose | Default Credentials |
|---|---|---|
| `/login` | Protected User Authentication Portal | `admin` / `Secure@123` |
| `/signup` | User Registration & Entropy/HIBP Audit | *(Register new accounts)* |
| `/vault` | Zero-Knowledge AES-256-GCM Vault | *(Requires user login)* |
| `/dashboard-login` | Administrative SOC Portal Gateway | `dashadmin` / `Dash@Admin1` |
| `/dashboard` | Live SOC Monitoring Dashboard | *(Requires admin login)* |
| `/dashboard/threats` | Active Threat Alerts & Incident Response | *(Requires admin login)* |
| `/dashboard/benchmarks`| Scientific & LANL Research Benchmarks | *(Strict data partitioning)* |
| `/admin-login` | **Decoy Honeypot Trap** (Fake Admin) | *(Any probe is trapped)* |

---

## 6. Verification & Security Auditing Commands

Execute all quality, security, and integrity checks with single commands:

```bash
# 1. Run full 75-test automated regression suite (100% green in ~25s)
pytest tests/ -v

# 2. Audit dependencies for known vulnerabilities (0 CVEs)
pip-audit

# 3. Static Application Security Testing (Bandit SAST - 0 issues across 3,003 LOC)
bandit -r bruteshield/ app.py wsgi.py attack_simulation.py scripts/

# 4. Verify protected machine learning artifact integrity
python -c "import hashlib; print('Model SHA-256:', hashlib.sha256(open('trained_model.pkl','rb').read()).hexdigest())"
# Expected Hash: 0f42590f98026b54b3f9c570c37f05e57a5a013da6c3dc3cb2e9e5421cd48e8f

# 5. Execute pre-flight demonstration health check
python scripts/demo_setup.py verify
```

---

## 7. Interactive Attack Simulation Tool

BruteShield includes an interactive attack demonstration tool to simulate real-world attacks against a running instance:

```bash
# Mode 1: Safe Dry-Run (preview planned requests without sending)
python attack_simulation.py login --dry-run

# Mode 2: Fast Brute Force attack on user login (/login)
python attack_simulation.py login

# Mode 3: Credential stuffing against SOC gateway (/dashboard-login)
python attack_simulation.py admin

# Mode 4: Scanner probe attack on Decoy Honeypot (/admin-login)
python attack_simulation.py honeypot

# Mode 5: Distributed-style Password Spraying across multiple usernames
python attack_simulation.py spray
```

---

## 8. Academic Project Information

- **Institution:** ABES Engineering College, Ghaziabad
- **Affiliation:** Dr. A.P.J. Abdul Kalam Technical University, Lucknow
- **Department:** Department of Computer Science & Engineering
- **Project Type:** B.Tech Capstone Project (Academic Session 2025–2026)
- **Domain:** Application Security, Machine Learning Anomaly Detection, Cyber Threat Intelligence
- **License:** MIT License (Academic & Research Use)
