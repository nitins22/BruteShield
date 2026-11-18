# BruteShield — Faculty Demonstration Runbook

**Project:** BruteShield — Adaptive Cybersecurity Defense Engine & SOC Monitoring Platform  
**Duration:** 10–12 minutes  
**Audience:** Project Evaluation Committee, External Examiners, Faculty Guide  

---

## Pre-Flight Checklist

Complete every item before the demonstration begins. Do not proceed if any check fails.

| # | Check | Command / Action | Expected |
|---|---|---|---|
| 1 | Server starts | `python wsgi.py` | Waitress banner, no errors |
| 2 | Database accessible | Server starts without SQLite errors | Clean startup |
| 3 | ML model loads | No `[WARN] Model file not found` in startup output | Model loaded |
| 4 | Dashboard login works | Browse `http://127.0.0.1:5000/dashboard-login`, log in as `dashadmin` / `Dash@Admin1` | Dashboard loads |
| 5 | User login works | Browse `http://127.0.0.1:5000/login`, log in as `admin` / `Secure@123` | Login success |
| 6 | HIBP API reachable | `python -c "import requests; r=requests.get('https://api.pwnedpasswords.com/range/5BAA6', timeout=3); print(r.status_code)"` | `200` |
| 7 | Attack simulator targets localhost | `python attack_simulation.py login --dry-run` | Dry-run output, no network calls |
| 8 | Demo credentials available | Username/password pairs noted for live use | Ready |
| 9 | Database is fresh | Delete `logs/bruteshield.db` and restart server for a clean slate, or accept existing data | Clean or acceptable |
| 10 | No sensitive data displayed | Close unrelated browser tabs; hide desktop icons | Clean screen |

**HIBP offline fallback:** If HIBP is unreachable, the application degrades gracefully — it reports `offline_mode` and does not block registration. Mention this during the demo if it occurs.

---

## Presentation Script

### PHASE 1 — Introduction & User Onboarding (~2 minutes)

**Objective:** Present the problem statement and demonstrate proactive client-side security.

**Speaker notes:**
> "BruteShield protects web applications against automated credential attacks — brute force, credential stuffing, and password spraying. Rather than a simple attempt counter, it uses Machine Learning anomaly detection on behavioural features extracted from a sliding time window."

**Steps:**

1. Navigate to `http://127.0.0.1:5000/signup`.
2. **Weak password demonstration:**
   - Enter username: `demo_student`
   - Enter password: `password123`
   - Show: zxcvbn rates this as "Weak" (score 0–1). Shannon entropy is low (~25 bits). Registration is rejected.
3. **HIBP k-Anonymity demonstration:**
   - Enter password: `Password1!`
   - Show: The system queries the Have I Been Pwned API using k-Anonymity. Only the first 5 characters of the SHA-1 hash are sent over the network; the full password is never transmitted.
   - Show breach count warning if the password is found.
   - **Accuracy note:** k-Anonymity means the HIBP server cannot determine which specific password was checked from the ~500 candidate hashes returned. It does not mean the check is fully anonymous — the client's IP is still visible to the HIBP API server.
4. **Successful registration:**
   - Enter a strong password (e.g., `K8#mQ9!vL2$xP5@wR7`).
   - Show: Entropy > 60 bits, zxcvbn score 4, registration succeeds.

**Recovery if step fails:** If HIBP is unreachable, explain offline fallback. If signup fails for another reason, use the pre-existing `admin` account.

---

### PHASE 2 — Password Vault (~2 minutes)

**Objective:** Demonstrate encrypted credential storage with tamper detection.

**Steps:**

1. Log in at `http://127.0.0.1:5000/login` with the newly created account (or `admin` / `Secure@123`).
2. Navigate to `http://127.0.0.1:5000/vault`.
3. **Store a credential:**
   - Service: `AWS Console`
   - Username: `ops@example.com`
   - Password: `SuperSecretDemo2026#`
   - Click Encrypt & Save.
