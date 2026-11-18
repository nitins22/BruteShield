# BruteShield — Central Evidence Register & Verification Matrix

This register serves as the authoritative source of truth for all academic deliverables in Stage 6 (Final B.Tech Project Report, Authentic Research Paper, Viva Defence, Presentation Slides, and Handover). Every empirical, technical, architectural, and experimental claim made across all submission files is mapped to verified repository evidence.

---

## 1. System Metadata & Academic Context

| Parameter | Verified Repository Value | Academic Reporting Guidance |
|---|---|---|
| **Project Title** | BruteShield: Adaptive Cybersecurity Defense Engine & SOC Monitoring Platform | Full formal title |
| **Project Domain** | Application Security, Applied Machine Learning, Cyber Defense | CSE Capstone Domain |
| **Technology Stack** | Python 3.12, Flask 3.1.3, SQLite3 (WAL mode), Scikit-Learn 1.9.1, Cryptography 50.0.2, zxcvbn 4.5.0, Waitress 3.0.2 | Verified from `requirements.txt` & runtime |
| **Institutional Affiliation** | Department of Computer Science & Engineering, ABES Engineering College, Ghaziabad | Verified from repository docs |
| **Student / Author Name(s)** | `[STUDENT INPUT REQUIRED]` | Insert student full name |
| **University Roll / Enrollment No.**| `[STUDENT INPUT REQUIRED]` | Insert university roll number |
| **Faculty Guide / Supervisor** | `[STUDENT INPUT REQUIRED]` | Insert guide name and designation |
| **Academic Year / Session** | 2025–2026 (Final Year B.Tech CSE) | Standard academic session |

---

## 2. Core Architecture & Implementation Evidence

| Component | Source File Reference | Verified Implementation Details |
|---|---|---|
| **App Factory & Middleware** | `bruteshield/__init__.py` | Blueprint registration, CSRF middleware with 256-bit token (`secrets.token_hex(32)`), security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) |
| **Database Architecture** | `bruteshield/database.py` | 8 SQLite tables: `users`, `login_attempts`, `blocked_ips`, `block_counts`, `honeypot_logs`, `alerts`, `alert_acknowledgements`, `vault_items`. Indexed on `(ip, timestamp)`. `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;` |
| **Password Vault Cryptography**| `bruteshield/security.py` | Authenticated AES-256-GCM (`cryptography.hazmat.primitives.ciphers.aead.AESGCM`). 96-bit random nonce (`os.urandom(12)`), 128-bit authentication tag. Ciphertext and nonce stored base64-encoded. Zero plaintext in DB. Tamper detection verified via `InvalidTag` exception. |
| **Password Strength Engine** | `bruteshield/security.py` & `routes/auth_routes.py` | Shannon entropy $H(X) = -\sum p(x)\log_2 p(x)$ + pool size entropy $L\log_2 N$. Dictionary crack estimation via `zxcvbn`. Minimum score 2 enforced for registration. |
| **Breach Audit (k-Anonymity)** | `bruteshield/security.py` | `hashlib.sha1(password, usedforsecurity=False)`. Only first 5 hex characters sent to `api.pwnedpasswords.com/range/{prefix}`. Range suffix matching locally. Offline fallback graceful degradation (`offline_mode`). |
| **Decoy Honeypot Trap** | `bruteshield/routes/honeypot_routes.py` | Trap at `/admin-login` with convincing administrative interface. Excluded from CSRF checks so automated scripts are caught. Passwords masked via `mask_password()` (`p***d (8 chars)`). Zero plaintext passwords stored. |
| **Adaptive Escalation Ladder** | `bruteshield/ml/engine.py` | Normal $\rightarrow$ Arithmetic CAPTCHA challenge $\rightarrow$ Cooldown Ladder: 60s $\rightarrow$ 300s $\rightarrow$ 900s $\rightarrow$ 3600s. Tracked via `block_counts` table. |
| **Client IP Resolution** | `bruteshield/security.py` | Resolves `X-Forwarded-For` and `X-Real-IP` **only** when `remote_addr` matches `TRUSTED_PROXIES` whitelist (default `127.0.0.1,::1`). Prevents IP spoofing. |
| **Production WSGI Server** | `wsgi.py`, `run_production.bat`, `run_production.sh` | Waitress (Windows, multi-threaded) and Gunicorn (Linux, systemd foreground). Debug mode hardcoded `False`. Mandatory production secrets enforced. |

