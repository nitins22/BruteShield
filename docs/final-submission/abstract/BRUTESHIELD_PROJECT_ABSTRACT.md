# BruteShield — Project Abstract & Multi-Format Descriptions

---

## 1. Formal Project Abstract (218 Words)

Modern web applications face pervasive credential-based cyber attacks, including automated brute-force, distributed credential stuffing, and low-and-slow password spraying. Conventional defenses rely on static lockout counters that trigger only when fixed thresholds are breached, leaving applications vulnerable to sophisticated adversaries who intentionally pace their requests to evade detection.

This project presents **BruteShield**, an adaptive application-layer cybersecurity defense engine and Security Operations Center (SOC) monitoring platform. BruteShield extracts a six-dimensional statistical and temporal feature vector across a 900-second sliding observation window—measuring attempt velocity, failure density, and target breadth. These features feed an unsupervised Isolation Forest anomaly detection model that scores authentication traffic continuously. Rather than imposing disruptive permanent account lockouts, BruteShield implements an adaptive escalation ladder that graduates from arithmetic CAPTCHA friction challenges to exponential IP cooldown quarantines (60s, 300s, 900s, 3600s).

The platform incorporates client-side Shannon entropy calculation, Have I Been Pwned (HIBP) $k$-anonymity breach audits, an authenticated zero-knowledge AES-256-GCM credential vault, and a proactive deception honeypot (`/admin-login`) with masked telemetry. Evaluated against synthetic attack scenarios and a 2.31-day empirical slice (21.26 million authentication events) of the Los Alamos National Laboratory (LANL) enterprise cybersecurity dataset, BruteShield detected 100% of stealthy low-and-slow proxy attacks that completely bypassed standard Fail2ban threshold counters.

---

## 2. 50-Word Elevator Pitch

BruteShield is an adaptive cybersecurity defense platform that replaces rigid threshold counters with machine learning anomaly detection. Analyzing temporal sliding-window features, it detects automated brute-force, password spraying, and low-and-slow attacks, graduating response from CAPTCHA friction to exponential cooldown lockouts, backed by an AES-256-GCM vault and real-time SOC dashboard.

---

## 3. 100-Word Extended Description

BruteShield is a defense-in-depth cybersecurity platform engineered to protect web authentication systems against automated credential threats. Traditional defenses fail against adversaries who distribute attempts or introduce delays between requests. BruteShield addresses this by analyzing six behavioral features over a 15-minute sliding window using an Isolation Forest anomaly model. The system responds adaptively—introducing arithmetic CAPTCHA friction before escalating to tiered IP cooldowns. Featuring an authenticated AES-256-GCM credential vault, HIBP $k$-anonymity breach auditing, a decoy honeypot trap, and an offline-capable dark SOC dashboard, BruteShield was benchmarked against 21.26 million Los Alamos National Laboratory enterprise authentication events.

---

## 4. Problem Statement

Authentication mechanisms remain the primary target of cyber adversaries. Traditional perimeter defenses implement rigid, static threshold rules (e.g., blocking an IP after five failures in 60 seconds). This model suffers from two critical vulnerabilities:
1. **Low-and-Slow Evasion:** Attackers inserting delays (e.g., one attempt every 70 seconds) completely reset fixed counters while cracking accounts over hours.
2. **Denial-of-Service Collateral:** Indiscriminate permanent account lockouts allow malicious actors to intentionally disable legitimate corporate accounts.
3. **Password Spraying:** Horizontal attacks testing common passwords across thousands of unique accounts never trip single-account lockout thresholds.

---

## 5. Project Objectives

1. **Behavioral Anomaly Detection:** Engineer a real-time sliding-window feature extractor and deploy an unsupervised machine learning model to classify anomalous authentication velocities.
2. **Adaptive Response Framework:** Construct an escalation ladder that applies friction (CAPTCHA) to borderline anomalies before applying temporary exponential cooldowns to confirmed threats.
3. **Cryptographic Data Protection:** Implement a zero-knowledge credential vault using authenticated AES-256-GCM encryption with unique nonces and tamper verification.
4. **Proactive Deception:** Deploy an unauthenticated decoy honeypot (`/admin-login`) that captures scanner probes and masks sensitive credential inputs.
5. **Operational Visibility:** Build an enterprise dark SOC dashboard that visualizes real-time telemetry, handles alert management, and partitions live operational logs from research benchmarks.
6. **Empirical Validation:** Benchmark the feature extraction pipeline against the Los Alamos National Laboratory (LANL) enterprise cybersecurity dataset.

---

## 6. Main Application Modules