4. **Show database stores no plaintext:**
   - Open a second terminal:
   ```powershell
   .\venv\Scripts\python.exe -c "import sqlite3; conn=sqlite3.connect('logs/bruteshield.db'); rows=conn.execute('SELECT service_name, encrypted_password, nonce FROM vault_items ORDER BY id DESC LIMIT 1').fetchall(); print(rows); conn.close()"
   ```
   - Show: `encrypted_password` contains base64-encoded ciphertext; `nonce` contains a 12-byte random IV. No plaintext.
5. **Explain encryption architecture:**
   > "Each vault entry is encrypted using AES-256-GCM with a unique 96-bit random nonce. GCM is an Authenticated Encryption mode — it provides both confidentiality and a 128-bit authentication tag. If even a single bit of the ciphertext is modified, decryption fails with an `InvalidTag` error."
   
   > "The encryption key is derived from `BRUTESHIELD_VAULT_KEY`, a server-side 32-byte master key. The server holds both the ciphertext and the key, so this is server-side encryption at rest — not a zero-knowledge architecture. The user trusts the server with the key."

**Recovery if step fails:** If vault save fails, verify login session is active and retry.

---

### PHASE 3 — Brute-Force Protection & Adaptive Cooldown (~2 minutes)

**Objective:** Demonstrate BruteShield detecting and blocking an automated attack in real time.

**Steps:**

1. **Open SOC Dashboard** in one browser tab:
   - `http://127.0.0.1:5000/dashboard-login`
   - Log in: `dashadmin` / `Dash@Admin1`
2. **Run attack simulation** in terminal:
   ```powershell
   .\venv\Scripts\python.exe attack_simulation.py login --max-attempts 15
   ```
3. **Watch terminal output:**
   - Attempts 1–3: Failed login attempts logged.
   - Attempt ~4: CAPTCHA friction challenge triggered (adaptive escalation).
   - Attempt ~5: ML behavioural anomaly detected → IP blocked on cooldown.
4. **Show SOC Dashboard response:**
   - Refresh or check the dashboard.
   - Show: HIGH-priority alert generated with block duration.
   - Show: Recent activity feed shows the failed attempt burst.
5. **Explain escalation ladder:**
   > "Block durations escalate: 60 seconds → 300 seconds → 900 seconds → 3600 seconds. Repeat offenders face progressively longer lockouts. This is the adaptive cooldown mechanism."

**Recovery if step fails:** If the IP is already blocked from a previous test, unblock via the dashboard Investigate panel, or delete `logs/bruteshield.db` and restart.

---

### PHASE 4 — Honeypot Decoy (~1.5 minutes)

**Objective:** Demonstrate deception technology trapping scanner probes.

**Steps:**

1. **Explain concept:**
   > "Automated vulnerability scanners and attacker reconnaissance tools probe common paths like /admin-login. BruteShield deploys a convincing fake login page at `/admin-login` that records every probe while the real administrative portal is at `/dashboard-login`."
2. **Run honeypot simulation:**
   ```powershell
   .\venv\Scripts\python.exe attack_simulation.py honeypot --max-attempts 5
   ```
3. **Show honeypot logs in dashboard:**
   - In the SOC Dashboard, check the Honeypot section.
   - Show: Probes captured with IP, timestamp, and attempted username.
   - Show: The `password_tried` field displays a masked value (e.g., `pa***rd (8 chars)`) — raw submitted passwords are not stored in the database.

**Recovery if step fails:** If honeypot page returns an error, verify server is running and retry.

---

### PHASE 5 — SOC Dashboard & Research Benchmarks (~2–3 minutes)

**Objective:** Demonstrate operational monitoring and present research evaluation results.

**Steps:**

