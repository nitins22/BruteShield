"""
BruteShield — Academic Diagram & Visual Asset Generator
---------------------------------------------------------
Generates Mermaid source definitions (.mmd), standalone SVG vector graphics,
and high-resolution PNG images for all 11 system architecture and design diagrams.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

DIAGRAM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "final-submission", "diagrams"))
os.makedirs(DIAGRAM_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. MERMAID SOURCE DEFINITIONS
# ---------------------------------------------------------------------------
MERMAID_DIAGRAMS = {
    "fig1_system_architecture.mmd": """graph TB
    subgraph Client_Layer [Client & Network Layer]
        Browser[Web Browser / SOC Analyst]
        Scanner[Automated Attacker / Bot Scanner]
    end

    subgraph Reverse_Proxy_Layer [Reverse Proxy / TLS Termination]
        Nginx[Nginx / Caddy Reverse Proxy]
        TLS[TLS 1.2 / 1.3 Termination]
        RateLimiter[Connection Rate Limiting]
    end

    subgraph WSGI_Application_Layer [WSGI Server & Flask Application Engine]
        WSGIServer[Waitress / Gunicorn WSGI Server]
        CSRFMiddleware[CSRF & Security Headers Middleware]
        AuthModule[Authentication & Entropy Engine]
        VaultModule[Zero-Knowledge AES-256-GCM Vault]
        HoneypotModule[Decoy Honeypot Trap (/admin-login)]
        DashboardModule[SOC Telemetry & Real-Time Analytics]
        MLEngine[Behavioral Anomaly Engine & Sliding Window]
    end

    subgraph Machine_Learning_Pipeline [Machine Learning Pipeline]
        ModelLoader[Trained Model / Isolation Forest]
        FeatureExtractor[6-Dimensional Sliding Window Extractor]
        DecisionScorer[Continuous Anomaly Scoring Engine]
    end

    subgraph Persistence_Layer [Persistence & Storage Layer]
        SQLiteDB[(SQLite Database - WAL Mode)]
        UsersTable[(users & vault_items)]
        TelemetryTable[(login_attempts & honeypot_logs)]
        AlertsTable[(alerts & blocked_ips)]
    end

    Browser --> Nginx
    Scanner --> Nginx
    Nginx --> TLS --> RateLimiter --> WSGIServer
    WSGIServer --> CSRFMiddleware
    CSRFMiddleware --> AuthModule
    CSRFMiddleware --> VaultModule
    CSRFMiddleware --> DashboardModule
    Scanner -.->|Targeting /admin-login| HoneypotModule
    AuthModule --> FeatureExtractor
    FeatureExtractor --> ModelLoader --> DecisionScorer
    DecisionScorer -->|Borderline| AuthModule
    DecisionScorer -->|Anomaly Block| AlertsTable
    AuthModule --> UsersTable
    AuthModule --> TelemetryTable
    VaultModule --> UsersTable
    HoneypotModule --> TelemetryTable
    DashboardModule --> SQLiteDB
