# BruteShield — Backup and Disaster Recovery Guide

This runbook outlines the backup, restoration, and disaster recovery procedures for BruteShield production databases hosted on Managed PostgreSQL (Render) and local SQLite instances.

---

## 1. Recovery Objectives

- **Recovery Point Objective (RPO)**: $\le 1\text{ hour}$ (maximum allowable data loss between snapshots).
- **Recovery Time Objective (RTO)**: $\le 15\text{ minutes}$ (time to restore service following database failure).

---

## 2. Render Managed PostgreSQL Automated Backups

Render PostgreSQL provides automated daily backups with point-in-time recovery capabilities on paid instances.
- **Backup Frequency**: Automatic daily full backup retained for 7 days.
- **Location**: Geographically redundant cloud storage managed by Render.
- **Initiating Manual Snapshot via UI**:
  1. Open Render Dashboard and navigate to the PostgreSQL service (`bruteshield-db`).
  2. Click on the **Backups** tab.
  3. Click **Create Backup**.
  4. Wait for status to show **Available**.

---

## 3. Manual Backup Runbook (`pg_dump`)

To create an offsite logical backup of the production database:

### Full Logical Backup (Compressed)
```bash
# Set PostgreSQL connection URL
export DATABASE_URL="postgresql://user:password@hostname:5432/bruteshield"

# Create timestamped compressed dump
pg_dump -Fc --no-acl --no-owner "$DATABASE_URL" > "bruteshield_backup_$(date +%Y%m%d_%H%M%S).dump"
```

### Schema-Only Backup
```bash
pg_dump --schema-only "$DATABASE_URL" > "bruteshield_schema_$(date +%Y%m%d).sql"
```

### Encrypted Archive Storage
Encrypt the database dump using AES-256 before storing in offsite storage (e.g., AWS S3, Google Cloud Storage):
```bash
openssl enc -aes-256-cbc -salt -pbkdf2 \
    -in "bruteshield_backup_$(date +%Y%m%d_%H%M%S).dump" \
    -out "bruteshield_backup_$(date +%Y%m%d_%H%M%S).dump.enc"
```

---

## 4. Disaster Recovery & Restoration Runbook (`pg_restore`)

If database corruption or accidental deletion occurs:

### Step 1: Provision Clean Target Database
Ensure the target database exists and is empty:
```bash
# Drop and recreate database if necessary (CAUTION: Destructive)
dropdb -h hostname -U username bruteshield
createdb -h hostname -U username bruteshield
```

### Step 2: Restore from Compressed Dump
```bash
pg_restore --clean --if-exists --no-owner --no-acl \
    -d "$DATABASE_URL" "bruteshield_backup_20261123_120000.dump"
```

### Step 3: Synchronize Serial Primary Key Sequences
Run the Python synchronization utility to verify all table ID sequences match maximum records:
```bash
python -c "
import psycopg2, os
from bruteshield.database import init_db
init_db(os.environ['DATABASE_URL'])
print('Schema initialized and sequences aligned.')
"
```

### Step 4: Verify Database Health
Probe the health-check endpoint:
```bash
curl -i https://your-bruteshield-app.onrender.com/health
```

---

## 5. Local SQLite Database Backup Runbook

For local development or embedded deployments using SQLite:

### Safe Hot Backup via SQLite CLI
Because SQLite operates in WAL (`journal_mode=WAL`) mode, hot backups can be taken without stopping the web server:
```bash
# Using SQLite's atomic .backup command
sqlite3 logs/bruteshield.db ".backup 'backups/bruteshield_hot_$(date +%Y%m%d_%H%M%S).db'"
```

### Integrity Verification
```bash
sqlite3 "backups/bruteshield_hot_20261123.db" "PRAGMA integrity_check;"
```
Expected output: `ok`.