1. **Overview tab:** Show live security metrics — total attempts, blocked IPs, active alerts, recent activity timeline.
2. **Threats tab:** Show active threat alerts with severity levels (HIGH/MEDIUM/INFO). Demonstrate alert acknowledgement.
3. **Investigate tab:** Show the ML feature vector for a suspicious IP — total attempts, failed attempts, distinct usernames, average gap, minimum gap, failure ratio.
4. **System tab:** Show model metadata — model type (IsolationForest), feature count (6), sliding window (900s).
5. **Benchmarks tab:**
   - **Clearly distinguish three data partitions:**
     - **Operational telemetry:** Live data from this running instance.
     - **Synthetic benchmark:** Simulated 300 normal + 190 attacker IPs (Phase 1).
     - **LANL research benchmark:** Los Alamos National Laboratory enterprise authentication dataset evaluation (Phase 2B).
   - **LANL results (actual verified values):**
     - Dataset: Days 0–2.31 empirical slice, 21.26M retained authentication events (Kerberos/NTLM), 10 exact-second red-team matches in slice out of 749 total.
     - Experiment A (Temporal Generalization): Isolation Forest achieved 75% recall, 0.14% precision, ROC-AUC 0.8026. One-Class SVM achieved 50% recall with ROC-AUC 0.9382.
     - Experiment B (Unseen-Identity): All models scored 0 TP, 0 FN (single-class test set, ROC-AUC undefined).
     - Custom Fail2ban baseline: 8,921 blocks triggered, 0% episode coverage — threshold-based counters failed completely on the LANL attack patterns.

> [!IMPORTANT]
> "These are results from a 2.31-day empirical time slice, not the full 58-day LANL dataset. The dataset contains enterprise Active Directory authentication (Kerberos/NTLM) events, not interactive web logins. The evaluation demonstrates that BruteShield's sliding-window behavioural features transfer to enterprise authentication telemetry."

**Recovery if step fails:** If dashboard data is empty, run the attack simulation first to generate telemetry.

---

### PHASE 6 — Conclusion (~30–60 seconds)

**Key talking points:**

1. **Main technical contribution:** Behavioural ML anomaly detection using 6 sliding-window features, replacing static threshold counters.
2. **Security architecture:** Defense-in-depth with CSRF protection, session fixation mitigation, AES-256-GCM vault, HIBP k-Anonymity, password masking in honeypot logs, and production secret enforcement.
3. **ML contribution:** Isolation Forest anomaly detector trained on synthetic attack telemetry, evaluated against real LANL enterprise data. Catches low-and-slow attacks that evade Fail2ban.
4. **Limitations:** SQLite limits concurrent write throughput; the LANL evaluation used a 2.31-day slice (not the full 58-day dataset); the model was trained on synthetic data, not production attack traffic.
5. **Current deployment scope:** Local development and demonstration. Production deployment guide provided but not executed on a public server.
6. **Future work:** PostgreSQL migration for concurrent deployments, real-time WebSocket dashboard updates, distributed IP reputation, additional ML models (LSTM sequence models), and integration with SIEM platforms.

---

## Faculty Viva — Technical Q&A (20+ Questions)

### Q1. Why was BruteShield developed?

**Short:** To demonstrate that ML-based behavioural analysis detects attacks that static threshold counters miss — specifically low-and-slow and distributed credential attacks.

**Detailed:** Traditional defences like Fail2ban block an IP after a fixed number of failures (e.g., 5 in 60 seconds). An attacker who waits 61 seconds between attempts, or distributes attempts across many IPs, evades this entirely. BruteShield extracts temporal and behavioural features from a sliding window and feeds them to an Isolation Forest anomaly detector, which learns the statistical distribution of normal authentication traffic and flags deviations.

---

### Q2. What is the difference between brute-force and credential-stuffing attacks?

**Short:** Brute force tries many passwords against one account; credential stuffing replays known username/password pairs from previous breaches across multiple accounts.

**Detailed:** In brute force, the attacker iterates through a password dictionary targeting a single username. In credential stuffing, the attacker has a list of compromised credentials (from a data breach) and tests each against the target site, typically one attempt per credential pair. BruteShield's `distinct_usernames` feature helps distinguish these — high distinct username counts suggest credential stuffing.

---

### Q3. How are the six ML features extracted?

**Short:** From all login attempts by a given IP within the most recent 900-second sliding window: total attempts, failed attempts, distinct usernames, average inter-attempt gap, minimum gap, and failure ratio.

