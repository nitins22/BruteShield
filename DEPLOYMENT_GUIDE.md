# BruteShield — Production Deployment Guide

This document describes how to deploy BruteShield in development, local production, and server environments. It covers WSGI server configuration, reverse proxy setup, TLS hardening, database maintenance, and operational checklists.

> [!IMPORTANT]
> Writing deployment instructions does not constitute a live public deployment. This guide documents **how** to deploy BruteShield — the actual deployment must be performed and verified by the operator on their own infrastructure.

---

## 1. Deployment Architecture

```
  Browser (HTTPS)
      │
      ▼
  ┌──────────────────────┐
  │  Reverse Proxy       │  Nginx or Caddy
  │  - TLS termination   │  - Listens on :443
  │  - Rate limiting     │  - Forwards to 127.0.0.1:5000
  │  - Static assets     │
  └──────────┬───────────┘
             │  HTTP (127.0.0.1:5000)
             │  X-Forwarded-For, X-Real-IP
             ▼
  ┌──────────────────────┐
  │  WSGI Server         │  Waitress (Windows) or Gunicorn (Linux)
  │  - Multi-threaded    │  - Imports wsgi:app
  │  - No TLS            │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  Flask Application   │  bruteshield.create_app()
  │  ├ Auth & CSRF       │
  │  ├ ML Anomaly Engine │
  │  ├ AES-GCM Vault     │
  │  ├ Honeypot Decoy    │
  │  └ SOC Dashboard     │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  SQLite (WAL mode)   │  logs/bruteshield.db
  └──────────────────────┘
```

> [!NOTE]
> Waitress does **not** terminate TLS. In production, TLS must be provided by the reverse proxy (Nginx/Caddy). For local demonstrations, plain HTTP on `127.0.0.1` is acceptable.

---

## 2. Environment Configuration

### 2.1 Configuration File

Copy `.env.example` to `.env` and replace all placeholders:

```bash
cp .env.example .env
```

### 2.2 Generating Cryptographic Secrets

```bash
# Session secret key (64 hex characters = 32 bytes)
python -c "import secrets; print(secrets.token_hex(32))"

# AES-256-GCM vault master key (32 URL-safe characters)
python -c "import secrets; print(secrets.token_urlsafe(32)[:32])"
```

### 2.3 Production Secret Enforcement

When `BRUTESHIELD_ENV=production`, the application **refuses to start** if:
- `BRUTESHIELD_SECRET_KEY` is missing or equals the demo default.
- `BRUTESHIELD_VAULT_KEY` is missing or equals the demo default.

This guard is enforced at module import time in `bruteshield/config.py`.

> [!CAUTION]
> Changing `BRUTESHIELD_VAULT_KEY` after vault entries have been stored makes those entries permanently unreadable. Back up the key before rotation.

---

## 3. Windows Deployment (Waitress)

### 3.1 Prerequisites

- Python 3.10+ installed and on PATH.
- Virtual environment created: `python -m venv venv`
- Dependencies installed: `pip install -r requirements.txt`

### 3.2 Starting the Server

**Using the launcher script:**

```cmd
run_production.bat
```

The launcher validates Python, the virtual environment, Waitress installation, database directory, and production secrets before starting.

**Using wsgi.py directly:**

```cmd
venv\Scripts\activate
python wsgi.py
```

**Using the Waitress CLI:**

```cmd
venv\Scripts\activate
waitress-serve --listen=127.0.0.1:5000 --threads=4 wsgi:app
```

### 3.3 Configuration

| Variable | Default | Description |
|---|---|---|
| `BRUTESHIELD_HOST` | `127.0.0.1` | Bind address |
| `BRUTESHIELD_PORT` | `5000` | Bind port |
| `WAITRESS_THREADS` | `4` | Worker thread count |

### 3.4 Firewall

If BruteShield should be accessible from other machines on the LAN:
1. Change `BRUTESHIELD_HOST` to `0.0.0.0`.
2. Create a Windows Firewall inbound rule for TCP port 5000.
3. Place a reverse proxy (Nginx for Windows, Caddy) in front for TLS.

### 3.5 Process Lifecycle

- **Start**: `run_production.bat` or `python wsgi.py`.
- **Stop**: Press `Ctrl+C` in the console window.
- **Logs**: Waitress writes to stdout/stderr. Redirect to a file if needed: `python wsgi.py > logs\server.log 2>&1`.

---

## 4. Linux Deployment (Gunicorn + systemd)

### 4.1 Prerequisites

```bash
sudo useradd --system --shell /usr/sbin/nologin --home-dir /opt/bruteshield bruteshield
sudo mkdir -p /opt/bruteshield
sudo cp -r . /opt/bruteshield/
sudo chown -R bruteshield:bruteshield /opt/bruteshield

cd /opt/bruteshield
sudo -u bruteshield python3 -m venv venv
sudo -u bruteshield venv/bin/pip install -r requirements.txt
sudo -u bruteshield venv/bin/pip install gunicorn
```

### 4.2 Gunicorn Configuration

