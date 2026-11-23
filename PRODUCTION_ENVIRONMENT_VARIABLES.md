# BruteShield — Production Environment Variables Reference

This document provides the complete reference for all environment variables supported by the BruteShield production architecture.

---

## 1. Core Production Variables

| Variable | Required in Prod? | Default | Type | Description |
|---|---|---|---|---|
| `BRUTESHIELD_ENV` | **YES** | `development` | String | Set to `production` in live environments. Enforces secure cookies, HSTS headers, and non-default secret validation. |
| `BRUTESHIELD_SECRET_KEY` | **YES** | None (Demo default rejected) | Hex String (64 chars) | Cryptographic secret for signing session cookies. Must be generated using CSPRNG. |
| `BRUTESHIELD_VAULT_KEY` | **YES** | None (Demo default rejected) | Byte/URLSafe (32 chars) | Master encryption key for AES-256-GCM vault item storage. |
| `DATABASE_URL` | **YES** | Empty (Falls back to SQLite) | URI | Connection string for Managed PostgreSQL (e.g., `postgresql://user:pass@host:5432/bruteshield`). |
| `BEHIND_PROXY` | **YES** (Cloud) | `true` in prod / Render | Boolean | Enables `ProxyFix` middleware so `request.remote_addr` accurately reflects client IP behind Render/Cloudflare. |

---

## 2. Database & Pool Tuning

| Variable | Required in Prod? | Default | Type | Description |
|---|---|---|---|---|
| `DATABASE_POOL_MIN` | No | `1` | Integer | Minimum connection pool size for PostgreSQL (`psycopg2.pool.ThreadedConnectionPool`). |
| `DATABASE_POOL_MAX` | No | `10` | Integer | Maximum concurrent database connections allowed in the pool. |
| `BRUTESHIELD_DB_PATH` | No | `logs/bruteshield.db` | Path | Fallback SQLite database path used if `DATABASE_URL` is omitted. |

---

## 3. Administrator Provisioning

| Variable | Required in Prod? | Default | Type | Description |
|---|---|---|---|---|
| `INITIAL_ADMIN_USER` | No | `dashadmin` | String | Username for the initial SOC Administrator account. |
| `INITIAL_ADMIN_PASSWORD` | **Recommended** | Empty | String | Password for the initial SOC Administrator. If provided, the account is created on first boot. Default demo credentials are **never seeded in production**. |

---

## 4. Threat Detection & ML Engine Tuning

| Variable | Required in Prod? | Default | Type | Description |
|---|---|---|---|---|
| `BRUTESHIELD_MODEL_PATH` | No | `trained_model.pkl` | Path | Absolute or relative path to the pre-trained Isolation Forest model file. |
| `MAX_FAILED_ATTEMPTS` | No | `5` | Integer | Number of failed attempts within `TIME_WINDOW_SECONDS` before fallback blocking engages. |
| `TIME_WINDOW_SECONDS` | No | `60` | Integer | Time window (seconds) for baseline rule-based failure threshold. |
| `SLIDING_WINDOW_SECONDS` | No | `900` (15 min) | Integer | Time window for 6-feature behavioral extraction: `[total, failed, distinct, avg_gap, min_gap, failure_ratio]`. |
| `CAPTCHA_SCORE_LIMIT` | No | `0.06` | Float | ML decision score threshold below which a suspicious IP is challenged with CAPTCHA before a hard block. |
| `TRUSTED_PROXIES` | No | `127.0.0.1,::1` | CSV String | Trusted upstream reverse proxy IP addresses. |

---

## 5. Rate Limiting Configuration

| Variable | Required in Prod? | Default | Type | Description |
|---|---|---|---|---|
| `LOGIN_RATE_LIMIT_MAX` | No | `20` | Integer | Maximum login requests allowed per IP address within the window. |
| `LOGIN_RATE_LIMIT_WINDOW` | No | `300` (5 min) | Integer | Window in seconds for login IP rate limiting. |
| `SIGNUP_RATE_LIMIT_MAX` | No | `10` | Integer | Maximum account registrations per IP address per hour. |
| `SIGNUP_RATE_LIMIT_WINDOW`| No | `3600` (1 hour) | Integer | Window in seconds for registration rate limiting. |

---

## 6. Email / SMTP Configuration (Optional)

| Variable | Required in Prod? | Default | Type | Description |
|---|---|---|---|---|
| `MAIL_SERVER` | No | Empty | String | Outbound SMTP server hostname (e.g., `smtp.sendgrid.net`). |
| `MAIL_PORT` | No | `587` | Integer | SMTP port (e.g., 587 for TLS, 465 for SSL). |
| `MAIL_USE_TLS` | No | `true` | Boolean | Whether to enable STARTTLS for SMTP connections. |
| `MAIL_USERNAME` | No | Empty | String | SMTP authentication username. |
| `MAIL_PASSWORD` | No | Empty | String | SMTP authentication password / API key. |
| `MAIL_DEFAULT_SENDER` | No | `noreply@bruteshield.local` | Email | Sender email address for password reset emails. |

*Note: If `MAIL_SERVER` is omitted, BruteShield operates in direct link mode, displaying the password reset link directly on screen for testing.*

---

## 7. Secret Generation Helper Commands

Run the following commands in Python to generate cryptographically secure keys:

```bash
# Generate BRUTESHIELD_SECRET_KEY (64-character hex string)
python -c "import secrets; print(secrets.token_hex(32))"

# Generate BRUTESHIELD_VAULT_KEY (32-character URL-safe string)
python -c "import secrets; print(secrets.token_urlsafe(32)[:32])"

# Generate INITIAL_ADMIN_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(24))"
```