**Detailed:** `get_features_for_ip()` queries `login_attempts WHERE ip = ? AND timestamp >= (now - 900)`, ordered by timestamp ascending. It computes:
1. `total_attempts` — count of rows.
2. `failed_attempts` — count where `success = 0`.
3. `distinct_usernames` — `len(set(username))`.
4. `avg_gap` — mean of consecutive timestamp differences.
5. `min_gap` — minimum timestamp gap (detects burst speed).
6. `failure_ratio` — `failed / total`.

---

### Q4. Why was Isolation Forest selected?

**Short:** It is an unsupervised anomaly detector that does not require labelled attack data for training — only examples of normal traffic.

**Detailed:** Isolation Forest works by randomly partitioning features with recursive splits. Anomalies (rare, different points) require fewer splits to isolate, producing shorter average path lengths. The `decision_function` returns a continuous anomaly score: negative values indicate anomalies (prediction = −1). This suits our use case because we have abundant normal login telemetry but limited labelled attack data.

---

### Q5. Why was One-Class SVM evaluated?

**Short:** As a second unsupervised anomaly detection baseline to compare against Isolation Forest.

**Detailed:** One-Class SVM fits a hyperplane (or hypersphere in RBF kernel space) around normal data, then classifies points outside the boundary as anomalies. In the LANL evaluation (Experiment A), One-Class SVM achieved the best ROC-AUC (0.9382) and lowest false positive rate (1.45%), but lower recall (50%) compared to Isolation Forest (75%).

---

### Q6. Why is Random Forest included as a supervised comparison?

**Short:** To benchmark a supervised model against the unsupervised approaches, using the LANL red-team labels.

**Detailed:** Random Forest requires labelled training data (attack vs. normal). In the LANL evaluation, it was trained with partition-local ambiguity embargoes. It achieved lower recall (25%) and higher FPR (10.51%) than both unsupervised models, suggesting that the small number of red-team events in the training partition provided insufficient positive examples for effective supervised learning.

---

### Q7. How does the anomaly-score orientation work?

**Short:** Isolation Forest `decision_function()` returns negative scores for anomalies and positive scores for normal points. `predict()` returns −1 for anomalies and +1 for normal.

**Detailed:** The score threshold is at 0. Scores between 0 and `CAPTCHA_SCORE_LIMIT` (0.06) trigger a CAPTCHA challenge (borderline suspicious). Scores below 0 trigger a full block. This continuous scoring allows graduated defensive response rather than a binary decision.

---

### Q8. How is the anomaly threshold selected?

**Short:** The Isolation Forest's default `contamination` parameter sets the threshold during training. The `CAPTCHA_SCORE_LIMIT` (0.06) defines the borderline warning band.

**Detailed:** During training on synthetic data (`train_synthetic.py`), the contamination parameter estimates the proportion of anomalies in the training set. At inference time, `decision_function()` returns the raw anomaly score. The configurable `CAPTCHA_SCORE_LIMIT` creates a soft zone: scores just above 0 but below 0.06 trigger CAPTCHA friction before escalating to a block.

---

### Q9. Why is a 900-second sliding window used?

**Short:** 15 minutes captures both fast bursts and slower distributed attacks while keeping the query scope manageable.

**Detailed:** A very short window (e.g., 60 seconds) misses low-and-slow attacks that spread attempts over several minutes. A very long window (e.g., 24 hours) accumulates stale data from resolved incidents, diluting current attack signals. 900 seconds balances detection sensitivity against computational cost — the indexed SQLite query `WHERE ip = ? AND timestamp >= ?` runs in under 2 milliseconds.

---

### Q10. Why is a 300-second stride used in the LANL evaluation?

**Short:** The 300-second (5-minute) stride controls how frequently the sliding window is re-evaluated across the LANL timeline.

**Detailed:** With a 900-second window and 300-second stride, consecutive evaluation windows overlap by 600 seconds (66%). This ensures that attack episodes are captured even if they begin partway through a window. The stride is an evaluation parameter — the production application evaluates features on every login attempt, not at fixed time intervals.

---

