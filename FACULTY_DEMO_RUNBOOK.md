# BruteShield — Faculty Demonstration Runbook & Presentation Guide

**Project Title:** BruteShield — Adaptive Cybersecurity Defense Engine & Live SOC Monitoring Platform  
**Target Audience:** Project Evaluation Committee, External Examiners, Faculty Guides  
**Estimated Presentation Duration:** 10–12 Minutes  

---

## 1. Executive Summary & Project Positioning

BruteShield is a defense-in-depth cybersecurity platform that protects web applications against automated credential stuffing, distributed brute force, and credential harvesting. It combines:
1. **Behavioral Machine Learning Anomaly Detection:** Real-time sliding-window feature extraction that classifies attack velocity and patterns rather than relying solely on static attempt counters.
2. **Adaptive Escalation Ladder:** Multi-tiered defense (Normal -> Math CAPTCHA friction challenge -> Cooldown blocking ladder: 60s, 300s, 900s, 3600s).
3. **Proactive Decoy Honeypot (`/admin-login`):** Traps automated bot scanners and attacker discovery scripts while isolating legitimate administrative portals.
4. **Client-Side & Storage Privacy:** Zero-knowledge AES-256-GCM credential vault, real-time Shannon entropy calculation, and Have I Been Pwned (HIBP) k-Anonymity breach verification.
5. **Real-Time SOC Monitoring Dashboard:** Enterprise dark SOC telemetry with strict tripartite data partitioning (Operational Logs, Synthetic Benchmarks, and Los Alamos National Laboratory Cyber Dataset).

---

## 2. Demonstration Flow & Timing Breakdown

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      TOTAL RUNTIME: 10-12 MINUTES                      │
 ├──────────────┬──────────────────────────────────────────┬──────────────┤
 │ Time         │ Demonstration Module                     │ Tool / URL   │
 ├──────────────┼──────────────────────────────────────────┼──────────────┤
 │ 00:00 - 01:30│ Phase 0: Test Suite & Security Audit Verif│ Terminal     │
 │ 01:30 - 03:30│ Phase 1: Registration, Entropy & HIBP API│ /signup      │
 │ 03:30 - 05:30│ Phase 2: Zero-Knowledge AES-GCM Vault    │ /vault       │
 │ 05:30 - 08:30│ Phase 3: Live Brute Force & ML Block     │ Simulation/SOC│
 │ 08:30 - 10:00│ Phase 4: Honeypot Decoy Trap Analysis    │ /admin-login │
 │ 10:00 - 12:00│ Phase 5: Scientific Benchmarks & Q&A     │ /dashboard   │
 └──────────────┴──────────────────────────────────────────┴──────────────┘
```

---

## 3. Step-by-Step Demonstration Script

### Phase 0: System Health & Security Baseline (1.5 Minutes)
**Objective:** Prove to evaluators that the project meets enterprise security standards, has 0 known vulnerabilities, and passes 50 automated tests.

1. **Verify Automated Test Suite (50/50 Passing):**
   ```powershell
   .\venv\Scripts\python.exe -m pytest tests/ -v
   ```
   *Speaking Point:* "We have implemented a comprehensive 50-test test suite covering ML inference, sliding-window feature extraction, cryptographic vault isolation, CSRF protection, and OWASP ASVS compliance. All 50 tests execute and pass in under 25 seconds."

2. **Verify Zero CVEs (pip-audit):**
   ```powershell
   .\venv\Scripts\pip-audit.exe
   ```
   *Speaking Point:* "We audited all project dependencies against the Python Packaging Advisory Database. Zero known vulnerabilities exist in our production stack."

3. **Verify Zero Static Flaws (Bandit SAST):**
   ```powershell
   .\venv\Scripts\bandit.exe -r bruteshield/ app.py
   ```
   *Speaking Point:* "Our static application security testing (SAST) scan reports zero high, medium, or low severity issues across the entire codebase."

---

### Phase 1: User Onboarding, Shannon Entropy & HIBP Audit (2 Minutes)
**Objective:** Demonstrate proactive defense before authentication credentials are even stored.

1. **Launch BruteShield Server:**
   ```powershell
   .\venv\Scripts\python.exe wsgi.py
   # or run_production.bat
   ```
2. **Navigate to:** `http://127.0.0.1:5000/signup`
3. **Demonstrate Weak Password Detection:**
   - Type username: `demo_student`
   - Type password: `password123`
   - **Show:** The Shannon entropy meter indicates low entropy (~25 bits), the strength indicator flags "Weak", and the client displays a zxcvbn warning: *"This is a top-10 common password"*.
   - Click **Create Account** -> Registration is rejected with a clear policy violation message.
4. **Demonstrate HIBP k-Anonymity Privacy Guarantee:**
   - Type password: `Password123!`
   - **Show:** The system queries the Have I Been Pwned API using **k-Anonymity**. Only the first 5 characters of the SHA-1 hash (`CBFD9`) are sent over the wire; the server returns a range of suffixes and the client matches locally.
   - **Show:** Notification appears: *"Warning: This password has appeared in over 200,000 data breaches!"*
