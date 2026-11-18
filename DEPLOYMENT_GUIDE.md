# BruteShield — Production Deployment & Hardening Guide

This document specifies the production deployment architecture, WSGI server configuration, reverse proxy setup, SSL/TLS hardening, and operational maintenance for **BruteShield**.

---

## 1. System Architecture Overview

In a production environment, BruteShield operates behind a dedicated reverse proxy (Nginx or Caddy) that terminates TLS/HTTPS, enforces network-level rate limits, and forwards authenticated requests to an internal WSGI server.

```
                      INTERNET
                         │
                         ▼ HTTPS (Port 443)
              ┌─────────────────────┐
              │     Nginx / Caddy   │  <- TLS Termination, Rate Limiting,
              │    (Reverse Proxy)  │     Security Headers, Static Caching
              └──────────┬──────────┘
                         │ HTTP (127.0.0.1:5000) with X-Forwarded-For
                         ▼
              ┌─────────────────────┐
              │   Waitress / Gunicorn│  <- Multi-Threaded WSGI Server
              │     (WSGI Worker)   │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   BruteShield App   │
              │  ├── Adaptive ML    │
              │  ├── AES-GCM Vault  │
              │  ├── Decoy Honeypot │
              │  └── SOC Dashboard  │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │ SQLite (WAL Mode)   │
              │  logs/bruteshield.db│
              └─────────────────────┘
```

---

## 2. Environment Configuration

Before deploying, create a `.env` file from `.env.example` and set production environment variables.

### Key Production Requirements
1. **`BRUTESHIELD_ENV=production`**: Enforces strict validation at application startup. If default keys are detected, startup halts immediately.
2. **`BRUTESHIELD_SECRET_KEY`**: Cryptographically secure random 64-character hex string.
3. **`BRUTESHIELD_VAULT_KEY`**: 32-byte master key for AES-256-GCM credential encryption.

### Generating Cryptographic Keys
```bash
# Generate Session Secret Key
python -c "import secrets; print(secrets.token_hex(32))"

# Generate Vault Master Key
python -c "import secrets; print(secrets.token_urlsafe(32)[:32])"
```

---

## 3. WSGI Server Configuration

### Windows Deployment (Waitress)
Waitress is the officially supported multi-threaded pure-Python WSGI server for Windows production environments.

Start via the included launcher:
```cmd
run_production.bat
```

Or invoke directly:
```cmd
python wsgi.py
```

Waitress CLI alternative:
```cmd
waitress-serve --listen=127.0.0.1:5000 --threads=8 wsgi:app
```

### Linux Deployment (Gunicorn / Systemd)
On Linux systems, Gunicorn with worker processes provides optimal performance.

#### Gunicorn Direct Execution:
```bash
gunicorn --bind 127.0.0.1:5000 \
         --workers 4 \
         --worker-class gthread \
         --threads 2 \
         --timeout 120 \
         --access-logfile logs/access.log \
         --error-logfile logs/error.log \
         wsgi:app
```

#### Systemd Service Unit (`/etc/systemd/system/bruteshield.service`):
```ini
[Unit]
Description=BruteShield Cybersecurity Defense Engine
After=network.target

[Service]
Type=simple
User=bruteshield
Group=bruteshield
WorkingDirectory=/opt/bruteshield
EnvironmentFile=/opt/bruteshield/.env
ExecStart=/opt/bruteshield/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --threads 2 wsgi:app
Restart=always
RestartSec=5
StandardOutput=append:/opt/bruteshield/logs/systemd.log
StandardError=append:/opt/bruteshield/logs/systemd_err.log

# Sandbox & Hardening Directives
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/bruteshield/logs
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bruteshield
sudo systemctl status bruteshield
```

---

## 4. Reverse Proxy Setup

### Option A: Nginx Configuration (`/etc/nginx/sites-available/bruteshield.conf`)

```nginx
# Upstream WSGI cluster
upstream bruteshield_backend {
    server 127.0.0.1:5000 max_fails=3 fail_timeout=10s;
    keepalive 32;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/m;

# HTTP Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name bruteshield.yourdomain.com;
    return 301 https://$host$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name bruteshield.yourdomain.com;

    # SSL Certificates (Certbot / Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/bruteshield.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bruteshield.yourdomain.com/privkey.pem;

    # TLS Hardening
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Maximum payload size (16MB limit matches BruteShield config)
    client_max_body_size 16M;

    # Static file serving (Offload from Python)
    location /static/ {
        alias /opt/bruteshield/static/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    # User login endpoint with network rate limiting
    location /login {
        limit_req zone=login_limit burst=3 nodelay;
        proxy_pass http://bruteshield_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Pass all other traffic to BruteShield backend
    location / {
        proxy_pass http://bruteshield_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

### Option B: Caddy Configuration (`/etc/caddy/Caddyfile`)

Caddy provides automatic zero-touch HTTPS certificate issuance and renewals:

```caddy
bruteshield.yourdomain.com {
    # Automatic TLS
    tls your-email@example.com

    # Security Headers
    header {
        Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Static assets
    handle_path /static/* {
        root * /opt/bruteshield/static
        file_server
    }

    # Reverse proxy to Waitress/Gunicorn
    reverse_proxy 127.0.0.1:5000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

---

## 5. Database Backup and Maintenance

BruteShield utilizes SQLite with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and `busy_timeout = 5000`. WAL mode permits continuous concurrent reads while writes are occurring without locking readers.

### Automated Hot Backup Script (`backup_db.py` / cron)
SQLite supports atomic hot backups while the application is actively serving requests:

```bash
# Atomic online backup using SQLite CLI
sqlite3 logs/bruteshield.db ".backup 'logs/backups/bruteshield_$(date +%Y%m%d_%H%M%S).db'"
```

Add to cron (`crontab -e`):
```cron
# Backup every night at 2:00 AM
0 2 * * * sqlite3 /opt/bruteshield/logs/bruteshield.db ".backup '/opt/bruteshield/logs/backups/bruteshield_$(date +\%Y\%m\%d_\%H\%M\%S).db'"
```

### WAL Checkpoint Maintenance
SQLite checkpoints automatically at 1000 pages. For high-volume deployments, manually checkpoint periodically:
```bash
sqlite3 logs/bruteshield.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

---

## 6. Production Security Checklist

| Check | Requirement | Verification Method | Status |
|---|---|---|:---:|
| 1 | Non-default `BRUTESHIELD_SECRET_KEY` | Application crashes if demo secret is used in production | Verified |
| 2 | Non-default `BRUTESHIELD_VAULT_KEY` | Application crashes if demo key is used in production | Verified |
| 3 | Cookies set to Secure | `SESSION_COOKIE_SECURE = True` in production mode | Verified |
| 4 | HTTPS / TLS Active | Reverse proxy forces 301 redirect to HTTPS | Configured |
| 5 | Trusted Proxy Whitelist | `TRUSTED_PROXIES` restricted to local reverse proxy IP | Verified |
| 6 | 0 CVEs in Dependencies | `pip-audit` reports zero vulnerabilities | 100% Clean |
| 7 | Static Code SAST Clean | `bandit -r bruteshield/ app.py` reports 0 issues | 100% Clean |
| 8 | All Regression Tests Pass | `pytest tests/ -v` passes 50/50 tests | 100% Green |
| 9 | Model Artifact Integrity | Protected hashes match baseline exactly | SHA-256 Verified |
| 10 | Decoy Honeypot Active | `/admin-login` catches scanners without leaking data | Verified |