| Variable | Default | Description |
|---|---|---|
| `BRUTESHIELD_HOST` | `127.0.0.1` | Bind address |
| `BRUTESHIELD_PORT` | `5000` | Bind port |
| `GUNICORN_WORKERS` | `2` | Worker process count |

**Worker count guidance**: SQLite supports concurrent readers under WAL mode but only one writer at a time. Setting `GUNICORN_WORKERS` higher than 2–4 provides diminishing returns and increases write contention. For this application, 2 workers is sufficient.

### 4.3 systemd Service Unit

Create `/etc/systemd/system/bruteshield.service`:

```ini
[Unit]
Description=BruteShield Cybersecurity Defense Engine
After=network.target
Documentation=file:///opt/bruteshield/DEPLOYMENT_GUIDE.md

[Service]
Type=simple
User=bruteshield
Group=bruteshield
WorkingDirectory=/opt/bruteshield
EnvironmentFile=/opt/bruteshield/.env
ExecStart=/opt/bruteshield/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile /opt/bruteshield/logs/access.log \
    --error-logfile /opt/bruteshield/logs/error.log \
    wsgi:app
Restart=on-failure
RestartSec=5

# Hardening directives
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/bruteshield/logs
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

> [!WARNING]
> `ProtectSystem=strict` makes the entire filesystem read-only except paths listed in `ReadWritePaths`. The database directory (`logs/`) must be listed or the application cannot write to its database.

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable bruteshield
sudo systemctl start bruteshield
sudo systemctl status bruteshield
```

Gunicorn runs in the **foreground** under systemd supervision. Do not use Gunicorn's `--daemon` flag with systemd.

### 4.4 Log Management

```bash
# View real-time logs
sudo journalctl -u bruteshield -f

# Application access/error logs
tail -f /opt/bruteshield/logs/access.log
tail -f /opt/bruteshield/logs/error.log
```

---

## 5. Nginx Reverse Proxy

### 5.1 Full Configuration

Create `/etc/nginx/sites-available/bruteshield`:

```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login_zone:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api_zone:10m   rate=30r/m;

# Upstream
upstream bruteshield {
    server 127.0.0.1:5000;
    keepalive 16;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name bruteshield.example.com;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name bruteshield.example.com;

    # --- TLS Configuration ---
    ssl_certificate     /etc/letsencrypt/live/bruteshield.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bruteshield.example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # --- Security Headers ---
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Content-Type-Options    "nosniff" always;
    add_header X-Frame-Options           "SAMEORIGIN" always;
    add_header Referrer-Policy           "strict-origin-when-cross-origin" always;

    # --- Request Size Limit (matches Flask MAX_CONTENT_LENGTH) ---
    client_max_body_size 16M;

    # --- Static Assets ---
    location /static/ {
        alias /opt/bruteshield/static/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }

    # --- Login Endpoints (rate limited) ---
    location ~ ^/(login|signup|dashboard-login|admin-login) {
        limit_req zone=login_zone burst=3 nodelay;
        proxy_pass http://bruteshield;
        include /etc/nginx/proxy_params_bruteshield;
    }

    # --- API Endpoints (rate limited) ---
    location /api/ {
        limit_req zone=api_zone burst=10 nodelay;
        proxy_pass http://bruteshield;
        include /etc/nginx/proxy_params_bruteshield;
    }

    # --- All Other Routes ---
    location / {
        proxy_pass http://bruteshield;
        include /etc/nginx/proxy_params_bruteshield;
    }

    # --- Logging ---
    access_log /var/log/nginx/bruteshield_access.log;
    error_log  /var/log/nginx/bruteshield_error.log warn;
}
```

Create `/etc/nginx/proxy_params_bruteshield`:

```nginx
proxy_http_version 1.1;
proxy_set_header   Connection "";
proxy_set_header   Host $host;
proxy_set_header   X-Real-IP $remote_addr;
proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header   X-Forwarded-Proto $scheme;
proxy_read_timeout 120s;
proxy_send_timeout 120s;
```

### 5.2 Trusted Proxy Configuration

BruteShield's `get_client_ip()` reads `X-Forwarded-For` **only** when the direct peer IP matches the `TRUSTED_PROXIES` list. With a single Nginx instance on the same machine:

```
TRUSTED_PROXIES=127.0.0.1,::1
```

An untrusted client sending a forged `X-Forwarded-For` header directly to BruteShield (without passing through the trusted proxy) will have its `X-Forwarded-For` header ignored; `remote_addr` is used instead.

> [!CAUTION]
> Do not add public IP addresses to `TRUSTED_PROXIES`. Do not apply Werkzeug `ProxyFix` with more `x_for` hops than the actual number of trusted reverse proxies in the chain. With one Nginx proxy, one hop is correct.

### 5.3 Enable and Test