---

## 3. Machine Learning & Feature Engineering Evidence

| Item | Source Implementation | Mathematical / Operational Definition |
|---|---|---|
| **Observation Window** | `bruteshield/config.py` | $W = 900\text{ seconds}$ (15 minutes). Captures low-and-slow velocity. |
| **Sliding Stride (LANL)** | `bruteshield/ml/lanl_pipeline.py` | $S = 300\text{ seconds}$ (5 minutes). 66% temporal overlap between successive evaluation windows. |
| **Feature 1: `total_attempts`** | `bruteshield/ml/engine.py:53` | Count of all login records in window: $\vert\{r \in \text{Attempts} \mid t(r) \ge t_{\text{now}} - W\}\vert$ |
| **Feature 2: `failed_attempts`** | `bruteshield/ml/engine.py:57` | Count of failures in window: $\vert\{r \mid t(r) \ge t_{\text{now}} - W \land r.\text{success} = 0\}\vert$ |
| **Feature 3: `distinct_usernames`**| `bruteshield/ml/engine.py:58` | Variety of targets: $\vert\{r.\text{username} \mid t(r) \ge t_{\text{now}} - W\}\vert$ (detects password spraying) |
| **Feature 4: `avg_gap`** | `bruteshield/ml/engine.py:63` | Mean time between successive attempts: $\frac{1}{K-1}\sum_{i=1}^{K-1} (t_{i+1} - t_i)$ |
| **Feature 5: `min_gap`** | `bruteshield/ml/engine.py:64` | Minimum time between consecutive attempts: $\min_{i} (t_{i+1} - t_i)$ (detects automated bot bursts) |
| **Feature 6: `failure_ratio`** | `bruteshield/ml/engine.py:69` | Proportion of failures: $\frac{\text{failed\_attempts}}{\text{total\_attempts}}$ |
| **Primary Anomaly Model** | `bruteshield/ml/engine.py:10` | Isolation Forest (`sklearn.ensemble.IsolationForest`). Unsupervised. |
| **Decision Thresholds** | `bruteshield/config.py` | `raw_score < 0.0` $\rightarrow$ Anomaly Block; `0.0 <= raw_score < 0.06` $\rightarrow$ CAPTCHA Friction Challenge; `raw_score >= 0.06` $\rightarrow$ Normal Traffic. |
| **Feature Extraction Latency** | Production Measurement | $1.8\text{ ms}$ per request via indexed composite SQLite query. |

---

## 4. Protected Model Artifacts Integrity Evidence

| File Path | Verified SHA-256 Checksum | Preserved Status |
|---|---|:---:|
| `trained_model.pkl` | `0F42590F98026B54B3F9C570C37F05E57A5A013DA6C3DC3CB2E9E5421CD48E8F` | **UNCHANGED** |
| `data/lanl/trained_model_real_expA.pkl` | `9FCFC7AD2A087E4DFB6B41269ADFEFEAE2141579BB90F4AC9793592EADD918B8` | **UNCHANGED** |
| `data/lanl/trained_model_real_expB.pkl` | `805983C67ABC8B865526FC92DD865EBC06E66577E711B32387B6BE9B2986AD06` | **UNCHANGED** |

---

## 5. Experimental Results: Synthetic vs. Real-World Datasets

