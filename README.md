# BruteShield — Adaptive Cybersecurity Defense Engine & SOC Monitoring Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-50%2F50%20Passing-brightgreen.svg)](tests/)
[![Security Audit](https://img.shields.io/badge/OWASP-ASVS%205.0.0%20Verified-blueviolet.svg)](SECURITY_AUDIT.md)
[![Vulnerabilities](https://img.shields.io/badge/Vulnerabilities-0%20Known%20(pip--audit)-success.svg)](DEPENDENCY_AUDIT.md)
[![SAST](https://img.shields.io/badge/SAST-Bandit%200%20Flaws-success.svg)](SECURITY_AUDIT.md)

BruteShield is an enterprise-grade, defense-in-depth cybersecurity platform designed to protect web applications against automated credential stuffing, distributed brute force, and credential harvesting. Rather than relying solely on naive attempt counters, BruteShield analyzes the **behavioral characteristics** of authentication traffic in real time using multi-dimensional temporal sliding windows and Machine Learning anomaly scoring.

Developed as a B.Tech Computer Science & Engineering Capstone Project at ABES Engineering College, Ghaziabad.

---

## 1. System Features & Architecture

| Defense Layer | Implementation | Security Benefit |
|---|---|---|
| **Behavioral ML Anomaly Detection** | Random Forest / Isolation Forest with 8 sliding-window features | Detects low-and-slow attacks, password spraying, and burst anomalies |
| **Adaptive Escalation Ladder** | Normal -> Math CAPTCHA Challenge -> Cooldown (60s -> 300s -> 900s -> 3600s) | Eliminates automated bot traffic while minimizing legitimate user friction |
| **Zero-Knowledge Password Vault** | Authenticated AES-256-GCM cipher with random nonces & auth tags | Cryptographic confidentiality & tamper detection; zero plaintext stored |
| **Client-Side Security Engine** | Shannon entropy (bits), zxcvbn dictionary evaluation | Prevents weak passwords from entering the system at registration |
| **Breach Audit (k-Anonymity)** | Have I Been Pwned API via 5-char SHA-1 prefix matching | Audits compromised passwords without disclosing user credentials |
| **Proactive Decoy Honeypot** | Trap endpoint at `/admin-login` with masked audit logging | Traps scanning bots and isolates attack traffic from real administration |
| **Live SOC Monitoring Portal** | Dark SOC interface, real-time telemetry, threat alerts, telemetry charts | Complete visibility into attack velocities, vectors, and live controls |
| **Scientific Benchmark Rigor** | Benchmarked on Los Alamos National Laboratory (LANL) cyber dataset | 97.4% Precision on real-world enterprise authentication telemetry |

---

## 2. Project Documentation Matrix

| Document | Purpose & Contents |
|---|---|
| [FACULTY_DEMO_RUNBOOK.md](FACULTY_DEMO_RUNBOOK.md) | **Step-by-step 10-12 minute academic evaluation & demo script with top 10 Q&A** |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production WSGI (Waitress/Gunicorn), Nginx/Caddy TLS setup, and Systemd service |
| [SECURITY_AUDIT.md](SECURITY_AUDIT.md) | OWASP ASVS 5.0.0 compliance audit, threat modeling, and vulnerability remediation |
| [PENETRATION_TEST_REPORT.md](PENETRATION_TEST_REPORT.md) | OWASP WSTG 4.2 attack test results and proof-of-concept testing logs |
| [TEST_MATRIX.md](TEST_MATRIX.md) | Detailed inventory of all 50 automated tests and outcomes |
| [DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md) | pip-audit dependency vulnerability audit and package licenses |
| [REAL_DATASET_EVALUATION.md](REAL_DATASET_EVALUATION.md) | LANL Cyber Security Dataset evaluation, data pipeline, and benchmark comparison |
| [STAGE4_FINAL_REPORT.md](STAGE4_FINAL_REPORT.md) | Comprehensive Stage 4 executive milestone summary |

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
# On Windows:
run_production.bat
# Or:
python wsgi.py

# On Linux:
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
# 1. Run full 50-test automated regression suite
pytest tests/ -v

# 2. Audit dependencies for known vulnerabilities (0 CVEs)
pip-audit

# 3. Static Application Security Testing (Bandit SAST - 0 issues)
bandit -r bruteshield/ app.py

# 4. Verify protected machine learning artifact integrity
python -c "import hashlib; print('Model SHA-256:', hashlib.sha256(open('trained_model.pkl','rb').read()).hexdigest())"
# Expected Hash: 0f42590f98026b54b3f9c570c37f05e57a5a013da6c3dc3cb2e9e5421cd48e8f
```

---

## 7. Interactive Attack Simulation

BruteShield includes an interactive attack demonstration tool to simulate real-world attacks against a running instance:

```bash
# Mode 1: Fast Brute Force attack on user login (/login)
python attack_simulation.py login

# Mode 2: Credential stuffing against SOC login (/dashboard-login)
python attack_simulation.py admin

# Mode 3: Scanner attack on Decoy Honeypot (/admin-login)
python attack_simulation.py honeypot

# Mode 4: Distributed-style Password Spraying
python attack_simulation.py spray
```

---

## 8. Academic Project Information

- **Institution:** ABES Engineering College, Ghaziabad
- **Department:** Department of Computer Science & Engineering
- **Project Type:** B.Tech Major / Capstone Project
- **Primary Domain:** Application Security, Applied Machine Learning, Cyber Defense
- **License:** MIT License (Academic & Research Use)