```bash
sudo ln -s /etc/nginx/sites-available/bruteshield /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Caddy Reverse Proxy (Alternative)

Caddy provides automatic HTTPS with Let's Encrypt certificate issuance.

### 6.1 Prerequisites

- A registered domain name pointing (DNS A record) to the server's public IP.
- Ports 80 and 443 open and reachable from the internet (required for ACME HTTP-01 challenge).
- Caddy installed: https://caddyserver.com/docs/install

> [!IMPORTANT]
> Automatic HTTPS **requires** DNS to resolve to the server and ports 80/443 to be publicly reachable. Without these prerequisites, Caddy cannot obtain a certificate. For local-only or LAN deployments, use self-signed certificates or plain HTTP.

### 6.2 Caddyfile

Create `/etc/caddy/Caddyfile`:

```caddy
bruteshield.example.com {
    # Automatic TLS (Let's Encrypt)
    tls admin@example.com

    # Security headers
    header {
        Strict-Transport-Security "max-age=63072000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Static files
    handle_path /static/* {
        root * /opt/bruteshield/static
        file_server
    }

    # Reverse proxy to WSGI server
    reverse_proxy 127.0.0.1:5000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

---

## 7. SQLite Backup and Recovery

### 7.1 WAL Mode

BruteShield configures SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and `PRAGMA busy_timeout=5000`. WAL mode allows concurrent readers while a write is in progress.

### 7.2 Online Backup (Consistency-Safe)

**Do not** simply copy `bruteshield.db` while the application is running — this may capture an inconsistent state if WAL transactions are active.

Use SQLite's built-in `.backup` command or the Python `sqlite3` backup API:

```bash
# Using sqlite3 CLI (recommended)
sqlite3 logs/bruteshield.db ".backup 'logs/backups/bruteshield_backup.db'"
```

```python
# Using Python sqlite3 backup API
import sqlite3, shutil, os
from datetime import datetime

src = sqlite3.connect("logs/bruteshield.db")
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs("logs/backups", exist_ok=True)
dst = sqlite3.connect(f"logs/backups/bruteshield_{stamp}.db")
src.backup(dst)
dst.close()
src.close()
```

Both methods produce a consistent, self-contained backup even while the application is serving requests.

### 7.3 Integrity Verification

After creating a backup, verify its integrity:

```bash
sqlite3 logs/backups/bruteshield_backup.db "PRAGMA integrity_check;"
# Expected output: ok
```

### 7.4 Restore Procedure

1. Stop the BruteShield server.
2. Move the current database aside: `mv logs/bruteshield.db logs/bruteshield.db.old`
3. Copy the backup: `cp logs/backups/bruteshield_backup.db logs/bruteshield.db`
4. Verify: `sqlite3 logs/bruteshield.db "PRAGMA integrity_check;"`
5. Remove WAL/SHM files if present: `rm -f logs/bruteshield.db-wal logs/bruteshield.db-shm`
6. Start the server.

### 7.5 Backup Rotation (cron)

```cron
# Daily backup at 02:00, retain 14 days
0 2 * * * sqlite3 /opt/bruteshield/logs/bruteshield.db ".backup '/opt/bruteshield/logs/backups/bruteshield_$(date +\%Y\%m\%d).db'"
0 3 * * * find /opt/bruteshield/logs/backups -name "bruteshield_*.db" -mtime +14 -delete
```

### 7.6 WAL Checkpoint

SQLite checkpoints automatically, but for maintenance:

```bash
sqlite3 logs/bruteshield.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

---

## 8. Production Readiness Checklist

### 8.1 Local Production-Style Execution

| # | Check | Verification |
|---|---|---|
| 1 | Python 3.10+ available | `python --version` |
| 2 | Virtual environment exists | `venv\Scripts\activate` or `source venv/bin/activate` |
| 3 | Dependencies installed | `pip install -r requirements.txt` |
| 4 | Waitress installed (Windows) | `python -c "import waitress"` |
| 5 | ML model present | `trained_model.pkl` exists |
| 6 | Database directory writable | `logs/` exists or can be created |
| 7 | Server starts without errors | `python wsgi.py` |
| 8 | All 50 tests pass | `pytest tests/ -v` |
| 9 | Zero known CVEs | `pip-audit` |

### 8.2 Private LAN Deployment

All items from 8.1, plus:

| # | Check |
|---|---|
| 10 | `BRUTESHIELD_HOST` set to `0.0.0.0` or specific LAN interface |
| 11 | Firewall allows inbound TCP on configured port |
| 12 | Non-default `BRUTESHIELD_SECRET_KEY` and `BRUTESHIELD_VAULT_KEY` |
| 13 | Database backup schedule configured |

### 8.3 Public Internet Deployment

All items from 8.1 and 8.2, plus:

| # | Check |
|---|---|
| 14 | `BRUTESHIELD_ENV=production` |
| 15 | Reverse proxy (Nginx/Caddy) configured and tested |
| 16 | TLS certificate valid and auto-renewed |
| 17 | HTTP redirects to HTTPS |
| 18 | `SESSION_COOKIE_SECURE=True` (automatic in production mode) |
| 19 | Rate limiting enabled on login endpoints |
| 20 | Access logs and error logs configured |
| 21 | Dedicated non-root service user |
| 22 | systemd service with hardening directives |
| 23 | Default demo accounts disabled or passwords changed |
| 24 | Database backed up and backup verified |
