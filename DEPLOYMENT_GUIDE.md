# BruteShield — Public Cloud Deployment Guide

This guide details the complete production deployment procedure for **BruteShield** as a publicly accessible, multi-user, cloud-hosted security platform. The reference architecture utilizes **Render Web Service** paired with a managed **Render PostgreSQL** relational database, served via **Gunicorn** WSGI with platform TLS termination and automated health monitoring.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |       Public Internet Clients         |
                      +-------------------+-------------------+
                                          |
                                          | HTTPS (Port 443 / TLS 1.3)
                                          v
                      +---------------------------------------+
                      |    Render Managed Cloudflare Edge     |
                      |   (SSL Termination / DDoS Shield)     |
                      +-------------------+-------------------+
                                          |
                                          | HTTP (Reverse Proxy Header: X-Forwarded-For)
                                          v
+-------------------------------------------------------------------------------+
| Render Web Service (Ubuntu / Python 3.12)                                     |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | Gunicorn WSGI Server (2 Workers x 4 Threads, Timeout 120s)              |  |
|  |  +-------------------------------------------------------------------+  |  |
|  |  | Flask Application Factory (bruteshield.create_app)                 |  |  |
|  |  |  - ProxyFix Middleware (IP Restoration)                           |  |  |
|  |  |  - Health Probe: GET /health (Database & ML Check)                |  |  |
|  |  |  - Cryptographic Password Vault (AES-256-GCM)                     |  |  |
|  |  |  - ML Inference Engine (Isolation Forest 6-Feature Behavioral)    |  |  |
|  |  +-------------------------------------------------------------------+  |  |
|  +-------------------------------------+-----------------------------------+  |
+----------------------------------------|--------------------------------------+
                                         |
                                         | Secure Internal Network Connection
                                         v
+-------------------------------------------------------------------------------+
| Render Managed PostgreSQL Database                                            |
|  - Relational Multi-User Storage (users, login_attempts, vault_items)         |
|  - Connection Pooling (ThreadedConnectionPool: 2-10 connections)              |
|  - ACID Concurrency, Foreign Keys, Cascading Deletes                          |
+-------------------------------------------------------------------------------+
```

---

## Method 1: Automated Blueprint Deployment (`render.yaml`)

The repository includes a production-grade `render.yaml` infrastructure-as-code blueprint that automatically provisions both the PostgreSQL instance and Web Service in a single step.

### Step 1: Push Repository to GitHub or GitLab
Ensure your latest changes are pushed to your remote repository:
```bash
git push origin master
```

### Step 2: Connect Repository to Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub/GitLab repository (`bruteshield_prototype`).
4. Render will parse `render.yaml` and display the resources to be created:
   - **`bruteshield-db`**: Managed PostgreSQL Database.
   - **`bruteshield-web`**: Python 3 Web Service.
5. Click **Apply**. Render will automatically provision the database, inject `DATABASE_URL`, generate secure random secrets for `BRUTESHIELD_SECRET_KEY` and `BRUTESHIELD_VAULT_KEY`, and deploy the application.

---

## Method 2: Manual Step-by-Step Deployment

If you prefer to configure services manually via the Render UI:

### Step 1: Create Managed PostgreSQL Database
1. In Render Dashboard, click **New +** > **PostgreSQL**.
2. Set configuration:
   - **Name**: `bruteshield-postgres`
   - **Database**: `bruteshield`
   - **User**: `bruteshield_admin`
   - **Region**: Choose closest to your users (e.g., `Oregon (US West)` or `Frankfurt (EU Central)`).
   - **Plan**: `Free` or `Starter`.
3. Click **Create Database**.
4. Once created, copy the **Internal Database URL** (e.g., `postgresql://bruteshield_admin:...@dpg-...-a/bruteshield`).

### Step 2: Create Web Service
1. In Render Dashboard, click **New +** > **Web Service**.
2. Select your repository.
3. Configure settings:
   - **Name**: `bruteshield-app`
   - **Region**: Same region as your database.
   - **Branch**: `master`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - **Health Check Path**: `/health`