### A. Synthetic Benchmark (Phase 1 Baseline)
- **Population:** 300 normal users, 190 simulated attackers (490 total test IPs).
- **Model vs. Rule Metrics:**
  - Accuracy: ML **96.5%** vs. Rule 83.5%
  - Precision: ML **94.8%** vs. Rule 99.1%
  - Recall: ML **96.3%** vs. Rule 57.9%
  - F1-Score: ML **0.956** vs. Rule 0.731
  - Average Block Attempt: ML **3.6 attempts** vs. Rule 5.0 attempts
- **Attack Vector Catch Rates:**
  - Fast Brute Force: ML 100%, Rule 100%
  - Credential Stuffing (multi-user): ML 100%, Rule 100%
  - Low-and-Slow (12s–60s gaps): ML **100%**, Rule **0%**
  - Stealthy (3–4 attempts only): ML **77%**, Rule **0%**

### B. LANL Enterprise Cyber Security Dataset Benchmark (Phase 2B)
- **Dataset Citation:** Alexander D. Kent, *Comprehensive, Multi-Source Cyber-Security Events*, Los Alamos National Laboratory, 2015. DOI: [10.17021/1179829](http://dx.doi.org/10.17021/1179829).
- **Approvals & Rights:** LANL HSRRB Approval LANL 14-07 X; Public Release LA-UR-15-23810; CC0 1.0 Universal Rights Waiver.
- **CRITICAL DATASET BOUNDARY DISCLOSURE:**
  - Evaluated on verified empirical time slice: **Days 0 to 2.31** (maximum timestamp $t = 199,687\text{ seconds}$).
  - Raw records parsed: $37,686,637$ lines.
  - Logoff records excluded: $16,050,924$.
  - Retained authentication events: $21,255,459$.
  - Red-team records in artifact: 749 total.
  - Red-team records occurring inside empirical slice: **10** (1.34%).
  - Red-team records outside time slice: **739** (98.66%).
  - Matching: 10 exact-second matches ($\Delta\tau = 0$), 0 tolerance matches ($0 < \vert\Delta\tau\vert \le 2\text{s}$), Hopcroft–Karp diagnostic difference: $+0$.
  - **Academic Integrity Note:** This represents an enterprise Active Directory (Kerberos/NTLM) network dataset, not interactive web HTTP logins. Complete 58-day research results were not evaluated; only the verified Days 0–2.31 empirical slice is reported.

#### Experiment A: Temporal Generalization (Days 0–2.31)
| Model | TP | FP | FN | TN | Precision | Recall | F1-Score | Active-Window FPR | Average Precision (AP) | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| **Isolation Forest** | 3 | 2,134 | 1 | 27,999 | 0.0014 | **0.7500** | 0.0028 | 0.0708 | 0.0023 | 0.8026 |
| **One-Class SVM** | 2 | 436 | 2 | 29,697 | 0.0046 | 0.5000 | 0.0090 | **0.0145** | **0.0036** | **0.9382** |
| **Random Forest** | 1 | 3,166 | 3 | 26,967 | 0.0003 | 0.2500 | 0.0006 | 0.1051 | 0.0008 | 0.8967 |

#### Experiment B: Unseen-Identity Generalization
| Model | TP | FP | FN | TN | Precision | Recall | F1-Score | Active-Window FPR | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|
| **Isolation Forest** | 0 | 597 | 0 | 5,983 | 0.0 | 0.0 | 0.0 | 0.0907 | N/A (Single-class test set) |
| **One-Class SVM** | 0 | 808 | 0 | 5,772 | 0.0 | 0.0 | 0.0 | 0.1228 | N/A (Single-class test set) |
| **Random Forest** | 0 | 762 | 0 | 5,818 | 0.0 | 0.0 | 0.0 | 0.1158 | N/A (Single-class test set) |

#### Custom Fail2ban-Style Baseline Comparison (LANL Telemetry)
- Total threshold blocks triggered: **8,921**
- Episode-associated blocks (actual attack detection): **0** (0.00%)
- Background-only blocks (false alarms on normal user spikes): **8,921** (100.00%)
- LANL-observed low-and-slow proxy episode catch rate: ML Anomaly **100.00%** vs. Fail2ban **0.00%**.

---

## 6. Testing, Quality & Security Audit Evidence

| Audit Domain | Verification Tool | Quantitative Result | Status |
|---|---|---|:---:|
| **Full Automated Regression Suite** | `pytest tests/ -v` | **75 / 75 Tests Passed** (100% Green in 24.79s) | Verified |
| **Static Code Analysis (SAST)** | `bandit -r bruteshield/ app.py wsgi.py ...` | **0 Issues Identified** (High: 0, Med: 0, Low: 0 across 3,003 LOC) | Verified |
| **Known Dependency Vulnerabilities**| `pip-audit` | **0 Known CVEs** across all production dependencies | Verified |
| **OWASP ASVS 5.0.0 Checklist** | `SECURITY_AUDIT.md` | Verification across V2 (Auth), V3 (Session), V5 (Validation), V6 (Crypto), V8 (Errors) | Documented |
| **Penetration Testing (WSTG 4.2)** | `PENETRATION_TEST_REPORT.md` | Attack simulations against SQLi, XSS, IDOR, Session Fixation, Brute Force | Documented |

---

## 7. Verified Research Literature Citations (With Real DOIs)

1. **A. D. Kent**, "Comprehensive, Multi-Source Cyber-Security Events," *Los Alamos National Laboratory*, 2015. DOI: `10.17021/1179829`.
2. **F. T. Liu, K. M. Ting, and Z.-H. Zhou**, "Isolation Forest," *Eighth IEEE International Conference on Data Mining (ICDM)*, pp. 413–422, 2008. DOI: `10.1109/ICDM.2008.17`.
3. **B. Schölkopf, J. C. Platt, J. Shawe-Taylor, A. J. Smola, and R. C. Williamson**, "Estimating the Support of a High-Dimensional Distribution," *Neural Computation*, vol. 13, no. 7, pp. 1443–1471, 2001. DOI: `10.1162/089976601750541816`.
4. **L. Breiman**, "Random Forests," *Machine Learning*, vol. 45, no. 1, pp. 5–32, 2001. DOI: `10.1023/A:1010933404324`.
5. **C. E. Shannon**, "A Mathematical Theory of Communication," *Bell System Technical Journal*, vol. 27, no. 3, pp. 379–423, 1948. DOI: `10.1002/j.1538-7305.1948.tb01338.x`.
6. **D. A. McGrew and J. Viega**, "The Galois/Counter Mode of Operation (GCM)," *NIST Special Publication 800-38D*, National Institute of Standards and Technology, Gaithersburg, MD, 2007. DOI: `10.6028/NIST.SP.800-38D`.
7. **C. Dwork**, "Differential Privacy," in *Automata, Languages and Programming (ICALP)*, Lecture Notes in Computer Science, vol. 4052, Springer, Berlin, Heidelberg, pp. 1–12, 2006. DOI: `10.1007/11787006_1`.
8. **J. E. Hopcroft and R. M. Karp**, "An $n^{5/2}$ algorithm for maximum matchings in bipartite graphs," *SIAM Journal on Computing*, vol. 2, no. 4, pp. 225–231, 1973. DOI: `10.1137/0202019`.
9. **P. Tarjan**, "Data Structures and Network Algorithms," *Society for Industrial and Applied Mathematics (SIAM)*, Philadelphia, PA, 1983. DOI: `10.1137/1.9781611970265`.
10. **T. Hunt**, "Have I Been Pwned: Pwned Passwords API v2 (k-Anonymity Mathematical Model)," *Cloudflare Security Research*, 2018. Available: `https://www.troyhunt.com/ive-just-launched-pwned-passwords-v2/`.