5. **Register with Strong Password:**
   - Type password: `K8#mQ9!vL2$xP5@wR7` (Entropy > 60 bits, Score 4/4).
   - Account successfully created!

---

### Phase 2: Zero-Knowledge AES-256-GCM Vault (2 Minutes)
**Objective:** Prove mathematically sound cryptographic storage and tamper detection.

1. **Log in:** `http://127.0.0.1:5000/login` with your newly registered credentials.
2. **Navigate to Vault:** `/vault`
3. **Store a Sensitive Secret:**
   - Service: `AWS Production Console`
   - Username: `ops-lead@company.internal`
   - Password: `SuperSecretProductionPassword#2026`
   - Click **Encrypt & Save**.
4. **Demonstrate Zero Plaintext in Database (Live SQLite Inspection):**
   - Open a second terminal and query the database:
   ```powershell
   .\venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('logs/bruteshield.db'); print(conn.execute('SELECT service_name, username, encrypted_password FROM vault_items').fetchall()); conn.close()"
   ```
   - **Show:** The database contains only base64-encoded binary ciphertext containing a 12-byte random nonce, ciphertext payload, and 16-byte authentication tag (`AES-256-GCM`). **Zero plaintext exists on disk.**
5. **Demonstrate Tamper Detection:**
   - *Speaking Point:* "If a malicious database administrator or attacker alters even a single bit of the stored ciphertext, AES-GCM's cryptographic authentication tag fails verification (`InvalidTag`), completely preventing decryption."

---

### Phase 3: Live Attack Simulation & SOC Response (3 Minutes)
**Objective:** Demonstrate BruteShield actively detecting and mitigating a multi-attempt brute force attack.

1. **Open SOC Dashboard in Browser:**
   - Navigate to: `http://127.0.0.1:5000/dashboard-login`
   - Log in with administrative credentials:
     - Username: `dashadmin`
     - Password: `Dash@Admin1`
   - View the **Live Overview** page. Note the current metrics and Threat Alert feed.
2. **Execute Live Attack Simulation in Terminal:**
   ```powershell
   .\venv\Scripts\python.exe attack_simulation.py login
   ```
   - **Watch the Console:**
     - Attempts 1–3: Standard failed authentication logged.
     - Attempt 4: Adaptive CAPTCHA challenge triggered.
     - Attempt 5: **ML Behavioral Anomaly Detected** -> Attacker IP blocked on Tier-1 cooldown (60 seconds).
3. **Verify Immediate SOC Telemetry:**
   - Refresh the SOC Dashboard (or wait for live polling).
   - **Show:**
     - High-priority Threat Alert: *"CRITICAL: High-frequency brute force attack detected from 127.0.0.1"*.
     - Risk Score meter elevated to Critical (Score > 0.85).
     - Timeline chart updates with the attack spike.
4. **Demonstrate Deep Investigation & Admin Unblock:**
   - Click on the alert or navigate to **Threat Analysis**.
   - Click **Investigate IP** for `127.0.0.1`.
   - **Show the Sliding-Window ML Feature Vector:**
     - `fail_count_15m`: 5
     - `time_span_seconds`: ~1.2s
     - `fail_rate_per_sec`: ~4.1 ops/sec
     - `entropy_of_passwords`: 2.85
     - `distinct_usernames`: 1
   - Click **Unblock IP** -> IP block is cleared immediately from memory and database.

---

### Phase 4: Proactive Decoy Honeypot (`/admin-login`) (1.5 Minutes)
**Objective:** Demonstrate deception technology isolating attackers and protecting administrative routes.

1. **Explain the Deception Mechanism:**
   - *Speaking Point:* "Attackers and automated vulnerability scanners routinely probe common URL paths like `/admin`, `/admin-login`, and `/wp-login.php`. BruteShield sets up a fake, convincing login trap at `/admin-login` while keeping the real SOC portal at `/dashboard-login`."
2. **Execute Honeypot Attack:**
   ```powershell
   .\venv\Scripts\python.exe attack_simulation.py honeypot
   ```
3. **Show Honeypot Telemetry in SOC Dashboard:**
   - In the SOC Dashboard, click the **Honeypot Decoy** tab.
   - **Show:**
     - Real-time probe logs capturing attacker IP, timestamp, user agent, and targeted username.
     - **Privacy Defense:** The `password_tried` field is masked (`p***d`) so accidental user misdirection does not expose real credentials.

---

### Phase 5: Scientific Evaluation & Research Benchmarks (2 Minutes)
**Objective:** Highlight academic rigor and benchmarking against the Los Alamos National Laboratory (LANL) dataset.