### Q11. How do low-and-slow attacks differ from fast brute force?

**Short:** Low-and-slow attacks use long delays between attempts to stay below threshold-based detection. Fast brute force sends rapid-fire requests.

**Detailed:** A fast brute-force attack might send 10 attempts in 2 seconds. A low-and-slow attack might send one attempt every 30–120 seconds. Fail2ban's "5 failures in 60 seconds" rule never triggers because the attacker paces below the threshold. BruteShield's ML features — particularly `failure_ratio`, `avg_gap`, and `distinct_usernames` — capture the cumulative behavioural pattern across the full 900-second window.

---

### Q12. What does the Fail2ban-style baseline measure?

**Short:** It simulates a simple threshold counter: block after 5 failures within 60 seconds. Used to quantify how many LANL attack episodes this approach catches versus BruteShield's ML.

**Detailed:** In the LANL evaluation, the custom Fail2ban state machine triggered 8,921 blocks. However, 100% of these were background-only blocks (false alarms on normal enterprise authentication bursts). Zero blocks were associated with actual red-team attack episodes. BruteShield's ML anomaly detector identified 100% of the low-and-slow proxy episodes that Fail2ban missed entirely.

---

### Q13. How is the LANL dataset structured?

**Short:** It contains 58 days of enterprise authentication events from Los Alamos National Laboratory, including 749 known red-team (simulated attacker) events.

**Detailed:** The dataset includes Kerberos ticket requests and NTLM authentication events — not interactive web logins. Each record contains: timestamp (seconds), source user, destination user, source computer, destination computer, authentication type, logon type, authentication orientation, and success/failure status. Red-team events are listed in a separate `redteam.txt` file with user, source computer, destination computer, and timestamp.

---

### Q14. What are the limitations of LANL failure-record visibility?

**Short:** The dataset records successful and failed authentications but does not distinguish between human password mistakes and automated attacks.

**Detailed:** The red-team labels identify which events were part of the controlled attack exercise, but the authentication telemetry itself does not contain attack metadata. Failed authentications could represent legitimate users mistyping passwords, expired Kerberos tickets, or actual attacks. BruteShield's evaluation matched red-team timestamps to authentication failures using greedy 1-to-1 matching with ±2 second tolerance.

---

### Q15. How are red-team events matched?

**Short:** Greedy 1-to-1 matching by (source user, destination user, source computer, destination computer, timestamp ±2 seconds).

**Detailed:** First pass: exact-second matches (Δτ = 0). Second pass: tolerance matches (0 < |Δτ| ≤ 2 seconds). Both passes use greedy 1-to-1 assignment — each red-team event matches at most one authentication event. The Hopcroft-Karp bipartite matching algorithm was run as a diagnostic to verify that greedy matching did not miss any optimal assignments (difference = +0).

---

### Q16. What do PR-AUC and ROC-AUC measure?

**Short:** ROC-AUC measures discrimination between anomalies and normals at all thresholds. PR-AUC (Average Precision) is more informative under class imbalance.

**Detailed:** ROC-AUC plots True Positive Rate vs. False Positive Rate. With extreme class imbalance (4 positive events vs. 30,000+ negative windows), a model can achieve high ROC-AUC while producing many false positives. PR-AUC (Precision vs. Recall) is more sensitive to this — it reflects whether the model's positive predictions are correct. In Experiment A, Isolation Forest had ROC-AUC 0.8026 but AP (Average Precision) of only 0.0023, reflecting the fundamental difficulty of the task.

---

### Q17. Why is AES-GCM used for vault encryption?

**Short:** AES-GCM provides authenticated encryption — both confidentiality and tamper detection — in a single operation.

**Detailed:** AES-GCM (Galois/Counter Mode) is an AEAD (Authenticated Encryption with Associated Data) cipher. It encrypts with AES in counter mode and simultaneously computes a 128-bit GMAC authentication tag over the ciphertext. If any bit of the ciphertext is modified, `AESGCM.decrypt()` raises `InvalidTag` and returns nothing. This prevents padding oracle attacks that affect unauthenticated modes like AES-CBC. Each vault entry uses a unique 96-bit random nonce (`os.urandom(12)`).

