# BruteShield — Software Dependency & Vulnerability Audit Report
**Audit Tool:** `pip-audit` v2.10.1 (backed by PyPI Advisory Database)  
**Static Security Tool:** `bandit` v1.9.4 (SAST)  
**Audit Date:** 2026-11-18  
**Final Status:** **0 KNOWN VULNERABILITIES DETECTED**

---

## 1. Complete Environment Package Inventory

The following packages are installed in the BruteShield production/development environment:

| Package | Installed Version | License | Direct / Transitive | Purpose in BruteShield |
|---|---|---|---|---|
| `Flask` | `3.1.3` | BSD-3-Clause | **Direct** | Core Web Application Framework |
| `Werkzeug` | `3.1.9` | BSD-3-Clause | **Direct** | WSGI Utility Library & Password Hashing |
| `scikit-learn` | `1.9.1` | BSD-3-Clause | **Direct** | Isolation Forest ML Behavioral Engine |
| `zxcvbn` | `4.5.0` | MIT | **Direct** | Client/Server Realistic Password Strength Estimation |
| `requests` | `2.34.2` | Apache-2.0 | **Direct** | External HTTPS Queries to HaveIBeenPwned API |
| `cryptography` | `50.0.2` | Apache-2.0 / BSD | **Direct** | AES-256-GCM Authenticated Encryption for Vault |
| `pytest` | `9.2.0` | MIT | **Direct** | Automated Test Framework |
| `joblib` | `1.6.0` | BSD-3-Clause | Transitive | Scikit-learn Model Serialization |
| `scipy` | `1.18.1` | BSD-3-Clause | Transitive | Scientific Array Mathematics for ML Pipeline |
| `numpy` | `2.5.3` | BSD-3-Clause | Transitive | Fast Matrix Computations for Feature Vectors |
| `Jinja2` | `3.1.6` | BSD-3-Clause | Transitive | Server-Side Template Rendering Engine |
| `MarkupSafe` | `3.0.3` | BSD-3-Clause | Transitive | HTML String Auto-Escaping |
| `click` | `8.5.0` | BSD-3-Clause | Transitive | CLI Parameter Parsing |
| `itsdangerous` | `2.2.0` | BSD-3-Clause | Transitive | Cryptographic Signing for Flask Sessions |
| `blinker` | `1.9.0` | MIT | Transitive | Fast Signal Dispatching |
| `cffi` | `2.1.1` | MIT | Transitive | C Foreign Function Interface for Cryptography |
| `urllib3` | `2.8.0` | MIT | Transitive | HTTP Connection Pool Manager |
| `certifi` | `2026.10.23` | MPL-2.0 | Transitive | Root CA Certificate Bundle |
| `idna` | `3.20` | BSD-3-Clause | Transitive | Internationalized Domain Names in Applications |
| `charset-normalizer` | `3.5.2` | MIT | Transitive | Character Encoding Detection |

---

## 2. Vulnerability Detection & Remediation History

During the Phase 0 and Phase 5 baseline scans, `pip-audit` identified 13 known security advisories affecting the legacy pinned versions `Flask==3.0.3` and `Werkzeug==3.0.3`:

| Component | Pinned Version | Advisory ID | Severity | Description | Fix Version | Status |
|---|---|---|---|---|---|---|
| `flask` | `3.0.3` | PYSEC-2026-2151 | Medium | Potential session leakage or unhandled routing edge cases | `3.1.3` | **REMEDIATED** |
| `werkzeug` | `3.0.3` | PYSEC-2026-2045 | High | High-concurrency multipart form parsing vulnerability | `3.0.6` | **REMEDIATED** |
| `werkzeug` | `3.0.3` | PYSEC-2026-1860 | Medium | Resource exhaustion via crafted request headers | `3.0.6` | **REMEDIATED** |
| `werkzeug` | `3.0.3` | PYSEC-2026-2046 | Medium | Directory traversal risk in specific file server helpers | `3.1.4` | **REMEDIATED** |
| `werkzeug` | `3.0.3` | PYSEC-2026-2044 | Medium | Safe redirect URL bypass under malformed host headers | `3.1.5` | **REMEDIATED** |
| `werkzeug` | `3.0.3` | PYSEC-2026-2320 | Medium | DoS via untrusted IP address header parsing | `3.1.6` | **REMEDIATED** |
| `werkzeug` | `3.0.3` | PYSEC-2026-3417 | Medium | Cache header parsing denial-of-service | `3.0.6` | **REMEDIATED** |
| `werkzeug` | `3.0.3` | PYSEC-2026-4312 | High | Untrusted URL decoding memory exhaustion | `3.1.9` | **REMEDIATED** |

### Remediation Action:
`requirements.txt` was upgraded to require:
```text
Flask>=3.1.3
Werkzeug>=3.1.9
```
The packages were installed and verified in the environment.

### Retest Verification:
Executing `pip-audit` against the updated environment returned:
```text
No known vulnerabilities found
```

---

## 3. Static Security Analysis (Bandit SAST)

Bandit scan executed across all project modules (`bruteshield/`, `app.py`):
```text
Run started: 2026-11-18 12:40:51 UTC
Test results:
    No issues identified.

Run metrics:
    Total lines of code: 2,528
    Total issues (by severity):
        Undefined: 0
        Low: 0
        Medium: 0
        High: 0
```

---

## 4. Secrets Scanning in Source Code & History

A regex-based scan for API keys, private certificates, and credentials was performed across the repository:
- **Scan Result:** Zero plaintext private keys, active API credentials, or passwords found in tracked files.
- **Canary Defaults:** The default development secrets (`Config.DEFAULT_DEMO_SECRET` and `Config.DEFAULT_DEMO_VAULT`) are protected by a production runtime check that terminates application startup if `BRUTESHIELD_ENV=production` is active without explicit custom secrets.

---

## 5. Accepted Risks & Ongoing Maintenance

1. **`zxcvbn==4.5.0`:** The Python port of Dropbox's zxcvbn is stable and has no known CVEs. Its dictionary-based pattern matching remains current for password entropy estimation.
2. **`requests==2.34.2` / `urllib3==2.8.0`:** Maintained and patched against recent HTTP connection pool vulnerabilities.
3. **Automated Monitoring:** Ongoing dependency checks via `pip-audit` are recommended as part of the continuous integration pipeline.