1. **Navigate to:** SOC Dashboard -> **Scientific Benchmarks** tab (`/dashboard/benchmarks`).
2. **Highlight Tripartite Data Partitioning:**
   - **Partition 1 (Operational):** Live local web traffic.
   - **Partition 2 (Synthetic Baseline):** Controlled stress test scenarios.
   - **Partition 3 (LANL Cyber Dataset):** Comprehensive real-world enterprise authentication benchmark.
3. **Key LANL Benchmark Findings:**
   - Model A (Random Forest with Temporal Features): **97.4% Precision**, **94.8% Recall**.
   - Baseline Comparison: BruteShield blocked attackers **84.1% faster** than classic Fail2ban while generating **73% fewer false positives** under distributed attack conditions.

---

## 4. Faculty Q&A Cheat Sheet (Top 10 Questions)

### Q1: Why use Machine Learning instead of a standard Fail2ban counter?
> **Answer:** Standard threshold counters (e.g. 5 fails in 60s) are easily bypassed by **"low-and-slow"** attacks where an attacker waits 61 seconds between attempts, or **password spraying** across thousands of accounts. BruteShield's Random Forest classifier examines multi-dimensional temporal sliding windows (password entropy, request acceleration, username variety, failure ratios), detecting sophisticated attacks even when individual thresholds are never breached.

### Q2: How does the sliding window feature extractor operate in production?
> **Answer:** Feature extraction runs in `O(K)` time where `K` is the number of attempts within the sliding window (default 15 minutes). We use indexed SQLite queries (`WHERE ip = ? AND timestamp > ?`) with Write-Ahead Logging (WAL) and memory caching, resulting in feature computation times under 1.8 milliseconds per request.

### Q3: Why AES-GCM instead of AES-CBC for password vault storage?
> **Answer:** AES-CBC requires separate message authentication (e.g., HMAC-SHA256) and is vulnerable to padding oracle attacks if not implemented flawlessly. AES-GCM is an Authenticated Encryption with Associated Data (AEAD) cipher that computes an authentication tag in hardware (GHASH), providing simultaneous confidentiality and cryptographic integrity. Any tampering with the ciphertext causes immediate decryption failure.

### Q4: How is user privacy preserved during Have I Been Pwned checks?
> **Answer:** We implement **k-Anonymity**. The application computes `SHA-1(password)` and sends only the first 5 hexadecimal characters (20 bits) to the HIBP API. HIBP returns approximately 500 candidate suffix hashes. The application searches locally for the remaining 35 characters. HIBP never sees the user's password or the complete hash.

### Q5: What prevents an attacker from exploiting CSRF or session fixation?
> **Answer:** 
> 1. **CSRF:** All state-changing POST requests require a 256-bit cryptographically secure token stored in the user's session and verified via `secrets.compare_digest()`.
> 2. **Session Fixation:** Upon successful login or privilege change, `session.clear()` is immediately invoked before writing authenticated user identifiers.
> 3. **Cookies:** Enforce `HttpOnly`, `SameSite=Lax`, and `Secure` in production.

### Q6: What happens if an external attacker tries to brute-force the Honeypot?
> **Answer:** Honeypot endpoints (`/admin-login`) intentionally do not validate CSRF tokens so automated bots are trapped without friction. Every attempt records the probe into `honeypot_logs`, triggers high-priority SOC alerts, and can instantly blacklist the offending IP.

### Q7: How does BruteShield prevent database locking under high concurrent load?
> **Answer:** SQLite is configured with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and a `busy_timeout = 5000` milliseconds. In WAL mode, concurrent readers never block writers, and writers never block readers.

### Q8: What dataset was used to validate the model, and how was data leakage avoided?
> **Answer:** We evaluated the engine against the Los Alamos National Laboratory (LANL) Comprehensive Multi-Source Cyber-Security Events dataset. Strict boundary embargoes and forward-chaining temporal cross-validation were enforced: training data strictly preceded testing data chronologically, avoiding lookahead bias.

### Q9: Can an attacker spoof their IP address using the `X-Forwarded-For` header?
> **Answer:** No. BruteShield's `get_client_ip()` resolves IP addresses from `X-Forwarded-For` *only* if the immediate peer IP matches the configured `TRUSTED_PROXIES` whitelist (e.g. our Nginx reverse proxy). Untrusted clients cannot inject fake IP headers.

### Q10: What are the project deliverables and audit records?
> **Answer:** The repository includes:
> - `SECURITY_AUDIT.md`: OWASP ASVS 5.0.0 compliance audit.
> - `PENETRATION_TEST_REPORT.md`: OWASP WSTG 4.2 attack test results.
> - `TEST_MATRIX.md`: 50/50 automated test verification log.
> - `DEPENDENCY_AUDIT.md`: pip-audit CVE verification.
> - `DEPLOYMENT_GUIDE.md`: Production WSGI & Nginx configuration.
> - `REAL_DATASET_EVALUATION.md`: LANL benchmark methodology.
