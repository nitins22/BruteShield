#!/usr/bin/env python3
"""
BruteShield — Production SQLite to Managed PostgreSQL Migration Utility

Safely copies existing records from local SQLite database into PostgreSQL
without altering, overwriting, or deleting the original SQLite database.
"""

import argparse
import os
import sqlite3
import sys
import time

# Ensure project root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from bruteshield.config import Config
from bruteshield.database import init_db, is_postgres_target, PostgresConnectionWrapper, convert_placeholders


def sync_postgres_sequences(cur, tables_with_serial):
    """Resets PostgreSQL sequence values to max(id) to prevent primary key collision."""
    for table in tables_with_serial:
        try:
            seq_query = f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1));"
            cur.execute(seq_query)
        except Exception as e:
            # If sequence does not follow default naming convention, continue
            pass


def migrate(sqlite_path: str, pg_url: str, dry_run: bool = False):
    print("=" * 70)
    print("BruteShield Database Migration: SQLite -> PostgreSQL")
    print("=" * 70)
    print(f"Source SQLite File:  {sqlite_path}")
    masked_pg = pg_url.split("@")[-1] if "@" in pg_url else pg_url
    print(f"Target PostgreSQL:   ...@{masked_pg}")
    print(f"Dry Run Mode:        {dry_run}")
    print("-" * 70)

    if not os.path.exists(sqlite_path):
        print(f"[ERROR] Source SQLite database not found at {sqlite_path}")
        return False

    if not is_postgres_target(pg_url):
        print("[ERROR] Target URL is not a valid PostgreSQL URL (must begin with postgresql:// or postgres://)")
        return False

    # Connect to SQLite (read-only mode)
    sqlite_conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # Initialize PostgreSQL schema
    print("[1/9] Ensuring target PostgreSQL schema and indexes exist...")
    if not dry_run:
        init_db(pg_url)

    import psycopg2
    import psycopg2.extras
    normalized_pg_url = pg_url.replace("postgres://", "postgresql://", 1)
    pg_conn = psycopg2.connect(normalized_pg_url)
    pg_conn.autocommit = False
    pg_cur = pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    tables_migrated = {}

    try:
        # 1. Users
        print("[2/9] Migrating 'users'...")
        sqlite_cur.execute("PRAGMA table_info(users)")
        cols = [c["name"] for c in sqlite_cur.fetchall()]
        has_email = "email" in cols
        has_reset = "reset_token" in cols

        if has_email and has_reset:
            users_rows = sqlite_cur.execute("SELECT id, username, password_hash, role, created_at, email, email_verified, reset_token, reset_token_expiry FROM users").fetchall()
        elif has_email:
            users_rows = sqlite_cur.execute("SELECT id, username, password_hash, role, created_at, email, email_verified, NULL as reset_token, NULL as reset_token_expiry FROM users").fetchall()
        else:
            users_rows = sqlite_cur.execute("SELECT id, username, password_hash, role, created_at, NULL as email, 0 as email_verified, NULL as reset_token, NULL as reset_token_expiry FROM users").fetchall()

        count = 0
        for u in users_rows:
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO users (id, username, password_hash, role, created_at, email, email_verified, reset_token, reset_token_expiry)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        username = EXCLUDED.username,
                        password_hash = EXCLUDED.password_hash,
                        role = EXCLUDED.role,
                        email = EXCLUDED.email;
                """, (u["id"], u["username"], u["password_hash"], u["role"], u["created_at"], u["email"], bool(u["email_verified"]), u["reset_token"], u["reset_token_expiry"]))
            count += 1
        tables_migrated["users"] = count

        # 2. Login Attempts
        print("[3/9] Migrating 'login_attempts'...")
        login_rows = sqlite_cur.execute("SELECT id, ip, username, success, timestamp FROM login_attempts").fetchall()
        count = 0
        for r in login_rows:
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO login_attempts (id, ip, username, success, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (r["id"], r["ip"], r["username"], r["success"], r["timestamp"]))
            count += 1
        tables_migrated["login_attempts"] = count

        # 3. Blocked IPs
        print("[4/9] Migrating 'blocked_ips'...")
        block_rows = sqlite_cur.execute("SELECT ip, blocked_until FROM blocked_ips").fetchall()
        count = 0
        for r in block_rows:
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO blocked_ips (ip, blocked_until)
                    VALUES (%s, %s)
                    ON CONFLICT (ip) DO UPDATE SET blocked_until = EXCLUDED.blocked_until;
                """, (r["ip"], r["blocked_until"]))
            count += 1
        tables_migrated["blocked_ips"] = count

        # 4. Block Counts
        print("[5/9] Migrating 'block_counts'...")
        count_rows = sqlite_cur.execute("SELECT ip, count FROM block_counts").fetchall()
        count = 0
        for r in count_rows:
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO block_counts (ip, count)
                    VALUES (%s, %s)
                    ON CONFLICT (ip) DO UPDATE SET count = EXCLUDED.count;
                """, (r["ip"], r["count"]))
            count += 1
        tables_migrated["block_counts"] = count

        # 5. Honeypot Logs
        print("[6/9] Migrating 'honeypot_logs'...")
        honey_rows = sqlite_cur.execute("SELECT id, ip, username_tried, password_tried, password_length, timestamp FROM honeypot_logs").fetchall()
        count = 0
        for r in honey_rows:
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO honeypot_logs (id, ip, username_tried, password_tried, password_length, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (r["id"], r["ip"], r["username_tried"], r["password_tried"], r["password_length"], r["timestamp"]))
            count += 1
        tables_migrated["honeypot_logs"] = count

        # 6. Alerts
        print("[7/9] Migrating 'alerts'...")
        alert_rows = sqlite_cur.execute("SELECT id, level, message, timestamp FROM alerts").fetchall()
        count = 0
        for r in alert_rows:
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO alerts (id, level, message, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (r["id"], r["level"], r["message"], r["timestamp"]))
            count += 1
        tables_migrated["alerts"] = count

        # 7. Alert Acknowledgements
        print("[8/9] Migrating 'alert_acknowledgements'...")
        ack_rows = sqlite_cur.execute("SELECT alert_id, acknowledged_by, acknowledged_at FROM alert_acknowledgements").fetchall()
        count = 0
        for r in ack_rows:
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO alert_acknowledgements (alert_id, acknowledged_by, acknowledged_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (alert_id) DO UPDATE SET acknowledged_by = EXCLUDED.acknowledged_by, acknowledged_at = EXCLUDED.acknowledged_at;
                """, (r["alert_id"], r["acknowledged_by"], r["acknowledged_at"]))
            count += 1
        tables_migrated["alert_acknowledgements"] = count

        # 8. Vault Items
        print("[9/9] Migrating 'vault_items'...")
        vault_rows = sqlite_cur.execute("SELECT id, user_id, service_name, username, encrypted_password, nonce, notes, created_at, updated_at FROM vault_items").fetchall()
        count = 0
        for r in vault_rows:
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO vault_items (id, user_id, service_name, username, encrypted_password, nonce, notes, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        service_name = EXCLUDED.service_name,
                        username = EXCLUDED.username,
                        encrypted_password = EXCLUDED.encrypted_password,
                        nonce = EXCLUDED.nonce,
                        notes = EXCLUDED.notes,
                        updated_at = EXCLUDED.updated_at;
                """, (r["id"], r["user_id"], r["service_name"], r["username"], r["encrypted_password"], r["nonce"], r["notes"], r["created_at"], r["updated_at"]))
            count += 1
        tables_migrated["vault_items"] = count

        if not dry_run:
            # Sync serial sequences
            sync_postgres_sequences(pg_cur, ["users", "login_attempts", "honeypot_logs", "alerts", "vault_items"])
            pg_conn.commit()

        print("=" * 70)
        print("MIGRATION COMPLETED SUCCESSFULLY" if not dry_run else "DRY RUN COMPLETED SUCCESSFULLY")
        print("=" * 70)
        for tbl, cnt in tables_migrated.items():
            print(f" - {tbl.ljust(25)}: {cnt} records migrated")
        print("=" * 70)
        print("Source SQLite file remains untouched and preserved.")
        return True

    except Exception as e:
        if not dry_run:
            pg_conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        return False
    finally:
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()


def main():
    parser = argparse.ArgumentParser(description="BruteShield SQLite to PostgreSQL Data Migration Tool")
    parser.add_argument("--source", default=Config.DB_PATH, help="Path to source SQLite database file")
    parser.add_argument("--target", default=Config.DATABASE_URL, help="Target PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", help="Inspect and count records without writing to target")

    args = parser.parse_args()

    if not args.target:
        print("[ERROR] Target PostgreSQL URL not specified. Provide via --target or DATABASE_URL env var.")
        sys.exit(1)

    success = migrate(args.source, args.target, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