---

### Q18. How does HIBP k-Anonymity work?

**Short:** The application sends only the first 5 characters of the SHA-1 hash of the password to the HIBP API. HIBP returns ~500 candidate suffixes, and the application checks for a match locally.

**Detailed:** `hashlib.sha1(password.encode(), usedforsecurity=False)` computes the SHA-1 hash. The first 5 hex characters (20 bits) are sent to `api.pwnedpasswords.com/range/{prefix}`. The API returns all hash suffixes matching that prefix. The application compares the remaining 35 hex characters locally. The HIBP server learns only the prefix — it cannot determine which of the ~500 returned candidates was the actual password hash.

---

### Q19. How is honeypot telemetry protected?

**Short:** Raw submitted passwords are never stored in the honeypot logs. Only a masked representation and the password length are recorded.

**Detailed:** `log_honeypot_attempt()` calls `mask_password(password)` before database insertion. For a password like `mysecretpassword`, the stored value is `my***rd (16 chars)`. The first 2 and last 2 characters are retained for investigative context, but the full password is never persisted. This prevents accidental credential exposure if a legitimate user mistakenly enters their real password on the honeypot page.

---

### Q20. How is BruteShield deployed using WSGI?

**Short:** `wsgi.py` creates the Flask application using the application factory and exposes a WSGI-compatible `app` object. External servers (Waitress/Gunicorn) import this object.

**Detailed:** `wsgi.py` calls `create_app(Config)` to initialise the Flask application, database, blueprints, and middleware. Waitress (Windows) runs `waitress.serve(app, ...)` with configurable threads. Gunicorn (Linux) forks worker processes, each importing `wsgi:app`. Neither Waitress nor Gunicorn handles TLS — a reverse proxy (Nginx/Caddy) terminates HTTPS in front of the WSGI server.

---

### Q21. Why does BruteShield use SQLite instead of PostgreSQL?

**Short:** SQLite requires zero infrastructure setup, runs embedded in the Python process, and is sufficient for single-server demonstration and development.

**Detailed:** BruteShield is a B.Tech capstone project designed for local execution and faculty demonstrations. SQLite provides ACID transactions, WAL mode for concurrent readers, and requires no separate database server. For production deployment serving hundreds of concurrent users, migration to PostgreSQL would be recommended to support concurrent writers and connection pooling.

---

### Q22. How does CSRF protection work in BruteShield?

**Short:** Every state-changing POST request must include a 256-bit CSRF token that is generated per session, stored in a secure HttpOnly cookie, and verified server-side using constant-time comparison.

**Detailed:** `generate_csrf_token()` creates `secrets.token_hex(32)` and stores it in `session["_csrf_token"]`. Templates include the token in a hidden form field. The `check_csrf_token()` before-request hook verifies the submitted token against the session token using `secrets.compare_digest()` (constant-time to prevent timing attacks). The honeypot `/admin-login` is intentionally exempt so automated scanner scripts can be trapped.

---

### Q23. What is the sliding-window feature extraction time complexity?

**Short:** O(K) where K is the number of login attempts in the window, plus O(log N) for the indexed SQLite lookup.

**Detailed:** The SQLite query uses the `idx_login_attempts_ip_time` composite index on `(ip, timestamp)`, making the lookup O(log N). Feature computation (gap calculation, distinct username set, failure ratio) is O(K) where K is typically small (< 50 attempts in a 15-minute window). Measured production latency is under 2 milliseconds per evaluation.

---

### Q24. How does session fixation mitigation work?

**Short:** On successful login, `session.clear()` is called before writing the authenticated user's identity, ensuring the pre-authentication session ID cannot be reused.

**Detailed:** If an attacker obtains a session cookie before the victim authenticates, session fixation allows the attacker to hijack the session after login. BruteShield prevents this by clearing all session data (which causes Flask to issue a new session cookie) immediately before writing `session["user_id"]`, `session["username"]`, and `session["role"]`.