- **Authentication & Registration Engine:** Enforces Shannon entropy thresholds, dictionary crack assessment via `zxcvbn`, and breach checks via HIBP $k$-anonymity.
- **Machine Learning Detection Engine:** Implements the 6-D sliding window extractor, Isolation Forest scoring, and fallback threshold logic.
- **Zero-Knowledge Vault:** Provides authenticated AES-256-GCM encryption/decryption with IDOR isolation.
- **Deception Honeypot:** Traps reconnaissance bots on fake admin routes and logs masked telemetry.
- **SOC Live Monitoring Portal:** Offline HTML5 canvas charts, threat alerts, IP investigation drawer, and benchmark views.
- **WSGI Production Architecture:** Multi-threaded Waitress (Windows) and Gunicorn (Linux) servers with Nginx reverse proxy guidance.

---

## 7. Technology Stack

- **Backend Framework:** Python 3.12, Flask 3.1.3, Werkzeug 3.1.9
- **Machine Learning:** Scikit-Learn 1.9.1 (Isolation Forest, One-Class SVM, Random Forest), NumPy, SciPy
- **Cryptography & Security:** Cryptography 50.0.2 (AESGCM), `hashlib` (SHA-1 for HIBP), `secrets`
- **Database & Storage:** SQLite3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL`)
- **Frontend & Visualization:** Responsive HTML5, Vanilla CSS3 (SOC Dark Theme), Offline HTML5 Canvas APIs
- **Testing & Verification:** Pytest 9.2.0 (75 automated tests), Bandit 1.9.4 (SAST), Pip-Audit 2.10.1 (CVE Scanner)
- **Production Server:** Waitress 3.0.2 WSGI server

---

## 8. Actual Technical Contributions

1. **Multi-Dimensional Feature Set:** Six behavioral features (`total_attempts`, `failed_attempts`, `distinct_usernames`, `avg_gap`, `min_gap`, `failure_ratio`) capturing velocity, breadth, and density.
2. **Graduated Friction Response:** Replacing binary lockouts with mathematical CAPTCHA friction on borderline anomaly scores ($0.0 \le s < 0.06$).
3. **Low-and-Slow Attack Detection:** Proved 100% catch rate on stealthy attack episodes where standard Fail2ban rules achieved 0%.
4. **Privacy-Preserving Telemetry:** Applying $k$-anonymity to breach checks and masking passwords in honeypot logs (`p***d (8 chars)`).
5. **Rigorous Quality Baseline:** 75 automated tests, zero Bandit security flaws, and zero dependency CVEs.

---

## 9. Experimental Methodology & Benchmark Results

- **Synthetic Baseline:** Evaluated against 300 normal users and 190 simulated attackers. ML model achieved **96.5% accuracy**, **94.8% precision**, and **96.3% recall** (vs. rule-based 83.5% accuracy, 57.9% recall).
- **LANL Cyber1 Dataset (Days 0–2.31 Empirical Slice):** Evaluated across 21.26 million retained Active Directory authentication records. Isolation Forest achieved **75.0% recall** on red-team attack windows, while One-Class SVM achieved **0.9382 ROC-AUC** with a 1.45% False Positive Rate.
- **Fail2ban Comparison:** In the LANL dataset, Fail2ban triggered 8,921 false alarms on normal background activity (0% attack episode coverage), while BruteShield caught 100% of low-and-slow proxy attacks.

---

## 10. Verified Limitations

1. **Dataset Scope:** The LANL evaluation was conducted on an empirical time slice (Days 0 to 2.31); full 58-day research results were not evaluated.
2. **Telemetry Context:** LANL captures Windows Active Directory Kerberos/NTLM authentication events, not interactive browser HTTP web logins.
3. **Database Concurrency:** SQLite WAL mode supports concurrent readers but serializes writes; large enterprise production requires PostgreSQL.
4. **Network Dependency:** Real-time HIBP breach auditing requires outbound internet connectivity; offline environments fall back to local entropy and dictionary scoring.

---

## 11. One-Minute Spoken Project Introduction

> *"Good morning, respected members of the evaluation committee. My project is **BruteShield**, an adaptive cybersecurity defense engine and SOC monitoring platform.*
>
> *Traditional login systems rely on simple counter rules—like blocking an IP after five wrong attempts. But today's attackers easily bypass this by pacing requests—called low-and-slow attacks—or by spraying common passwords across thousands of accounts.*
>
> *BruteShield solves this by extracting six behavioral features over a 15-minute sliding window and evaluating them with an unsupervised Isolation Forest machine learning model. Instead of permanent lockouts that cause Denial of Service for normal users, BruteShield uses an adaptive escalation ladder: starting with math CAPTCHA friction challenges and escalating to temporary cooldown lockouts.*
>
> *We also built a zero-knowledge AES-256-GCM password vault, an unauthenticated honeypot trap at `/admin-login`, and a real-time SOC monitoring dashboard. When evaluated on 21 million authentication records from the Los Alamos National Laboratory cyber dataset, BruteShield caught 100% of low-and-slow attacks that standard Fail2ban completely missed.*
>
> *The entire codebase is verified with 75 automated tests, zero security vulnerabilities, and production WSGI deployment scripts. Thank you, and I look forward to your questions."*