### Step 3: Configure Production Environment Variables
Under the **Environment** tab of the Web Service, add the following variables:

| Key | Value / Source | Description |
|---|---|---|
| `BRUTESHIELD_ENV` | `production` | Enforces strict secret validation & HTTPS cookies |
| `DATABASE_URL` | *Paste Internal Database URL* | Points to managed PostgreSQL |
| `BRUTESHIELD_SECRET_KEY` | *Generate 64-char hex* | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `BRUTESHIELD_VAULT_KEY` | *Generate 32-char key* | `python -c "import secrets; print(secrets.token_urlsafe(32)[:32])"` |
| `BEHIND_PROXY` | `true` | Enables `ProxyFix` for client IP resolution |
| `INITIAL_ADMIN_USER` | `dashadmin` | Username for SOC Dashboard operator |
| `INITIAL_ADMIN_PASSWORD` | *Strong Password* | Initial admin password (seeded on first boot) |
| `DATABASE_POOL_MIN` | `2` | Minimum connection pool size |
| `DATABASE_POOL_MAX` | `10` | Maximum connection pool size |

Click **Save Changes**. Render will initiate the initial build and deployment.

---

## Database Migration & Schema Verification

When the Web Service launches for the first time, `bruteshield/__init__.py` invokes `init_db(target_db)` automatically, creating all necessary tables and indexes in PostgreSQL.

To migrate existing records from a local SQLite database into your Render PostgreSQL database:

```bash
# Set your target Render External Database URL
export DATABASE_URL="postgresql://bruteshield_admin:PASSWORD@dpg-host.oregon-postgres.render.com/bruteshield"

# Run non-destructive migration script
python scripts/migrate_sqlite_to_postgres.py --source logs/bruteshield.db --target "$DATABASE_URL"
```

The migration script:
1. Validates connection to both SQLite and PostgreSQL.
2. Ensures all tables and indexes exist on the target.
3. Copies `users`, `login_attempts`, `blocked_ips`, `block_counts`, `honeypot_logs`, `alerts`, `alert_acknowledgements`, and `vault_items`.
4. Synchronizes PostgreSQL auto-increment sequences (`users_id_seq`, etc.).
5. Preserves the source SQLite file completely untouched.

---

## Health Check and Smoke Verification

Once deployment completes, verify operational readiness using the `/health` endpoint:

```bash
curl -i https://your-bruteshield-app.onrender.com/health
```

Expected response (`200 OK`):
```json
{
  "status": "healthy",
  "database": "connected",
  "database_engine": "postgresql",
  "model_loaded": true,
  "timestamp": 1740000000.123
}
```

### Production Smoke Test Checklist:
1. **Public Registration**: Visit `https://your-bruteshield-app.onrender.com/signup` and register a new user account with email.
2. **User Authentication**: Log in at `/login`.
3. **Password Vault CRUD**: Add a secret credential in `/vault/`, verify that it displays masked, and click to decrypt using AES-256-GCM.
4. **Multi-User Isolation**: Open a private browser window, register a second user, and confirm that the second user cannot see or decrypt the first user's vault items.
5. **SOC Dashboard Access**: Log into `/dashboard-login` with `dashadmin` credentials and verify real-time metrics and active ML model status.
6. **Honeypot Decoy**: Navigate to `/admin-login` and test a decoy attempt; observe that the attempt is captured in SOC logs and the IP is challenged.

---

## Custom Domain and TLS Termination

1. In the Render Dashboard under **Settings**, navigate to **Custom Domains**.
2. Click **Add Custom Domain** (e.g., `shield.yourdomain.com`).
3. Add the provided CNAME or ALIAS record in your DNS provider (Cloudflare, Route53, Namecheap).
4. Render automatically provisions and renews a free Let's Encrypt SSL/TLS certificate.
5. BruteShield's HSTS policy automatically enforces HTTPS redirection and prevents protocol downgrades.