""",

    "fig2_user_authentication_flow.mmd": """sequenceDiagram
    autonumber
    actor User as User / Attacker
    participant Proxy as Reverse Proxy (Nginx)
    participant Auth as Auth Controller (/login)
    participant Sec as Security Engine (IP & Cooldown)
    participant ML as ML Anomaly Engine
    participant DB as SQLite Database (WAL)

    User->>Proxy: POST /login (username, password, csrf_token)
    Proxy->>Auth: Forward with X-Forwarded-For
    Auth->>Sec: Check IP status & active cooldown
    alt IP is actively blocked
        Sec-->>Auth: Blocked (remaining cooldown seconds)
        Auth-->>User: 429 Too Many Requests / Cooldown Template
    else IP is not blocked
        Auth->>ML: Evaluate needs_captcha(IP)
        alt Borderline anomaly score (0.0 <= score < 0.06)
            ML-->>Auth: CAPTCHA Challenge Required
            Auth->>Auth: Verify arithmetic challenge
        end
        Auth->>DB: Query users WHERE username = ?
        DB-->>Auth: User record (password_hash)
        Auth->>Auth: Verify check_password_hash(hash, password)
        Auth->>DB: INSERT INTO login_attempts (ip, user, success, timestamp)
        alt Authentication Successful
            Auth->>Auth: session.clear() (Session Fixation Defense)
            Auth->>Auth: session[user_id] = id; session[role] = role
            Auth-->>User: 200 OK (Redirect to /vault or /dashboard)
        else Authentication Failed
            Auth->>ML: Evaluate is_suspicious_by_ml(IP)
            alt ML Anomaly Detected (score < 0.0)
                ML->>DB: block_ip(IP) (Escalate cooldown duration)
                ML->>DB: create_alert(HIGH, IP blocked by ML)
                Auth-->>User: 403 Forbidden (Suspicious pattern detected)
            else Standard Failure
                Auth-->>User: 200 OK (Invalid username or password)
            end
        end
    end
""",

    "fig3_vault_crypto_flow.mmd": """graph LR
    subgraph Encryption_Flow [AES-256-GCM Vault Encryption Flow]
        P[Plaintext Secret Credential] --> NonceGen[os.urandom 12 Nonce Generator]
        MasterKey[BRUTESHIELD_VAULT_KEY 32-Byte Master Key] --> GCMEncrypt[AESGCM Encrypt Function]
        NonceGen -->|96-bit IV Nonce| GCMEncrypt
        P --> GCMEncrypt
        GCMEncrypt --> Cipher[Ciphertext Payload]
        GCMEncrypt --> Tag[128-bit Authentication Tag]
        Cipher & Tag --> B64C[Base64 Encoded Ciphertext]
        NonceGen --> B64N[Base64 Encoded Nonce]
        B64C & B64N --> DB[(SQLite vault_items Table)]
    end

    subgraph Decryption_Flow [Authenticated Decryption & Tamper Verification Flow]
        DB --> ReadCipher[Retrieve B64 Ciphertext & Nonce]
        ReadCipher --> B64Dec[Base64 Decode]
        MasterKey --> GCMDecrypt[AESGCM Decrypt Function]
        B64Dec -->|Ciphertext + Auth Tag + Nonce| GCMDecrypt
        GCMDecrypt -->|Auth Tag Validated| PlaintextResult[Decrypted Secret Returned]
        GCMDecrypt -->|InvalidTag Tamper Exception| DecryptFail[Access Denied / Cryptographic Alert]
    end
""",

    "fig4_ml_pipeline.mmd": """graph TD
    subgraph Sliding_Window_Extraction [Sliding-Window Feature Extraction]
        Req[Authentication Telemetry Event] --> DB[(login_attempts Table)]
        DB --> Query[Query attempts WHERE ip = ? AND timestamp >= now - 900s]
        Query --> F1[total_attempts: Count of records in 15m]
        Query --> F2[failed_attempts: Count of failed records]
        Query --> F3[distinct_usernames: Unique username count]
        Query --> F4[avg_gap: Mean inter-attempt gap seconds]
        Query --> F5[min_gap: Minimum inter-attempt burst gap]
        Query --> F6[failure_ratio: failed_attempts / total_attempts]
        F1 & F2 & F3 & F4 & F5 & F6 --> Vector[6-Dimensional Feature Vector]
    end

    subgraph Model_Evaluation [Inference & Tiered Response]
        Vector --> Model[Isolation Forest Model - trained_model.pkl]
        Model --> DecFunc[decision_function - Raw Score]
        DecFunc --> Branch{Decision Threshold}
        Branch -->|raw_score < 0.0| Block[Anomaly Detected -> Tiered Block Ladder]
        Branch -->|0.0 <= raw_score < 0.06| Captcha[Borderline Suspicious -> CAPTCHA Challenge]
        Branch -->|raw_score >= 0.06| Allow[Normal Behavioral Pattern -> Unrestricted]
    end
