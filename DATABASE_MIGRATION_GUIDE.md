# BruteShield — Production Database Migration Guide

This guide details the database architecture, schema definitions, and migration procedures for transitioning from SQLite to Managed PostgreSQL on cloud providers (Render, AWS RDS, Supabase, Neon).

---

## 1. Dual-Engine Architecture

BruteShield supports both **SQLite** (local development, academic testing, embedded mode) and **PostgreSQL** (production multi-user deployment) through an intelligent abstraction layer in `bruteshield/database.py`.

```
                    +---------------------------+
                    |   Application Queries     |
                    |   (auth, vault, ml, soc)   |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |  get_db() Connection Factory
                    +-------------+-------------+
                                  |
            +---------------------+---------------------+
            | (is_postgres_target = True)               | (is_postgres_target = False)
            v                                           v
+-------------------------------+           +-------------------------------+
| ThreadedConnectionPool        |           | sqlite3.connect()             |
|  - Minconn: 2, Maxconn: 10    |           |  - WAL mode (journal_mode=WAL)|
|  - PostgresConnectionWrapper  |           |  - busy_timeout=5000          |
|  - ? -> %s SQL translation    |           |  - foreign_keys=ON            |
|  - Mock PRAGMA handler        |           |  - sqlite3.Row factory        |
|  - psycopg2.extras.DictCursor |           +-------------------------------+
+-------------------------------+
```

### Automatic SQL Parameter Translation
All queries in BruteShield write standard parameter markers (`?`). When connected to PostgreSQL, `PostgresConnectionWrapper` transparently converts unquoted `?` markers to `%s` parameter markers, enabling identical code execution across both databases without code duplication.

---

## 2. Relational Schema Reference

### 2.1 Table: `users`
| Column | SQLite Type | PostgreSQL Type | Constraints | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | `SERIAL` | `PRIMARY KEY` | Auto-incrementing user ID |
| `username` | `TEXT` | `VARCHAR(64)` | `UNIQUE NOT NULL` | Unique account login name |
| `password_hash` | `TEXT` | `VARCHAR(256)` | `NOT NULL` | Werkzeug scrypt/pbkdf2 hash |
| `role` | `TEXT` | `VARCHAR(32)` | `DEFAULT 'user'` | `user` or `admin` |
| `created_at` | `REAL` | `DOUBLE PRECISION` | `NOT NULL` | Epoch timestamp |
| `email` | `TEXT` | `VARCHAR(120)` | `UNIQUE` | Optional user email |
| `email_verified` | `INTEGER` | `BOOLEAN` | `DEFAULT FALSE` | Verification status |
| `reset_token` | `TEXT` | `VARCHAR(128)` | `NULL` | Cryptographic reset token |
| `reset_token_expiry`| `REAL`| `DOUBLE PRECISION` | `NULL` | Token expiration epoch |

### 2.2 Table: `vault_items`
| Column | SQLite Type | PostgreSQL Type | Constraints | Description |
|---|---|---|---|---|
| `id` | `INTEGER` | `SERIAL` | `PRIMARY KEY` | Auto-incrementing item ID |
| `user_id` | `INTEGER` | `INTEGER` | `REFERENCES users(id) ON DELETE CASCADE` | Owner user ID |
| `service_name` | `TEXT` | `VARCHAR(128)` | `NOT NULL` | e.g., "Google", "GitHub" |
| `username` | `TEXT` | `VARCHAR(128)` | `NOT NULL` | Account username |
| `encrypted_password`| `TEXT`| `TEXT` | `NOT NULL` | Base64 AES-256-GCM ciphertext |
| `nonce` | `TEXT` | `TEXT` | `NOT NULL` | Base64 96-bit GCM nonce |
| `notes` | `TEXT` | `TEXT` | `NULL` | Optional encrypted notes |
| `created_at` | `REAL` | `DOUBLE PRECISION` | `NOT NULL` | Epoch timestamp |
| `updated_at` | `REAL` | `DOUBLE PRECISION` | `NOT NULL` | Epoch timestamp |

### 2.3 Telemetry & ML Tables
- **`login_attempts`**: Telemetry log storing `ip`, `username`, `success`, `timestamp` for ML feature extraction.
- **`blocked_ips`**: Actively blocked IPs with `blocked_until` epoch.
- **`block_counts`**: Tracks repeat offenses per IP for adaptive cooldown calculation.
- **`honeypot_logs`**: Logs decoy interactions at `/admin-login` with masked credentials.
- **`alerts`**: System security alerts with level (`HIGH`, `MEDIUM`, `INFO`) and timestamp.
- **`alert_acknowledgements`**: Tracks SOC operator acknowledgements (`acknowledged_by`, `acknowledged_at`).

---

## 3. Migration Procedure: SQLite to PostgreSQL

### Step 1: Pre-Migration Backup
Before running migration, ensure your local SQLite database is backed up:
```bash
cp logs/bruteshield.db logs/bruteshield.db.bak-$(date +%Y%m%d%H%M%S)
```

### Step 2: Dry Run Verification
Execute the migration script in dry-run mode to inspect table row counts without writing to PostgreSQL:
```bash
python scripts/migrate_sqlite_to_postgres.py \
    --source logs/bruteshield.db \
    --target "postgresql://user:password@hostname:5432/bruteshield" \
    --dry-run
```

Expected output:
```
======================================================================
BruteShield Database Migration: SQLite -> PostgreSQL
======================================================================
Source SQLite File:  logs/bruteshield.db
Target PostgreSQL:   ...@hostname:5432/bruteshield
Dry Run Mode:        True
----------------------------------------------------------------------
[1/9] Ensuring target PostgreSQL schema and indexes exist...
[2/9] Migrating 'users'...
[3/9] Migrating 'login_attempts'...
[4/9] Migrating 'blocked_ips'...
[5/9] Migrating 'block_counts'...
[6/9] Migrating 'honeypot_logs'...
[7/9] Migrating 'alerts'...
[8/9] Migrating 'alert_acknowledgements'...
[9/9] Migrating 'vault_items'...
======================================================================
DRY RUN COMPLETED SUCCESSFULLY
======================================================================
 - users                    : 2 records migrated
 - login_attempts           : 48 records migrated
 - blocked_ips              : 2 records migrated
 - block_counts             : 2 records migrated
 - honeypot_logs            : 5 records migrated
 - alerts                   : 12 records migrated
 - alert_acknowledgements   : 3 records migrated
 - vault_items              : 4 records migrated
======================================================================
```

### Step 3: Execute Live Migration
Run the live migration to transfer data and synchronize serial sequences:
```bash
python scripts/migrate_sqlite_to_postgres.py \
    --source logs/bruteshield.db \
    --target "postgresql://user:password@hostname:5432/bruteshield"
```

The script automatically executes `SELECT setval(pg_get_serial_sequence('...', 'id'), MAX(id))` on all tables with primary key sequences so subsequent web application inserts will not experience key collision errors.

---

## 4. Rollback and Disaster Recovery

If you need to roll back:
1. Simply unset `DATABASE_URL` in your environment or Render dashboard.
2. The application will immediately fall back to local SQLite storage at `BRUTESHIELD_DB_PATH`.
3. The source SQLite database is opened in read-only mode during migration and is **never modified or deleted**.
