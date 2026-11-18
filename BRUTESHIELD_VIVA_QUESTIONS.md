# BruteShield — Faculty Viva Voce & Technical Defence Guide
## 50 Comprehensive Examination Questions with Technical & Practical Explanations

**Project Title:** BruteShield: Adaptive Cybersecurity Defense Engine & Live SOC Monitoring Platform  
**Target Domain:** Application Security, Applied Machine Learning, Network Authentication, Threat Detection  
**Target Audience:** Internal Faculty Guides, External University Examiners, Technical Viva Committees  

---

## Navigation Matrix

- [Category A: Project Understanding & Problem Motivation (Q1 – Q8)](#category-a-project-understanding--problem-motivation)
- [Category B: Cybersecurity Concepts & Threat Vectors (Q9 – Q16)](#category-b-cybersecurity-concepts--threat-vectors)
- [Category C: Machine Learning & Feature Engineering (Q17 – Q28)](#category-c-machine-learning--feature-engineering)
- [Category D: Cryptography & Data Protection (Q29 – Q36)](#category-d-cryptography--data-protection)
- [Category E: Dataset, LANL Research & Experimental Benchmark (Q37 – Q44)](#category-e-dataset-lanl-research--experimental-benchmark)
- [Category F: Software Architecture, WSGI & Production Deployment (Q45 – Q52)](#category-f-software-architecture-wsgi--production-deployment)

---

## Category A: Project Understanding & Problem Motivation

### Q1. What is BruteShield, and what fundamental problem does it solve?
- **Short Spoken Answer:** BruteShield is an adaptive authentication defense platform and SOC monitor that uses machine learning anomaly detection to detect low-and-slow, distributed, and high-frequency login attacks that bypass traditional fixed-threshold counters.
- **Detailed Technical Answer:** Conventional defenses (such as classic Fail2ban or basic lockout counters) rely on static rules (e.g., $N$ failures in $T$ seconds). Attackers easily bypass these rules by pacing requests ("low-and-slow") or distributing attempts across multiple accounts (password spraying). BruteShield addresses this by extracting multi-dimensional temporal and statistical features across a 900-second sliding window and evaluating them with an Isolation Forest model to detect anomalous authentication velocities and patterns.
- **BruteShield Implementation Example:** In `bruteshield/ml/engine.py`, `get_features_for_ip()` aggregates attempts over 15 minutes, and `is_suspicious_by_ml()` flags behavioral deviations even when fixed thresholds are not breached.
- **Likely Follow-Up:** *Why did you choose 900 seconds instead of a shorter or longer window?*
- **Hinglish Explanation:** *Normal systems me fixed rule hota hai ki 5 baar galat password dala toh block. Attacker kya karta hai ki har 65 second me ek try karega aur rule bypass ho jayega. BruteShield 15 minute ke sliding window me behavior pattern analyze karke aise attacks ko pakad leta hai.*

---

### Q2. What are the key technical contributions of BruteShield?
- **Short Spoken Answer:** Our main contributions are: (1) a 6-dimensional temporal sliding-window feature extractor; (2) an unsupervised ML anomaly detector evaluated on the empirical LANL cyber dataset; (3) an adaptive escalation cooldown ladder; (4) a zero-knowledge AES-256-GCM vault; and (5) a proactive honeypot decoy with masked credential telemetry.
- **Detailed Technical Answer:** The project bridges real-time anomaly detection with practical web security:
  1. Feature engineering that captures attack velocity (`min_gap`, `avg_gap`), target breadth (`distinct_usernames`), and error density (`failure_ratio`).
  2. Multi-tier defensive escalation: Normal $\rightarrow$ Math CAPTCHA friction $\rightarrow$ Exponential cooldown lockout (60s, 300s, 900s, 3600s).
  3. Deception technology via `/admin-login` capturing scanner probes while isolating the true SOC gateway at `/dashboard-login`.
  4. Real-time SOC dashboard with pure client-side HTML5 canvas charts and strict tripartite data partitioning.
- **BruteShield Implementation Example:** The complete defensive escalation is managed in `bruteshield/routes/auth_routes.py` (lines 30–106) and `bruteshield/ml/engine.py` (lines 146–171).
- **Likely Follow-Up:** *Is this a purely theoretical prototype or an actual working application?*
- **Hinglish Explanation:** *BruteShield sirf ek model nahi hai balki pura system hai: Flask application, real database, AES encryption vault, decoy honeypot, aur live SOC dashboard.*

---

### Q3. How does BruteShield differ from an off-the-shelf login security plugin?
- **Short Spoken Answer:** Most standard plugins only count failed logins per IP or apply static CAPTCHAs. BruteShield combines continuous ML anomaly scoring, adaptive cooldowns, zero-knowledge encrypted storage, and deception traps within an integrated SOC architecture.
- **Detailed Technical Answer:** Off-the-shelf plugins (like WordPress Limit Login Attempts) are stateless or maintain rudimentary attempt counters in memory or cache. They lack: (1) multi-user spraying detection; (2) continuous mathematical scoring of inter-arrival distributions; (3) client-side entropy & k-anonymity validation before registration; and (4) cryptographic tamper detection on stored vault data.
- **BruteShield Implementation Example:** The calculation of `distinct_usernames` in `bruteshield/ml/engine.py:58` instantly differentiates between single-user brute force and broad enterprise password spraying.
- **Likely Follow-Up:** *How does your system handle legitimate users who simply forget their password?*
- **Hinglish Explanation:** *Market me jo plugins hote hain wo bas count karte hain. BruteShield dekhta hai ki ek IP se kitne alag usernames try ho rahe hain, time gap kitna fast hai, aur pehle CAPTCHA challenge deta hai bina seedhe block kiye.*

---

### Q4. What is the scope and boundary of this B.Tech CSE project?
- **Short Spoken Answer:** The project is scoped as an application-layer defense engine and SOC monitoring platform for web applications. It covers user authentication, vault management, real-time threat detection, and offline benchmarking on synthetic and LANL enterprise datasets.
- **Detailed Technical Answer:** BruteShield operates at Layer 7 (Application Layer). It does not inspect raw TCP/IP packet payloads or implement kernel-level firewalling (e.g., `iptables` / eBPF), but it provides application-level request filtering, HTTP rate-limiting coordination, and exportable SOC security telemetry.
- **BruteShield Implementation Example:** The Flask application factory in `bruteshield/__init__.py` defines the security boundary with CSRF protection, secure cookie flags, and custom HTTP response headers.
- **Likely Follow-Up:** *Could BruteShield be deployed in front of an existing legacy system without changing its code?*
- **Hinglish Explanation:** *Ye Layer 7 web security application hai. Iska scope user login, password vault, ML anomaly detection, aur SOC dashboard telemetry tak hai.*

---

### Q5. What are the known limitations of the current BruteShield prototype?
- **Short Spoken Answer:** Key limitations are: SQLite's single-writer concurrency constraint under extreme load, lack of distributed cache synchronization across multiple servers, and offline fallback when the external HIBP API is unreachable.
- **Detailed Technical Answer:** (1) Concurrency: SQLite WAL mode permits concurrent readers, but writes are serialized; (2) Distributed state: In a multi-instance cluster, in-memory model inference and SQLite state require migration to Redis and PostgreSQL; (3) External dependency: Have I Been Pwned API checks depend on outbound internet connectivity, though our code includes graceful offline fallback.
- **BruteShield Implementation Example:** In `bruteshield/database.py:16`, `PRAGMA busy_timeout = 5000;` prevents immediate database locks, but high concurrency requires PostgreSQL.
- **Likely Follow-Up:** *What would you change if you were scaling this to 100,000 active users?*
- **Hinglish Explanation:** *Limitations ye hain ki SQLite use ho raha hai jo enterprise me PostgreSQL hona chahiye, aur agar internet down ho toh HIBP check offline fallback pe chala jata hai.*

---

### Q6. How did you structure the Git engineering lifecycle across the project?
- **Short Spoken Answer:** We followed a disciplined six-stage Git checkpoint workflow: Stage 1 (Core app), Stage 2 (ML & LANL), Stage 3 (SOC UI/UX), Stage 4 (Security audit & 50 tests), Stage 5 (WSGI & 75 tests), and Stage 6 (Final submission & research paper).
- **Detailed Technical Answer:** Every major milestone was developed without altering protected baseline models, committed to Git with structured commit messages, verified against automated regression tests, and tagged with immutable Git tags (`checkpoint-stage1` through `checkpoint-stage6`).
- **BruteShield Implementation Example:** The Git repository history shows commits `c737664`, `17e759c`, `23a8e68`, `9012c5c`, `70834fc`, `06094d6`, and tags matching every stage.
- **Likely Follow-Up:** *Did you ever have to revert or rewrite your Git history?*
- **Hinglish Explanation:** *Humne step-by-step 6 checkpoints banaye hain Git tags ke saath. Har stage ke baad full regression tests pass huye hain tabhi aage badhe hain.*

---

### Q7. How does BruteShield ensure that experimental research data does not contaminate live operational telemetry?
- **Short Spoken Answer:** Through strict architectural data partitioning: live operational logs, synthetic benchmark baselines, and LANL empirical research metrics are isolated into separate backend pipelines and UI views.
- **Detailed Technical Answer:** Operational logs reside in SQLite (`login_attempts`, `alerts`). Benchmark metrics reside in immutable static data structures in `bruteshield/benchmarks.py`. The dashboard routes (`/dashboard/api/benchmarks` vs. `/dashboard/api/overview`) query strictly separated endpoints, preventing synthetic stress tests from skewing operational health scores.
- **BruteShield Implementation Example:** In `bruteshield/benchmarks.py:11–130`, `SYNTHETIC_BENCHMARK` and `LANL_BENCHMARK` dictionaries are completely decoupled from database tables.
- **Likely Follow-Up:** *Why is this separation critical for security auditing?*
- **Hinglish Explanation:** *Live system ka data aur research benchmark ka data bilkul alag rakha gaya hai taaki research evaluation se live system ki monitoring confuse na ho.*

---

### Q8. What user roles exist in BruteShield, and how are permissions enforced?
- **Short Spoken Answer:** There are two distinct roles: `user` (access to login, signup, personal encrypted vault) and `admin` (access to the SOC dashboard, threat alerts, ML investigations, and manual IP unblocking).
- **Detailed Technical Answer:** Role-based access control (RBAC) is enforced at the route level using Flask session cookies signed with `BRUTESHIELD_SECRET_KEY`. Standard user routes verify `session.get("user_id")`, while administrative SOC routes strictly enforce `session.get("is_admin") == True` and `session.get("role") == "admin"`.
- **BruteShield Implementation Example:** In `bruteshield/routes/dashboard_routes.py:20–27`, `admin_required` decorator redirects unauthorized or standard users to `/dashboard-login` with a 403 status.
- **Likely Follow-Up:** *Can a regular user access another user's vault items by manipulating the ID parameter (IDOR)?*
- **Hinglish Explanation:** *Do roles hain: normal user jo apna password vault dekhta hai, aur admin jo SOC dashboard monitor karta hai. Route decorators se unauthorized access block hota hai.*

---

## Category B: Cybersecurity Concepts & Threat Vectors

### Q9. What is the fundamental difference between brute-force, credential stuffing, and password spraying?
- **Short Spoken Answer:** Brute force tests many passwords against one account; credential stuffing replays leaked breach credentials across many accounts; password spraying tests one common password across thousands of accounts.
- **Detailed Technical Answer:**
  - **Brute Force:** High-volume vertical attack targeting a single user with a large password list.
  - **Credential Stuffing:** Automated testing of stolen username/password pairs obtained from external data breaches.
  - **Password Spraying:** Horizontal attack testing a few high-probability passwords (e.g., `Company2026!`) against many usernames to stay beneath lockout thresholds.
- **BruteShield Implementation Example:** In `attack_simulation.py`, the `spray` mode iterates across distinct usernames with fixed passwords, while `login` mode tests password dictionaries against a single username.
- **Likely Follow-Up:** *Which feature in your 6-dimensional ML vector detects password spraying?*
- **Hinglish Explanation:** *Brute force ek user pe hazaro password try karta hai. Credential stuffing purane leak huye passwords use karta hai. Password spraying ek password ko hazaro accounts pe try karta hai taaki lockout na ho.*

---

### Q10. What is a "low-and-slow" attack, and why does traditional Fail2ban fail to stop it?
- **Short Spoken Answer:** A low-and-slow attack inserts delays between failed attempts that exceed the monitoring window of traditional threshold counters, evading detection while slowly cracking accounts.
- **Detailed Technical Answer:** Fail2ban typically counts failures within a fixed window (e.g., 5 failures in 60 seconds). If an attacker submits a failure every 65 seconds, the counter resets on each attempt, allowing unlimited attempts indefinitely. BruteShield's 900-second window and `avg_gap` / `failure_ratio` features capture this persistent anomalous pattern.
- **BruteShield Implementation Example:** In the LANL benchmark (`REAL_DATASET_EVALUATION.md:74–77`), Fail2ban caught 0% of low-and-slow attack episodes, whereas BruteShield's ML model identified 100% of them.
- **Likely Follow-Up:** *Why doesn't BruteShield just make the threshold window 24 hours long?*
- **Hinglish Explanation:** *Fail2ban 60 second me 5 galti dekhta hai. Agar attacker har 70 second me ek request bheje toh counter hamesha zero ho jata hai. BruteShield ka 15-minute window is velocity ko pakad leta hai.*

---

### Q11. What is an adaptive escalation cooldown ladder, and how does it prevent Denial of Service against legitimate users?
- **Short Spoken Answer:** Instead of permanently locking accounts or immediately banning IPs for days, the cooldown ladder escalates lockout times progressively: 60s $\rightarrow$ 300s $\rightarrow$ 900s $\rightarrow$ 3600s.
- **Detailed Technical Answer:** Permanent account lockouts create a Denial of Service (DoS) vulnerability where an attacker locks out legitimate users intentionally. BruteShield locks the *source IP*, not the user account, and imposes brief initial cooling periods (60s) which halt automated high-speed bot scripts without imposing severe friction on legitimate human users who make typos.
- **BruteShield Implementation Example:** In `bruteshield/ml/engine.py:155–170`, `block_ip()` inspects `block_counts` and indexes into `Config.BLOCK_DURATIONS = [60, 300, 900, 3600]`.
- **Likely Follow-Up:** *What happens if the attacker rotates IP addresses using a botnet?*
- **Hinglish Explanation:** *Agar pehli baar koi suspicious activity kare toh sirf 60 second ka block milta hai. Agar wo baar-baar repeat kare toh 5 minute, 15 minute, aur 1 ghanta ho jata hai.*

---

### Q12. How does a decoy honeypot trap protect an organization's administrative perimeter?
- **Short Spoken Answer:** Attackers frequently run automated scanners looking for `/admin`, `/admin-login`, or `/wp-login.php`. BruteShield places a fake admin portal at `/admin-login` that traps bots, logs their signatures, and flags their IPs while legitimate staff use `/dashboard-login`.
- **Detailed Technical Answer:** Honeypots act as deception defense. Legitimate users have no reason to ever visit `/admin-login` because legitimate navigation points to `/dashboard-login`. Any traffic reaching the decoy is treated as hostile reconnaissance. The honeypot logs the IP, user agent, attempted username, masks the attempted password, and creates an immediate high-priority SOC alert.
- **BruteShield Implementation Example:** Defined in `bruteshield/routes/honeypot_routes.py:10–38`, where CSRF checks are bypassed intentionally so bot scripts are trapped without throwing client-side CSRF errors.
- **Likely Follow-Up:** *Could an attacker tell that `/admin-login` is a honeypot from the HTML response?*
- **Hinglish Explanation:** *Hackers ke automated tools `/admin` ya `/admin-login` scan karte hain. BruteShield wahan fake page dikhata hai. Jo bhi wahan enter karega wo turant pakda jayega aur alert trigger ho jayega.*

---

### Q13. Why must passwords submitted to a honeypot never be stored in plaintext?
- **Short Spoken Answer:** If a legitimate user accidentally lands on the honeypot page and enters their real password, storing it in plaintext would create a severe data breach vulnerability in the logs.
- **Detailed Technical Answer:** Storing plaintext credentials violates OWASP ASVS V6 and data privacy regulations. If the database is compromised, plaintext honeypot logs expose credentials. BruteShield mitigates this via `mask_password()` which stores only the first two and last two characters along with the total character length (e.g., `pa***rd (8 chars)`).
- **BruteShield Implementation Example:** In `bruteshield/security.py:128–138`, `mask_password()` formats the string, and `log_honeypot_attempt()` in `bruteshield/ml/engine.py:196–210` writes only the masked representation.
- **Likely Follow-Up:** *Why do you store any characters at all rather than a one-way hash?*
- **Hinglish Explanation:** *Agar koi apna real password galti se honeypot me daal de toh database me plain text password leak na ho jaye, isiliye BruteShield usko mask karke store karta hai.*

---

### Q14. How does BruteShield prevent Cross-Site Request Forgery (CSRF)?
- **Short Spoken Answer:** All state-changing POST requests require a cryptographically secure 256-bit random token stored in the session cookie and verified using constant-time comparison.
- **Detailed Technical Answer:** In `bruteshield/__init__.py:24–62`, a `before_request` hook verifies `csrf_token` from request headers or form bodies against `session["_csrf_token"]` using `secrets.compare_digest()`. Requests without valid tokens are rejected with HTTP 403 Forbidden. Safe methods (GET, HEAD, OPTIONS) and the honeypot trap are exempted.
- **BruteShield Implementation Example:** `secrets.compare_digest(token, expected)` prevents timing attacks when comparing token strings.
- **Likely Follow-Up:** *Why is the honeypot explicitly exempted from CSRF verification?*
- **Hinglish Explanation:** *Har POST form me ek secret token hota hai. Agar koi bahar se malicious website ke zariye request bheje toh token match nahi hoga aur request reject ho jayegi.*

---

### Q15. How does BruteShield mitigate Session Fixation attacks?
- **Short Spoken Answer:** Upon successful authentication, the server immediately clears the entire session dictionary before writing authenticated user identifiers, forcing the issuance of a fresh session cookie.
- **Detailed Technical Answer:** In a session fixation attack, an adversary tricks a victim into using a known session ID, waiting for them to log in, and then hijacking the authenticated session. In BruteShield, `session.clear()` is called immediately before `session["user_id"] = user["id"]`, invalidating the pre-authentication session identifier.
- **BruteShield Implementation Example:** In `bruteshield/routes/auth_routes.py:75–78` and `test_session_fixation_mitigation` in `tests/test_security_audit.py:46–64`.
- **Likely Follow-Up:** *What cookie attributes are set to protect this session from theft via JavaScript?*
- **Hinglish Explanation:** *Login hone se pehle ka session data turant delete karke naya session generate kiya jata hai taaki koi purana session hijack na kar sake.*

---

### Q16. How does BruteShield resolve client IP addresses safely behind reverse proxies without trusting spoofed headers?
- **Short Spoken Answer:** We only read the `X-Forwarded-For` header if the direct socket peer address matches our strict `TRUSTED_PROXIES` whitelist; otherwise, `remote_addr` is used directly.
- **Detailed Technical Answer:** Attackers can send arbitrary `X-Forwarded-For: 8.8.8.8` headers in HTTP requests to bypass IP blocks. BruteShield's `get_client_ip()` checks `request.remote_addr`. If it is in `Config.TRUSTED_PROXIES` (e.g., `127.0.0.1` corresponding to our Nginx proxy), it parses the header safely; otherwise, the header is completely ignored.
- **BruteShield Implementation Example:** Verified in `bruteshield/security.py:170–190` and tested in `test_client_ip_resolution` in `tests/test_security.py:46–60`.
- **Likely Follow-Up:** *What happens if an attacker sends multiple comma-separated IPs in X-Forwarded-For?*
- **Hinglish Explanation:** *Agar koi header me fake IP daal de toh BruteShield usko accept nahi karta jab tak request hamare apne trusted Nginx proxy se na aayi ho.*

---

## Category C: Machine Learning & Feature Engineering

### Q17. What are the six machine learning features extracted by BruteShield, and what does each measure?
- **Short Spoken Answer:**
  1. `total_attempts`: overall traffic volume.
  2. `failed_attempts`: count of authentication errors.
  3. `distinct_usernames`: breadth of targets (detects spraying).
  4. `avg_gap`: mean speed of attempts.
  5. `min_gap`: burst speed (detects automated bot scripts).
  6. `failure_ratio`: density of failed logins to total logins.
- **Detailed Technical Answer:** Extracted across the 900-second sliding window by `get_features_for_ip()`:
  $$\vec{x} = [N_{\text{tot}}, N_{\text{fail}}, U_{\text{dist}}, \bar{\Delta t}, \Delta t_{\min}, R_{\text{fail}}]$$
  Where $\bar{\Delta t} = \frac{1}{K-1}\sum_{i=1}^{K-1}(t_{i+1}-t_i)$ and $R_{\text{fail}} = \frac{N_{\text{fail}}}{N_{\text{tot}}}$.
- **BruteShield Implementation Example:** `bruteshield/ml/engine.py:25–72`.
- **Likely Follow-Up:** *What happens to these features when an IP makes its very first request?*
- **Hinglish Explanation:** *Ye 6 features hain: total attempts, failed attempts, kitne alag username try kiye, average time gap, minimum time gap, aur failure ratio.*

---

### Q18. Why was Isolation Forest selected as the primary anomaly detection algorithm?
- **Short Spoken Answer:** Because Isolation Forest is an unsupervised algorithm that explicitly isolates anomalies using binary trees rather than profiling normal data points, making it highly efficient and well-suited for unlabelled authentication streams.
- **Detailed Technical Answer:** Isolation Forest constructs an ensemble of isolation trees (iTrees). Because anomalies have distinct attribute values and are rare, they are isolated closer to the root of the tree, requiring fewer partitions (shorter average path length $h(x)$). The anomaly score is normalized between 0 and 1:
  $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
  Where $c(n) = 2\ln(n - 1) + 0.5772156649 - \frac{2(n-1)}{n}$ is the average path length of unsuccessful searches in a Binary Search Tree.
- **BruteShield Implementation Example:** Loaded in `bruteshield/ml/engine.py:10–23` from `trained_model.pkl`.
- **Likely Follow-Up:** *What is the computational complexity of Isolation Forest during inference?*
- **Hinglish Explanation:** *Isolation Forest unsupervised algorithm hai. Ye anomalous points ko jaldi isolate kar leta hai kyunki abnormal points tree me kam depth pe split ho jate hain.*

---

### Q19. How does Scikit-Learn's `decision_function()` score orientation work in Isolation Forest?
- **Short Spoken Answer:** In Scikit-Learn, negative scores represent anomalies, while positive scores represent normal inliers.
- **Detailed Technical Answer:** Scikit-Learn's `decision_function()` computes the score as an offset from the contamination threshold. A score $< 0.0$ corresponds to `predict() == -1` (anomaly), while a score $\ge 0.0$ corresponds to `predict() == 1` (normal). BruteShield maps scores $< 0.0$ to immediate blocks and scores between $0.0$ and $0.06$ to the CAPTCHA friction band.
- **BruteShield Implementation Example:** Enforced in `bruteshield/ml/engine.py:115–120` and tested in `test_ml_decision_score_orientation` in `tests/test_security_audit.py:214–227`.
- **Likely Follow-Up:** *Why did you add a CAPTCHA friction band between 0.0 and 0.06 instead of a binary block?*
- **Hinglish Explanation:** *Scikit-learn me negative score ka matlab anomaly hota hai aur positive ka matlab normal. BruteShield 0 se 0.06 ke beech borderline cases ko CAPTCHA deta hai.*

---

### Q20. Why was One-Class SVM evaluated as a secondary unsupervised model in Phase 2B?
- **Short Spoken Answer:** One-Class SVM models the density distribution of normal inliers using a non-linear kernel (RBF), serving as a benchmark to compare boundary-based anomaly detection against tree-based isolation.
- **Detailed Technical Answer:** One-Class SVM maps training data into a high-dimensional feature space via kernel function $\Phi(x)$ and finds a maximal-margin hyperplane separating the data from the coordinate origin. In Phase 2B (LANL Experiment A), One-Class SVM achieved the highest ROC-AUC (0.9382) and lowest False Positive Rate (1.45%), but lower recall (50%) than Isolation Forest (75%).
- **BruteShield Implementation Example:** Implemented in `bruteshield/ml/lanl_pipeline.py:114–120` with RBF kernel and $\nu = 0.05$.
- **Likely Follow-Up:** *Why wasn't One-Class SVM chosen as the default model in production?*
- **Hinglish Explanation:** *One-Class SVM data ke charon taraf ek boundary banata hai. Ye mathematically strong hai lekin high data pe memory aur training time zyada leta hai.*

---

### Q21. Why was Random Forest included in the research evaluation if authentication attacks are typically unlabelled?
- **Short Spoken Answer:** Random Forest was included as a supervised upper-bound reference to evaluate how much performance gain is theoretically achievable when ground-truth labels (red-team markers) are available.
- **Detailed Technical Answer:** In real-world web environments, attacks arrive unlabelled. However, to evaluate the efficacy of our 6 features, we trained a supervised Random Forest on the LANL partition using red-team markers. It achieved 25% recall and 10.5% FPR, demonstrating that extreme class imbalance and sparse attack markers make supervised learning challenging without synthetic oversampling.
- **BruteShield Implementation Example:** Evaluated in `REAL_DATASET_EVALUATION.md:56` and `bruteshield/benchmarks.py:85–90`.
- **Likely Follow-Up:** *How did you handle class imbalance when evaluating Random Forest?*
- **Hinglish Explanation:** *Random Forest ek supervised model hai jisko comparison ke liye benchmark kiya gaya taaki dekha ja sake ki agar labels hon toh supervised model kaisa perform karta hai.*

---

### Q22. What is the difference between ROC-AUC and PR-AUC, and why is PR-AUC more informative in cybersecurity?
- **Short Spoken Answer:** ROC-AUC evaluates True Positive Rate vs. False Positive Rate across all thresholds; PR-AUC evaluates Precision vs. Recall. In extreme class imbalance, ROC-AUC can look deceivingly high while Precision is very low.
- **Detailed Technical Answer:** When normal events outnumber attacks by 10,000 to 1, a model can generate thousands of false alarms while maintaining a "low" False Positive Rate (e.g., 2%), yielding an impressive ROC-AUC of 0.93. However, Precision ($\frac{TP}{TP + FP}$) will be extremely low ($< 0.5\%$), which PR-AUC accurately exposes. In SOC environments, false alarms overwhelm human analysts.
- **BruteShield Implementation Example:** Documented in `REAL_DATASET_EVALUATION.md:54–56`, where One-Class SVM achieved ROC-AUC of 0.9382 but Average Precision (PR-AUC) of only 0.0036.
- **Likely Follow-Up:** *What is the operational consequence of an Average Precision of 0.0036?*
- **Hinglish Explanation:** *Agar 1 lakh normal logins me 10 attack hain, toh ROC-AUC 95% dikha sakta hai lekin 99% alerts false alarm honge. PR-AUC precision aur recall dekhta hai jo real security me zyada important hai.*

---

### Q23. Why did you use a 900-second window and a 300-second stride in the LANL pipeline?
- **Short Spoken Answer:** A 900-second (15-minute) window captures temporal attack patterns, and a 300-second (5-minute) stride provides a 66% temporal overlap between successive evaluation windows to prevent missing boundary-crossing attacks.
- **Detailed Technical Answer:** If the stride equals the window length (900s), an attack spanning seconds 890 to 910 is split across two windows, diluting the signal in both. A 300-second stride ensures that any 15-minute attack episode is fully contained within at least two consecutive overlapping analysis windows.
- **BruteShield Implementation Example:** Verified in `bruteshield/ml/lanl_pipeline.py:46–60` and tested in `test_boundary_embargo_guard` in `tests/test_lanl_pipeline.py:80–95`.
- **Likely Follow-Up:** *Does the live Flask web app use a 300-second stride during production requests?*
- **Hinglish Explanation:** *15-minute window aur 5-minute stride se windows aapas me 66% overlap karti hain, jisse boundary pe aane wale attacks miss nahi hote.*

---

### Q24. How does the fallback rule in `is_suspicious_by_rule()` operate if the ML model fails to load?
- **Short Spoken Answer:** If `trained_model.pkl` is missing or corrupted, the system falls back to a deterministic rule: if failed attempts exceed `MAX_FAILED_ATTEMPTS` (5) within `TIME_WINDOW_SECONDS` (60s), the IP is flagged.
- **Detailed Technical Answer:** High availability requires graceful degradation. In `bruteshield/ml/engine.py:74–92`, if `get_ml_model()` returns `None`, an exception is caught and logged, and execution delegates to `is_suspicious_by_rule(ip)`. This ensures authentication protection remains active even during disk errors or model deserialization failures.
- **BruteShield Implementation Example:** In `bruteshield/ml/engine.py:94–104`, SQLite executes:
  `SELECT COUNT(*) FROM login_attempts WHERE ip = ? AND success = 0 AND timestamp >= ?`
- **Likely Follow-Up:** *How would the SOC analyst know that the system is operating in fallback mode?*
- **Hinglish Explanation:** *Agar model file corrupt ya delete ho jaye toh system crash nahi hota, balki automatic standard 5-attempt rule pe fallback kar leta hai.*

---

### Q25. What is the mathematical foundation of Shannon Entropy in BruteShield's password registration?
- **Short Spoken Answer:** It measures the information uncertainty or randomness of the password string in bits:
  $$H(X) = -\sum_{i=1}^{n} p(x_i) \log_2 p(x_i)$$
- **Detailed Technical Answer:** For a password of length $L$ containing character probabilities $p(x_i)$, Shannon entropy quantifies redundancy. If a password repeats characters (e.g., `aaaaaaaa`), $H(X) = 0$. Total entropy is $L \times H(X)$. BruteShield also computes theoretical pool entropy $L \log_2 N$ based on character diversity (lowercase, uppercase, digits, symbols), providing a multi-dimensional strength rating.
- **BruteShield Implementation Example:** In `bruteshield/security.py:12–70`, ratings range from "Very Weak" ($< 28$ bits) to "Cryptographically Strong" ($\ge 80$ bits).
- **Likely Follow-Up:** *Why is Shannon entropy alone insufficient to judge password security?*
- **Hinglish Explanation:** *Shannon entropy string ki randomness ko bits me calculate karti hai. Agar user repeated ya predictable characters dalega toh entropy low aayegi.*

---

### Q26. Why do you combine Shannon Entropy with `zxcvbn` dictionary assessment?
- **Short Spoken Answer:** Shannon entropy measures character distribution randomness, but cannot detect common dictionary words (e.g., `CorrectHorseBatteryStaple`), which have high entropy but are easily cracked by dictionary attacks.
- **Detailed Technical Answer:** `zxcvbn` is a pattern-matching and dictionary modeling library developed by Dropbox. It detects l33tspeak substitutions (`P@ssw0rd`), spatial keyboard walks (`qwertyuiop`), and popular dictionary terms. BruteShield requires both: high information entropy and a `zxcvbn` score $\ge 2$.
- **BruteShield Implementation Example:** In `bruteshield/routes/auth_routes.py:131–151`, registration rejects passwords scoring $< 2$ on `zxcvbn` or found heavily breached in HIBP.
- **Likely Follow-Up:** *Can you give an example of a password that has high Shannon entropy but fails zxcvbn?*
- **Hinglish Explanation:** *Sirf entropy dictionary words nahi pakad sakti. `zxcvbn` common passwords, keyboard patterns, aur substitutions ko pehchan kar score deta hai.*

---

### Q27. What is the Hopcroft-Karp algorithm, and why was it used as a diagnostic in Phase 2B?
- **Short Spoken Answer:** Hopcroft-Karp is a graph algorithm that computes maximum-cardinality bipartite matching in $O(E \sqrt{V})$ time. We used it to verify that our greedy 1-to-1 matching of red-team events was mathematically optimal.
- **Detailed Technical Answer:** When matching red-team attack timestamps to authentication records, multiple events might fall within the $\pm 2$ second tolerance window. To guarantee that greedy tie-breaking did not sacrifice valid matches, Hopcroft-Karp was executed as a formal diagnostic on the bipartite graph of candidate pairs. The cardinality difference was exactly $+0$, proving greedy matching achieved the global optimum.
- **BruteShield Implementation Example:** Implemented in `bruteshield/ml/lanl_pipeline.py:90–108` and verified in `test_hopcroft_karp_diagnostic` in `tests/test_lanl_pipeline.py:65–78`.
- **Likely Follow-Up:** *What would a non-zero Hopcroft-Karp difference have indicated?*
- **Hinglish Explanation:** *Hopcroft-Karp ek bipartite graph matching algorithm hai. Humne verify kiya ki red-team events ko authentication records ke saath match karte waqt koi bhi match chhoot nahi raha.*

---

### Q28. What are left and right episode censoring in temporal cyber security evaluations?
- **Short Spoken Answer:** Censoring occurs when an attack episode starts before the evaluation window opens (left censoring) or continues after the evaluation window closes (right censoring), biasing duration and detection latency metrics.
- **Detailed Technical Answer:** In temporal event streams, treating a truncated episode as complete understates the true attack length or misattributes detection latency. BruteShield's pipeline flags boundary-crossing episodes and applies boundary embargoes (guard intervals) to ensure evaluation windows evaluate clean, uncensored authentication sequences.
- **BruteShield Implementation Example:** In `bruteshield/ml/lanl_pipeline.py:140–165` and `REAL_DATASET_EVALUATION.md:42–50`.
- **Likely Follow-Up:** *How many boundary-crossing episodes were identified in the 2.31-day empirical slice?*
- **Hinglish Explanation:** *Agar koi attack recording start hone se pehle shuru ho chuka ho ya end hone ke baad tak chale, usko censoring kehte hain. Isko track na kiya jaye toh metrics galat aate hain.*

---

## Category D: Cryptography & Data Protection

### Q29. Why does BruteShield use AES-256-GCM instead of AES-CBC for vault credential storage?
- **Short Spoken Answer:** AES-GCM is an Authenticated Encryption with Associated Data (AEAD) cipher that guarantees both confidentiality and cryptographic integrity, completely eliminating padding oracle vulnerabilities inherent to AES-CBC.
- **Detailed Technical Answer:** AES-CBC requires PKCS#7 padding and a separate message authentication code (HMAC) verified under an Encrypt-then-MAC paradigm. If implemented improperly, CBC is vulnerable to padding oracle attacks. AES-GCM uses CTR mode for encryption and computes a 128-bit GHASH authentication tag over the ciphertext and nonce in hardware. Any modification to ciphertext or nonce causes decryption to abort.
- **BruteShield Implementation Example:** `bruteshield/security.py:141–168` and `test_vault_aes_gcm_tamper_detection` in `tests/test_security_audit.py:142–158`.
- **Likely Follow-Up:** *What exact exception does Python's cryptography library raise when ciphertext is modified?*
- **Hinglish Explanation:** *AES-CBC me padding oracle attack ka risk hota hai. AES-GCM authenticated encryption hai: ye encrypt bhi karta hai aur sath me 128-bit tag se verify bhi karta hai ki kisi ne 1 bit bhi change na ki ho.*

---

### Q30. What is a nonce in AES-GCM, and what happens if a nonce is reused with the same key?
- **Short Spoken Answer:** A nonce (Number used ONCE) is an initialization vector. In AES-GCM, reusing a nonce with the same key destroys the authentication guarantee and allows an attacker to recover the GHASH authentication key and forge messages.
- **Detailed Technical Answer:** GCM security depends strictly on nonce uniqueness across all encryptions under key $K$. Nonce reuse leaks the difference of authentication tags, exposing the GHASH key $H = E_K(0^{128})$ and the counter keystream. BruteShield uses a 96-bit (12-byte) cryptographically secure random nonce generated via `os.urandom(12)` on every single `encrypt_vault_secret()` call.
- **BruteShield Implementation Example:** In `bruteshield/security.py:148`, `nonce = os.urandom(12)` and uniqueness is verified in `test_vault_nonce_uniqueness` in `tests/test_security_audit.py:160–174`.
- **Likely Follow-Up:** *Why is a 96-bit nonce preferred over a 128-bit nonce in GCM?*
- **Hinglish Explanation:** *Nonce ka matlab Number Used Once. Agar ek hi key ke saath same nonce do baar use ho jaye toh GCM ki cryptographic security toot jati hai. Isiliye har entry ke liye naya 12-byte random nonce banta hai.*

---

### Q31. How does Have I Been Pwned (HIBP) k-Anonymity work, and what is its mathematical privacy guarantee?
- **Short Spoken Answer:** The client computes $\text{SHA-1}(P)$, sends only the first 5 hexadecimal characters (20 bits) to the API, and receives approximately 500 candidate hash suffixes, performing the final matching locally.
- **Detailed Technical Answer:** Sending passwords or full hashes over the network exposes user credentials. Under $k$-anonymity, an individual's query cannot be distinguished from a group of at least $k$ candidates. The 5-character prefix matches a bucket of $\approx \frac{16^{40-5}}{16^{35}} \approx 500\text{ to }1,000$ known breached hash suffixes. The HIBP server learns only that the user's password hash starts with those 5 characters, not the full hash or password.
- **BruteShield Implementation Example:** In `bruteshield/security.py:72–126` and tested in `test_hibp_privacy_guarantee` in `tests/test_security_audit.py:190–202`.
- **Likely Follow-Up:** *Why is SHA-1 used for HIBP instead of SHA-256 or bcrypt?*
- **Hinglish Explanation:** *Hum HIBP ko pura password ya pura hash nahi bhejte, sirf pehle 5 characters bhejte hain. HIBP wahan se 500 possible suffixes wapas karta hai aur matching local machine pe hoti hai.*

---

### Q32. What is the difference between hashing and encryption in BruteShield?
- **Short Spoken Answer:** Hashing is a one-way mathematical transformation used for passwords (cannot be decrypted); encryption is a two-way transformation used for vault secrets (can be decrypted using the master key).
- **Detailed Technical Answer:** User login passwords stored in `users.password_hash` are hashed using Werkzeug's `generate_password_hash()` (salted Scrypt / PBKDF2-HMAC-SHA256). They cannot be reversed; verification uses `check_password_hash()`. Conversely, vault entries in `vault_items.encrypted_password` must be retrieved by the user, so they are encrypted with two-way AES-256-GCM.
- **BruteShield Implementation Example:** In `bruteshield/database.py:120–125` for hashing and `bruteshield/security.py:141–168` for encryption.
- **Likely Follow-Up:** *Why can't you use AES-256-GCM for user login passwords too?*
- **Hinglish Explanation:** *Login passwords ko hash kiya jata hai taaki koi unhe reverse na kar sake. Vault items ko encrypt kiya jata hai taaki authorized user unhe decrypt karke wapas dekh sake.*

---

### Q33. How does BruteShield prevent Insecure Direct Object References (IDOR) in the password vault?
- **Short Spoken Answer:** Every vault operation strictly binds the database query to the authenticated user's session ID (`WHERE id = ? AND user_id = ?`).
- **Detailed Technical Answer:** In an IDOR vulnerability, user A modifies an ID in a request (e.g., `GET /vault/decrypt/42`) to read user B's secret. BruteShield's `vault_routes.py` extracts `user_id = session.get("user_id")` and executes parameterized queries ensuring that records belonging to other user IDs return a 404/403 error.
- **BruteShield Implementation Example:** Verified in `tests/test_security_audit.py:84–110` (`test_vault_idor_cross_user_isolation`).
- **Likely Follow-Up:** *What HTTP status code is returned if User A queries User B's vault item?*
- **Hinglish Explanation:** *Agar koi user URL me doosre user ka vault ID daal kar secret padhne ki koshish kare, toh database query me `user_id = session['user_id']` match nahi hoga aur access reject ho jayega.*

---

### Q34. How are master keys managed, and how does production mode protect against default key leakage?
- **Short Spoken Answer:** The master keys are read from environment variables (`BRUTESHIELD_SECRET_KEY` and `BRUTESHIELD_VAULT_KEY`). In production mode, the application halts at startup if default keys are detected.
- **Detailed Technical Answer:** In `bruteshield/config.py:17–26`, if `BRUTESHIELD_ENV == "production"`, `Config` inspects both keys. If either matches `DEFAULT_DEMO_SECRET` or `DEFAULT_DEMO_VAULT`, a `RuntimeError` is raised immediately before the Flask app can bind or serve traffic.
- **BruteShield Implementation Example:** Tested in `test_production_secret_enforcement` in `tests/test_security_audit.py:176–188`.
- **Likely Follow-Up:** *How would you safely rotate `BRUTESHIELD_VAULT_KEY` without corrupting existing vault data?*
- **Hinglish Explanation:** *Production mode me application start hi nahi hoti agar demo keys change na ki gayi hon. Key rotation ke liye pehle data purani key se decrypt karke nayi key se re-encrypt karna padta hai.*

---

### Q35. How does BruteShield protect against SQL injection vulnerabilities?
- **Short Spoken Answer:** All database interactions use strictly parameterized SQL queries (`?` parameter binding); dynamic string concatenation of user input into SQL queries is completely forbidden.
- **Detailed Technical Answer:** SQLite's parameterized interface separates SQL command parsing from data literals. Malicious payloads like `' OR '1'='1` are treated purely as string literals, completely preventing query manipulation. Bandit SAST scans verified zero SQL injection risks (CWE-89 / B608).
- **BruteShield Implementation Example:** Tested in `test_sql_injection_resistance` in `tests/test_security_audit.py:124–140`.
- **Likely Follow-Up:** *Did Bandit find any B608 issues during development, and how did you resolve them?*
- **Hinglish Explanation:** *Saari SQL queries me parameterized statements (`?`) use huye hain. Koi bhi user input directly query string me concatanate nahi hota.*

---

### Q36. What Content Security Policy (CSP) headers are implemented, and what attacks do they mitigate?
- **Short Spoken Answer:** We enforce a strict CSP that restricts script execution, disallows framing (`frame-ancestors 'self'`), restricts form submissions, and allows outbound connections only to self and the official HIBP API.
- **Detailed Technical Answer:** In `bruteshield/__init__.py:70–79`, the `apply_security_headers` hook sets:
  `default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self' https://api.pwnedpasswords.com; frame-ancestors 'self';`
  This mitigates Cross-Site Scripting (XSS), clickjacking, and unauthorized outbound data exfiltration.
- **BruteShield Implementation Example:** Tested in `test_security_headers_present` in `tests/test_security_audit.py:204–212`.
- **Likely Follow-Up:** *What does `frame-ancestors 'self'` protect against?*
- **Hinglish Explanation:** *CSP headers browser ko instruct karte hain ki scripts aur external resources kahan se load ho sakte hain. Ye XSS aur clickjacking attacks ko rokte hain.*

---

## Category E: Dataset, LANL Research & Experimental Benchmark

### Q37. What is the Los Alamos National Laboratory (LANL) `cyber1` dataset?
- **Short Spoken Answer:** It is an authentic, publicly released enterprise cybersecurity dataset collected over 58 days from LANL's internal corporate network, containing over 1 billion multi-source security events including red-team attack exercises.
- **Detailed Technical Answer:** Published by Alexander D. Kent (2015), DOI `10.17021/1179829`. It comprises five event streams: Windows Active Directory authentication events (`auth.txt.gz`), process executions (`proc.txt.gz`), network flows (`flows.txt.gz`), DNS queries (`dns.txt.gz`), and red-team attacks (`redteam.txt.gz`).
- **BruteShield Implementation Example:** Documented in `REAL_DATASET_EVALUATION.md:12–17`.
- **Likely Follow-Up:** *What event type in LANL is relevant to BruteShield?*
- **Hinglish Explanation:** *LANL dataset Los Alamos National Lab ka real enterprise security dataset hai jisme internal network ke real authentication events aur red-team attacks recorded hain.*

---

### Q38. What is the exact coverage and boundary of the LANL empirical dataset slice evaluated by BruteShield?
- **Short Spoken Answer:** We evaluated the verified empirical time slice spanning Days 0 to 2.31 ($199,687$ seconds), retaining $21,255,459$ Active Directory authentication events and capturing 10 red-team ground-truth matches.
- **Detailed Technical Answer:** The full LANL dataset is 58 days and several hundred gigabytes. For our B.Tech evaluation pipeline, we ingested the Days 0 to 2.31 time slice ($37,686,637$ raw lines parsed, $16,050,924$ LogOff records excluded, yielding $21,255,459$ retained records). Within this slice, exactly 10 red-team records occurred; the remaining 739 red-team records occurred in days 3 through 58.
- **BruteShield Implementation Example:** Documented in `REAL_DATASET_EVALUATION.md:19–41` and `bruteshield/benchmarks.py:52–65`.
- **Likely Follow-Up:** *Why didn't you evaluate all 58 days?*
- **Hinglish Explanation:** *Full LANL dataset bohot bada hai (hundreds of GBs). Humne verified empirical slice (Days 0 to 2.31) pe pipeline execute kiya jisme 2.12 crore authentication events aur 10 red-team attacks evaluate huye.*

---

### Q39. What is the difference between LANL enterprise authentication telemetry and interactive web logins?
- **Short Spoken Answer:** LANL captures Windows Active Directory Kerberos and NTLM network authentication tokens between workstations and domain controllers; it is not a record of human users typing passwords into web browser forms.
- **Detailed Technical Answer:** Interactive web logins involve HTTP POST requests, browser cookies, and session state. LANL Active Directory events capture Kerberos TGT/TGS ticket requests, service logins (LogonType 3/5), and automated system tokens. Our evaluation demonstrates that BruteShield's sliding-window features transfer successfully to enterprise network authentication streams.
- **BruteShield Implementation Example:** Disclosed in `REAL_DATASET_EVALUATION.md:11` and `FACULTY_DEMO_RUNBOOK.md`.
- **Likely Follow-Up:** *Why is testing on enterprise AD data valuable if BruteShield is a web platform?*
- **Hinglish Explanation:** *Web login me browser se HTTP requests aati hain, jabki LANL me Windows domain controllers ke Kerberos events hain. Ye prove karta hai ki hamare features enterprise network pe bhi apply hote hain.*

---

### Q40. How did you match red-team events to authentication failure records?
- **Short Spoken Answer:** Using greedy 1-to-1 matching across four tuples (source user, destination user, source computer, destination computer) within an exact-second ($\Delta\tau = 0$) or $\pm 2$ second tolerance window.
- **Detailed Technical Answer:** Red-team events in `redteam.txt.gz` contain timestamps and machine IDs, but not event IDs. In `bruteshield/ml/lanl_pipeline.py:65–88`, matching is performed: (1) Exact-second match ($\Delta\tau = 0$), finding 10 exact matches; (2) Secondary tolerance pass ($0 < |\Delta\tau| \le 2\text{s}$), finding 0 additional matches; (3) Verified via Hopcroft-Karp algorithm that greedy tie-breaking achieved the theoretical maximum.
- **BruteShield Implementation Example:** In `REAL_DATASET_EVALUATION.md:32–41`.
- **Likely Follow-Up:** *What happened to the 739 red-team events that did not match in the time slice?*
- **Hinglish Explanation:** *Red-team file me se attack timestamp aur computer match kiye gaye exact second aur 2-second tolerance ke saath. Hopcroft-Karp algorithm se verify kiya ki matching optimal hai.*

---

### Q41. What were the specific results of Experiment A (Temporal Generalization)?
- **Short Spoken Answer:** Isolation Forest achieved 75% recall and ROC-AUC of 0.8026; One-Class SVM achieved 50% recall, the lowest FPR (1.45%), and highest ROC-AUC (0.9382); Random Forest achieved 25% recall and ROC-AUC of 0.8967.
- **Detailed Technical Answer:** Across 30,137 evaluation windows:
  - **Isolation Forest:** $\text{TP}=3, \text{FP}=2134, \text{FN}=1, \text{TN}=27999$, $\text{Precision}=0.0014$, $\text{Recall}=0.7500$, $\text{FPR}=0.0708$, $\text{ROC-AUC}=0.8026$.
  - **One-Class SVM:** $\text{TP}=2, \text{FP}=436, \text{FN}=2, \text{TN}=29697$, $\text{Precision}=0.0046$, $\text{Recall}=0.5000$, $\text{FPR}=0.0145$, $\text{ROC-AUC}=0.9382$.
  - **Random Forest:** $\text{TP}=1, \text{FP}=3166, \text{FN}=3, \text{TN}=26967$, $\text{Precision}=0.0003$, $\text{Recall}=0.2500$, $\text{FPR}=0.1051$, $\text{ROC-AUC}=0.8967$.
- **BruteShield Implementation Example:** Verified in `REAL_DATASET_EVALUATION.md:52–57`.
- **Likely Follow-Up:** *Why did Isolation Forest achieve the highest recall?*
- **Hinglish Explanation:** *Experiment A me Isolation Forest ne 75% attacks detect kiye, jabki One-Class SVM ne sabse kam false positives (1.45%) aur best ROC-AUC (0.9382) diya.*

---

### Q42. Why is ROC-AUC reported as `N/A` in Experiment B (Unseen-Identity Generalization)?
- **Short Spoken Answer:** Because the test partition for Experiment B contains only negative (normal) baseline instances and zero positive attack instances; ROC-AUC is mathematically undefined when a class is absent.
- **Detailed Technical Answer:** ROC-AUC requires calculating the True Positive Rate ($\frac{TP}{TP + FN}$). When positive instances are zero ($P = 0$), the denominator is zero, making TPR mathematically undefined ($\frac{0}{0}$). Rather than fabricating a metric, BruteShield correctly reports `N/A`, reporting the Active-Window FPR (9.07% for IF, 12.28% for OC-SVM).
- **BruteShield Implementation Example:** In `REAL_DATASET_EVALUATION.md:59–64` and `bruteshield/benchmarks.py:101–102`.
- **Likely Follow-Up:** *What did Experiment B test if there were no attacks in the test set?*
- **Hinglish Explanation:** *Agar test set me koi attack hua hi na ho, toh True Positive Rate divide by zero ho jata hai. Isiliye humne fake value likhne ke bajaye mathematically correct `N/A` likha hai.*

---

### Q43. How did the custom Fail2ban baseline perform against LANL attack episodes?
- **Short Spoken Answer:** Fail2ban triggered 8,921 false alarm blocks on normal enterprise background activity, but achieved 0% detection of actual red-team attack episodes.
- **Detailed Technical Answer:** Real enterprise users occasionally generate burst logins (scripts, Kerberos ticket renewal spikes), tripping Fail2ban's static 5-attempt counter 8,921 times. Conversely, red-team attacks in the LANL dataset were paced and distributed, completely evading Fail2ban's fixed window. In contrast, BruteShield's ML engine caught 100% of the marker-bounded low-and-slow proxy episodes.
- **BruteShield Implementation Example:** Documented in `REAL_DATASET_EVALUATION.md:66–77`.
- **Likely Follow-Up:** *What does this reveal about traditional rule-based security in enterprise environments?*
- **Hinglish Explanation:** *Fail2ban ne normal background noise pe 8,921 baar false block lagaya, lekin real red-team attacks ko zero pakda kyunki attacks slow aur spaced out the.*

---

### Q44. How were boundary embargoes enforced in the temporal cross-validation?
- **Short Spoken Answer:** We enforced a temporal guard interval between training and test sets so that sliding windows in the training set could not overlap with or leak information into the test set.
- **Detailed Technical Answer:** In time-series modeling, standard random k-fold cross-validation causes lookahead bias. BruteShield uses chronological forward-chaining partitioning. A boundary embargo equal to the sliding window duration ($W = 900\text{ seconds}$) is inserted at the boundary, ensuring training data strictly precedes test data in time.
- **BruteShield Implementation Example:** In `bruteshield/ml/lanl_pipeline.py:125–138` and tested in `test_boundary_embargo_guard` in `tests/test_lanl_pipeline.py:80–95`.
- **Likely Follow-Up:** *What would happen if you trained and tested on randomly shuffled login records?*
- **Hinglish Explanation:** *Time series me data leak na ho, isiliye training data aur testing data ke beech me 900 second ka embargo (gap) rakha gaya taaki future ka data past me leak na ho.*

---

## Category F: Software Architecture, WSGI & Production Deployment

### Q45. What is WSGI, and why is the Flask development server unsuitable for production?
- **Short Spoken Answer:** WSGI (Web Server Gateway Interface) is the Python standard for web servers communicating with applications. The Flask built-in development server is single-threaded, lacks process supervision, and leaks sensitive debug information upon exceptions.
- **Detailed Technical Answer:** The Flask built-in server (`Werkzeug`) is intended solely for local debugging. It lacks security hardening, request queue management, worker process recycling, and protection against slowloris attacks. In production, a hardened multi-threaded WSGI server like Waitress (Windows) or Gunicorn (Linux) is required.
- **BruteShield Implementation Example:** `wsgi.py` exposes `app = create_app(Config)` with debug hardcoded to `False`, running via Waitress or Gunicorn.
- **Likely Follow-Up:** *Does Waitress natively terminate HTTPS/TLS?*
- **Hinglish Explanation:** *Flask ka built-in server sirf testing ke liye hota hai. Production me multi-threaded WSGI server (jaise Waitress ya Gunicorn) chahiye jo crash na ho aur heavy traffic handle kare.*

---

### Q46. What is the role of Waitress vs. Gunicorn in BruteShield's deployment architecture?
- **Short Spoken Answer:** Waitress is the officially supported multi-threaded WSGI server for Windows production environments; Gunicorn is the multi-process WSGI server used for Linux systemd deployments.
- **Detailed Technical Answer:** Gunicorn relies on POSIX `fork()` system calls which do not exist natively on Windows. Waitress is pure Python, operates reliably across Windows and POSIX, handles slowloris attacks, and manages worker thread pools without requiring Unix fork semantics.
- **BruteShield Implementation Example:** Launchers in `run_production.bat` (Waitress) and `run_production.sh` (Gunicorn/Waitress).
- **Likely Follow-Up:** *Why do we run Gunicorn in the foreground under systemd?*
- **Hinglish Explanation:** *Windows pe Gunicorn nahi chal sakta kyunki POSIX fork nahi hota, isiliye Windows pe Waitress use hota hai aur Linux pe Gunicorn.*

---

### Q47. What is SQLite WAL mode, and why is it critical for BruteShield?
- **Short Spoken Answer:** Write-Ahead Logging (WAL) allows concurrent readers to read from the database without blocking writers, and writers to write without blocking readers.
- **Detailed Technical Answer:** In standard rollback journal mode, SQLite locks the entire database file during writes, causing `database is locked` errors during concurrent login bursts. In WAL mode (`PRAGMA journal_mode=WAL`), changes are written to a separate `.db-wal` file. Readers read from the database and WAL file concurrently without locking writers.
- **BruteShield Implementation Example:** In `bruteshield/database.py:15`, `conn.execute("PRAGMA journal_mode=WAL;")` and `conn.execute("PRAGMA busy_timeout=5000;")`.
- **Likely Follow-Up:** *How do you safely back up an SQLite database while WAL transactions are active?*
- **Hinglish Explanation:** *Standard SQLite me write ke time pura DB lock ho jata tha. WAL mode me concurrent reads aur writes sath me chal sakte hain bina database lock huye.*

---

### Q48. How does the SQLite Online Backup API work, and why is simply copying `bruteshield.db` unsafe?
- **Short Spoken Answer:** Simply copying the `.db` file while writes are occurring can copy half-written pages, producing a corrupted backup. SQLite's online backup API locks pages safely and creates a consistent snapshot.
- **Detailed Technical Answer:** SQLite's `sqlite3_backup_step()` (exposed in Python via `source_conn.backup(dest_conn)`) copies pages while holding a shared lock, checkpointing WAL data atomically. In `scripts/demo_setup.py:100–125`, our backup tool executes this API and verifies the backup with `PRAGMA integrity_check`.
- **BruteShield Implementation Example:** Tested in `test_backup_and_integrity` in `tests/test_stage5.py:102–140`.
- **Likely Follow-Up:** *What command checks the structural integrity of the restored database?*
- **Hinglish Explanation:** *Agar running database file ko direct copy-paste karoge toh corrupted copy ban sakti hai. Python ka `backup()` API atomic consistent snapshot banata hai.*

---

### Q49. What is the reverse proxy architecture when deploying BruteShield behind Nginx?
- **Short Spoken Answer:** Nginx acts as the public-facing gateway on port 443, terminating TLS, serving static files directly, enforcing rate limits, and proxying HTTP requests to Waitress/Gunicorn on `127.0.0.1:5000`.
- **Detailed Technical Answer:** Nginx handles high-concurrency client connections, HTTP-to-HTTPS 301 redirection, modern TLS ciphers (TLS 1.2/1.3), gzip compression, and rate limiting (`limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m`). It passes clean traffic to the WSGI backend along with `X-Forwarded-For` and `X-Real-IP`.
- **BruteShield Implementation Example:** Detailed configuration provided in `DEPLOYMENT_GUIDE.md:140–210`.
- **Likely Follow-Up:** *Why should static files (`/static/`) be served by Nginx rather than Python?*
- **Hinglish Explanation:** *Nginx public internet pe port 443 pe baithta hai, HTTPS/SSL sambhalta hai, rate limiting karta hai, aur clean requests andar Waitress server ko forward karta hai.*

---

### Q50. How does the SOC Live Dashboard render charts without external CDN dependencies?
- **Short Spoken Answer:** It uses a custom offline JavaScript engine that draws directly onto HTML5 `<canvas>` elements, ensuring full functionality in air-gapped or sandboxed environments.
- **Detailed Technical Answer:** External CDNs (like Chart.js or Google Fonts) introduce privacy leakage, latency, and failure points in air-gapped SOC environments. BruteShield's `static/js/soc-charts.js` implements a custom canvas drawing library that renders threat bar charts, sliding-window feature sparklines, and timeline distributions using pure vanilla JavaScript.
- **BruteShield Implementation Example:** `static/js/soc-charts.js` and `templates/dashboard.html`.
- **Likely Follow-Up:** *How often does the dashboard poll for new telemetry?*
- **Hinglish Explanation:** *Dashboard me koi external Chart.js library ya CDN use nahi kiya gaya. Pure HTML5 canvas pe offline render hota hai taaki secure SOC environments me bina internet ke bhi chale.*

---

### Q51. What happens during pre-flight verification before a live faculty demonstration?
- **Short Spoken Answer:** We run `python scripts/demo_setup.py verify`, which checks database integrity, ML model file size, Waitress installation, Flask application creation, and HIBP network reachability.
- **Detailed Technical Answer:** Pre-flight checks prevent live demonstration glitches:
  1. `PRAGMA integrity_check` on SQLite database.
  2. Verified existence and size of `trained_model.pkl` (2,372 KB).
  3. Import verification of `waitress` and `create_app()`.
  4. HIBP range endpoint connectivity test (with graceful offline fallback documentation).
- **BruteShield Implementation Example:** In `scripts/demo_setup.py:65–98`.
- **Likely Follow-Up:** *What do you do if an examiner asks you to simulate an attack live?*
- **Hinglish Explanation:** *Demo dene se pehle `demo_setup.py verify` run karke database, model file, waitress aur application factory check kar lete hain taaki koi error na aaye.*

---

### Q52. If an examiner asks you to unblock an IP during the demo, how do you do it?
- **Short Spoken Answer:** We open the SOC Dashboard as `dashadmin`, go to the "Threats" or "Investigate" tab, enter the IP, view its extracted ML feature vector, and click the "Unblock IP" button.
- **Detailed Technical Answer:** The "Unblock IP" button sends a POST request with CSRF token to `/dashboard/api/unblock-ip`, executing `DELETE FROM blocked_ips WHERE ip = ?`. The IP is instantly cleared from quarantine, allowing immediate re-testing.
- **BruteShield Implementation Example:** In `bruteshield/routes/dashboard_routes.py:120–135` and `bruteshield/ml/engine.py:256–263`.
- **Likely Follow-Up:** *Does unblocking an IP also clear its history in `login_attempts`?*
- **Hinglish Explanation:** *SOC dashboard me Investigate drawer khol kar 'Unblock IP' click karte hain. Ye database se blocked_ips entry delete kar deta hai aur IP turant unblock ho jati hai.*

---

## Final Viva Advice for the Student

> [!TIP]
> 1. **Be Honest About Scope:** Emphasize that BruteShield is an application-layer defense engine tested on synthetic data and a verified 2.31-day empirical slice of the LANL enterprise dataset.
> 2. **Never Claim 58 Days:** If asked about LANL duration, state clearly: *"Our evaluation was executed on the verified Days 0 to 2.31 empirical slice ($21.26\text{M}$ records) under the approved Phase 2B research protocol."*
> 3. **Explain Low Precision Confidently:** If asked why LANL precision is $0.0014$, explain: *"In extreme class imbalance ($4$ attacks out of $30,000$ test windows), even a very low false positive rate of $7\%$ produces a low precision. This is why ROC-AUC alone is deceptive, and why we implemented tiered friction (CAPTCHA) rather than immediate permanent bans."*