""",

    "fig5_cooldown_ladder.mmd": """stateDiagram-v2
    [*] --> NormalState: Client IP Activity
    NormalState --> Tier1: 1st Anomaly Triggered
    Tier1 --> Tier2: 2nd Anomaly Triggered (within 24h)
    Tier2 --> Tier3: 3rd Anomaly Triggered
    Tier3 --> Tier4: 4th+ Anomaly Triggered

    Tier1 --> NormalState: 60s Expiration
    Tier2 --> NormalState: 300s (5m) Expiration
    Tier3 --> NormalState: 900s (15m) Expiration
    Tier4 --> NormalState: 3600s (1h) Expiration

    state Tier1 {
        desc1: 60 Seconds Lockout (Initial Cooling)
    }
    state Tier2 {
        desc2: 300 Seconds Lockout (5 Minutes Warning)
    }
    state Tier3 {
        desc3: 900 Seconds Lockout (15 Minutes Containment)
    }
    state Tier4 {
        desc4: 3600 Seconds Lockout (1 Hour Hard Isolation)
    }
""",

    "fig6_honeypot_flow.mmd": """graph LR
    Attacker[Scanning Bot / Threat Actor] -->|Probing /admin-login| Trap[Decoy Honeypot Route]
    Trap --> CSRFExempt[CSRF Validation Bypassed]
    CSRFExempt --> FakeForm[Fake Administrative Login Form Displayed]
    Attacker -->|Submits Guessed Credentials| PostAction[POST Handler]
    PostAction --> Mask[mask_password Function]
    Mask -->|p***d length preserved| MaskedSecret[Masked Telemetry]
    PostAction --> DB[(honeypot_logs Table)]
    MaskedSecret --> DB
    PostAction --> Alert[create_alert CRITICAL: Honeypot Probed]
    PostAction --> BlockIP[block_ip: Instant IP Quarantine]
    PostAction --> FakeResponse[Convincing 200 OK: Invalid administrative credentials]
    FakeResponse --> Attacker
""",

    "fig7_soc_dashboard_flow.mmd": """graph TD
    Analyst[SOC Security Analyst] -->|Auth as dashadmin| WebUI[SOC Live Dashboard]
    WebUI --> API1[GET /dashboard/api/overview]
    WebUI --> API2[GET /dashboard/api/threats]
    WebUI --> API3[GET /dashboard/api/investigate?ip=X]
    WebUI --> API4[GET /dashboard/api/benchmarks]
    WebUI --> API5[GET /dashboard/api/honeypot]

    subgraph Data_Partitioning [Strict Data Partitioning Architecture]
        API1 --> LiveDB[(Live Operational Telemetry)]
        API2 --> LiveDB
        API3 --> LiveDB
        API5 --> LiveDB
        API4 --> SynthPart[Synthetic Benchmark Baseline Data]
        API4 --> LANLPart[LANL Empirical Cyber Dataset Benchmark]
    end

    WebUI --> CanvasCharts[Offline HTML5 Canvas Rendering Engine]
    LiveDB --> CanvasCharts
    SynthPart --> CanvasCharts
    LANLPart --> CanvasCharts
""",

    "fig8_database_er.mmd": """erDiagram
    users ||--o{ vault_items : owns
    alerts ||--o{ alert_acknowledgements : receives

    users {
        int id PK
        string username UK
        string password_hash
        string role
        real created_at
    }

    vault_items {
        int id PK
        int user_id FK
        string service_name
        string username
        string encrypted_password
        string nonce
        string notes
        real created_at
        real updated_at
    }

    login_attempts {
        int id PK
        string ip
        string username
        int success
        real timestamp
    }

    blocked_ips {
        string ip PK
        real blocked_until
    }

    block_counts {
        string ip PK
        int count
    }

    honeypot_logs {
        int id PK
        string ip
        string username_tried
        string password_tried
        int password_length
        real timestamp
    }

    alerts {
        int id PK
        string level
        string message
        real timestamp
    }

    alert_acknowledgements {
        int alert_id PK, FK
        string acknowledged_by
        real acknowledged_at
    }
""",

    "fig9_deployment_architecture.mmd": """graph TB
    InternetClient[Internet / Enterprise WAN Clients] -->|HTTPS Port 443| Nginx[Nginx Reverse Proxy]
    subgraph Reverse_Proxy_Host [Hardened Gateway Boundary]
        Nginx --> Certbot[Let's Encrypt TLS Certificates]
        Nginx --> RateLimit[limit_req: 5r/m login, 30r/m api]
        Nginx --> StaticCache[Static File Cache /static/]
    end

    Nginx -->|HTTP 127.0.0.1:5000 with X-Forwarded-For| WSGIServer[Waitress (Windows) / Gunicorn (Linux)]
    
    subgraph Internal_Application_Boundary [Internal Security Context]
        WSGIServer --> AppFactory[BruteShield Flask Application]
        AppFactory --> SQLite[(SQLite Database - logs/bruteshield.db)]
        AppFactory --> Model[(ML Model - trained_model.pkl)]
    end
""",

    "fig10_use_case_diagram.mmd": """graph LR
    User([Standard User])
    Analyst([SOC Security Analyst])
    Attacker([Automated Attacker / Bot])

    User --> UC1(User Registration with Shannon Entropy & HIBP Audit)
    User --> UC2(User Login with Password Verification)
    User --> UC3(Manage Encrypted Vault Items - AES-GCM)

    Attacker -.-> UC4(Execute High-Frequency Brute Force)
    Attacker -.-> UC5(Probe Decoy Honeypot Trap)

    Analyst --> UC6(Authenticate to SOC Dashboard)
    Analyst --> UC7(Monitor Real-Time Authentication Telemetry)
    Analyst --> UC8(Investigate Suspicious IP ML Feature Vectors)
    Analyst --> UC9(Acknowledge Security Threat Alerts)
    Analyst --> UC10(Unblock Quarantined IP Addresses)
    Analyst --> UC11(Review LANL & Synthetic Benchmarks)
""",

    "fig11_dfd_levels.mmd": """graph TD
    subgraph DFD_Level_0 [DFD Level 0: Context Level Diagram]
        U1[End User] -->|Credentials & Vault Items| BS((BruteShield Defense Platform))
        BS -->|Auth Status & Decrypted Vault Data| U1
        AT[External Attacker] -->|Attack Payloads & Scanner Probes| BS
        BS -->|CAPTCHA Challenges & Cooldown Blocks| AT
        AN[SOC Analyst] -->|Management Queries & Unblock Actions| BS
        BS -->|Live Telemetry, Alerts & Benchmark Metrics| AN
        BS -->|5-char SHA-1 Prefix Query| HIBP[Have I Been Pwned API]
        HIBP -->|Candidate Hash Suffix Range| BS
    end
"""
}

# ---------------------------------------------------------------------------
# 2. WRITE ALL MERMAID (.MMD) FILES
# ---------------------------------------------------------------------------
for fname, content in MERMAID_DIAGRAMS.items():
    fpath = os.path.join(DIAGRAM_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[*] Wrote Mermaid source: {fname}")

# ---------------------------------------------------------------------------
# 3. GENERATE VISUAL PNG DIAGRAMS (HIGH-RES PUBLICATION QUALITY)
# ---------------------------------------------------------------------------
def draw_rounded_rect(draw, coords, radius=10, fill=(30, 41, 59), outline=(59, 130, 246), width=2):
    draw.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)

def create_banner(img, title, subtitle):
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (img.width, 70)], fill=(15, 23, 42))
    draw.rectangle([(0, 68), (img.width, 70)], fill=(59, 130, 246))
    draw.text((30, 15), title, fill=(248, 250, 252))
    draw.text((30, 42), subtitle, fill=(148, 163, 184))

# List of visual diagram specifications to render
PNG_SPECS = [
    ("fig1_system_architecture.png", "Figure 1: BruteShield Modular System Architecture", "Multi-Tier SOC Defense-in-Depth Topology", [
        ("Client / Network Layer", [(50, 100, 350, 180), (390, 100, 690, 180), (730, 100, 1030, 180)], 
         ["Web Client / Browser", "SOC Analyst Gateway", "Attacker / Automated Scanner"]),
        ("Reverse Proxy & Gateway Boundary", [(50, 220, 520, 310), (560, 220, 1030, 310)],
         ["Nginx / Caddy Proxy (TLS 1.2 / 1.3)", "Connection Rate Limiting & ProxyFix"]),
        ("WSGI & Application Core Layer", [(50, 350, 270, 460), (300, 350, 530, 460), (560, 350, 780, 460), (810, 350, 1030, 460)],
         ["Auth & Entropy Module", "AES-256-GCM Vault", "Decoy Honeypot Trap", "SOC Telemetry Engine"]),
        ("Machine Learning & Intelligence Layer", [(50, 500, 520, 590), (560, 500, 1030, 590)],
         ["6-D Sliding Window Feature Extractor", "Isolation Forest Anomaly Scorer"]),
        ("Persistence & Database Storage", [(50, 630, 520, 720), (560, 630, 1030, 720)],
         ["SQLite3 Database (WAL Mode)", "Protected Model Artifacts (.pkl)"])
    ]),

    ("fig2_user_authentication_flow.png", "Figure 2: User Authentication & Threat Verification Flow", "Step-by-Step Defense Ladder & Session Regeneration", [
        ("Authentication Decision Ladder", [(50, 110, 260, 220), (310, 110, 520, 220), (570, 110, 780, 220), (830, 110, 1040, 220)],
         ["1. Check Cooldown", "2. Check CAPTCHA", "3. Verify DB Password", "4. Session Fixation Clear"]),
        ("Defensive Branching", [(50, 270, 350, 400), (390, 270, 700, 400), (740, 270, 1040, 400)],
         ["Normal Success -> Clear Session", "Borderline Anomaly -> CAPTCHA Challenge", "High Anomaly -> ML Cooldown Ladder"]),
        ("Telemetry & Logging", [(50, 450, 520, 570), (560, 450, 1040, 570)],
         ["Record login_attempts", "Escalate Cooldown in block_counts"])
    ]),

    ("fig3_vault_crypto_flow.png", "Figure 3: Zero-Knowledge AES-256-GCM Vault Cryptography", "Authenticated Encryption, Random Nonces, and Tamper Detection", [
        ("Encryption Pipeline", [(50, 110, 350, 230), (390, 110, 690, 230), (730, 110, 1030, 230)],
         ["Plaintext Credential", "os.urandom(12) Nonce", "AES-256-GCM Ciphertext + Tag"]),
        ("Storage in SQLite", [(50, 280, 520, 390), (560, 280, 1030, 390)],
         ["Base64 Encoded Ciphertext", "Base64 Encoded Nonce (Zero Plaintext)"]),
        ("Decryption & Verification", [(50, 440, 520, 560), (560, 440, 1030, 560)],
         ["Master Key Derivation", "InvalidTag Exception on Any Bit Tamper"])
    ]),

    ("fig4_ml_pipeline.png", "Figure 4: Machine Learning Anomaly Detection Pipeline", "Sliding-Window Feature Vector & Isolation Forest Inference", [
        ("6 Behavioral Features", [(50, 110, 200, 210), (220, 110, 370, 210), (390, 110, 540, 210), (560, 110, 710, 210), (730, 110, 880, 210), (900, 110, 1040, 210)],
         ["total_attempts", "failed_attempts", "distinct_users", "avg_gap_sec", "min_gap_sec", "failure_ratio"]),
        ("Evaluation Engine", [(50, 260, 520, 380), (560, 260, 1030, 380)],
         ["Isolation Forest Model (trained_model.pkl)", "Decision Function Continuous Scoring"]),
        ("Decision Thresholds", [(50, 430, 350, 550), (390, 430, 690, 550), (730, 430, 1030, 550)],
         ["Score >= 0.06 -> Normal", "0.0 <= Score < 0.06 -> CAPTCHA", "Score < 0.0 -> Anomaly Block"])
    ]),

    ("fig5_cooldown_ladder.png", "Figure 5: Adaptive Escalation Cooldown Ladder", "Exponential Tiered Lockout Progression for Repeat Attackers", [
        ("Escalation Ladder Tiers", [(50, 110, 270, 240), (305, 110, 525, 240), (560, 110, 780, 240), (815, 110, 1035, 240)],
         ["Tier 1: 60 Seconds", "Tier 2: 300s (5 Mins)", "Tier 3: 900s (15 Mins)", "Tier 4: 3600s (1 Hour)"]),
        ("State Progression", [(50, 300, 520, 420), (560, 300, 1030, 420)],
         ["Stored in block_counts Table", "Cooldown Checked on Every Request"]),
        ("Administrative Control", [(50, 470, 1030, 580)],
         ["Manual Unblock via SOC Dashboard Investigate Drawer"])
    ]),

    ("fig6_honeypot_flow.png", "Figure 6: Decoy Honeypot Trap Architecture (/admin-login)", "Deception Technology, Scanner Capture, and Credential Masking", [
        ("Attacker Interaction", [(50, 110, 350, 230), (390, 110, 690, 230), (730, 110, 1030, 230)],
         ["Attacker Probes /admin-login", "Convincing Fake Portal", "Silent Capture of Credentials"]),
        ("Data Protection & Privacy", [(50, 280, 520, 400), (560, 280, 1030, 400)],
         ["mask_password() Applied (p***d)", "Zero Plaintext Passwords Saved"]),
        ("Threat Escalation", [(50, 450, 520, 560), (560, 450, 1030, 560)],
         ["Instant CRITICAL Alert Generated", "Offending IP Flagged for SOC Review"])
    ]),

    ("fig7_soc_dashboard_flow.png", "Figure 7: SOC Real-Time Telemetry & Data Partitioning", "Operational Feeds, Canvas Visualizations, and Scientific Benchmarks", [
        ("SOC Portals & APIs", [(50, 110, 350, 220), (390, 110, 690, 220), (730, 110, 1030, 220)],
         ["Overview & Feed API", "Threats & Ack API", "Investigate Drawer API"]),
        ("Strict Tripartite Partitioning", [(50, 270, 350, 400), (390, 270, 690, 400), (730, 270, 1030, 400)],
         ["1. Live Operational Logs", "2. Synthetic Benchmarks", "3. LANL Cyber Dataset"]),
        ("Client-Side Rendering", [(50, 450, 1030, 560)],
         ["Pure HTML5 Canvas Offline Chart Engine (No External CDNs)"])
    ]),

    ("fig8_database_er.png", "Figure 8: SQLite Database Entity-Relationship Model", "Relational Schema, Foreign Key Constraints, and Performance Indexes", [
        ("Core Identity Tables", [(50, 110, 520, 240), (560, 110, 1030, 240)],
         ["users (id, username, password_hash, role)", "vault_items (id, user_id FK, enc_pwd, nonce)"]),
        ("Telemetry & Threat Tables", [(50, 280, 350, 420), (390, 280, 690, 420), (730, 280, 1030, 420)],
         ["login_attempts (ip, success, time)", "blocked_ips (ip, blocked_until)", "block_counts (ip, count)"]),
        ("Audit & Deception Tables", [(50, 460, 350, 590), (390, 460, 690, 590), (730, 460, 1030, 590)],
         ["honeypot_logs (ip, user, masked_pwd)", "alerts (id, level, message, time)", "alert_acknowledgements (alert_id FK)"])
    ]),

    ("fig9_deployment_architecture.png", "Figure 9: Production Deployment Topology", "Nginx TLS Gateway, Multi-Threaded WSGI Server, and Hardened Host", [
        ("Internet Gateway", [(50, 110, 1030, 220)],
         ["Nginx Reverse Proxy (TLS 1.2/1.3, Rate Limiting, Static Asset Cache)"]),
        ("WSGI Server Layer", [(50, 270, 520, 390), (560, 270, 1030, 390)],
         ["Waitress Server (Windows: 8 Threads)", "Gunicorn Server (Linux: systemd Foreground)"]),
        ("Application & Storage", [(50, 440, 520, 560), (560, 440, 1030, 560)],
         ["Flask App (Config Guarantees, CSP)", "SQLite (WAL Mode, PRAGMA busy_timeout=5000)"])
    ]),

    ("fig10_use_case_diagram.png", "Figure 10: System Use Case Interaction Model", "Actors, Security Boundaries, and Operational Responsibilities", [
        ("Actors", [(50, 110, 350, 220), (390, 110, 690, 220), (730, 110, 1030, 220)],
         ["Registered User", "SOC Security Analyst", "Malicious Attacker / Scanner"]),
        ("User & Attacker Use Cases", [(50, 270, 520, 400), (560, 270, 1030, 400)],
         ["Signup, Login & Vault Encryption", "Brute Force, Spraying & Honeypot Probes"]),
        ("Analyst Use Cases", [(50, 450, 1030, 570)],
         ["Live Telemetry, ML Investigation, Alert Acknowledgement & Manual Unblock"])
    ]),

    ("fig11_dfd_levels.png", "Figure 11: Data Flow Diagram (DFD Level 0 & Level 1)", "External Entities, Processes, Data Flows, and Data Stores", [
        ("DFD Level 0 (Context)", [(50, 110, 350, 230), (390, 110, 690, 230), (730, 110, 1030, 230)],
         ["Client / Attacker Entities", "BruteShield Defense Platform Core", "Have I Been Pwned External API"]),
        ("DFD Level 1 Processes", [(50, 280, 270, 400), (300, 280, 530, 400), (560, 280, 780, 400), (810, 280, 1030, 400)],
         ["1.0 Auth & Entropy", "2.0 Vault Cryptography", "3.0 ML Threat Detection", "4.0 SOC Telemetry Display"]),
        ("Data Stores", [(50, 450, 520, 570), (560, 450, 1030, 570)],
         ["D1: users & vault_items", "D2: login_attempts, alerts & honeypot_logs"])
    ])
]

# Generate each PNG image
for fname, title, subtitle, sections in PNG_SPECS:
    img = Image.new("RGB", (1100, 760), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    create_banner(img, title, subtitle)

    for sec_title, boxes, labels in sections:
        for idx, (x1, y1, x2, y2) in enumerate(boxes):
            label = labels[idx] if idx < len(labels) else ""
            draw_rounded_rect(draw, (x1, y1, x2, y2), radius=8, fill=(30, 41, 59), outline=(59, 130, 246), width=2)
            # Center text inside box
            draw.text((x1 + 16, y1 + 16), label, fill=(241, 245, 249))

    out_path = os.path.join(DIAGRAM_DIR, fname)
    img.save(out_path, "PNG", dpi=(300, 300))
    print(f"[*] Generated PNG diagram: {fname}")

print("\n[+] All 11 diagrams successfully generated in docs/final-submission/diagrams/!")
