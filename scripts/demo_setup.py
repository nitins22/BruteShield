"""
BruteShield — Demo Setup and Reset Utility
=============================================
Provides controlled demo account provisioning and database reset for faculty
demonstrations.  Demo users are explicitly provisioned — never hardcoded in
production paths.

Usage:
    python scripts/demo_setup.py setup     # Provision demo accounts + verify
    python scripts/demo_setup.py reset     # Delete logs/bruteshield.db and re-init
    python scripts/demo_setup.py verify    # Pre-flight health check
    python scripts/demo_setup.py backup    # Create a backup of the current database
"""

import sys
import os
import sqlite3
import shutil
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bruteshield.config import Config
from bruteshield.database import init_db, get_db


def cmd_setup():
    """Provision demo accounts and verify the environment."""
    print("[setup] Initialising database and seeding default accounts...")
    init_db(Config.DB_PATH)

    conn = get_db(Config.DB_PATH)
    users = conn.execute("SELECT username, role FROM users ORDER BY id").fetchall()
    conn.close()

    print(f"[setup] Database: {Config.DB_PATH}")
    print(f"[setup] Provisioned users:")
    for u in users:
        print(f"         - {u['username']} (role: {u['role']})")

    print("[setup] Demo environment ready.")
    print()
    print("  SOC Dashboard : http://127.0.0.1:5000/dashboard-login")
    print(f"    Username    : {Config.DEFAULT_ADMIN_USER}")
    print(f"    Password    : {Config.DEFAULT_ADMIN_PASS}")
    print()
    print("  User Portal   : http://127.0.0.1:5000/login")
    print(f"    Username    : {Config.DEFAULT_DEMO_USER}")
    print(f"    Password    : {Config.DEFAULT_DEMO_PASS}")
    return 0


def cmd_reset():
    """Delete the database and re-initialise with fresh demo accounts."""
    db_path = Config.DB_PATH
    wal_path = db_path + "-wal"
    shm_path = db_path + "-shm"

    if os.path.exists(db_path):
        print(f"[reset] Removing {db_path}")
        os.remove(db_path)
    if os.path.exists(wal_path):
        os.remove(wal_path)
    if os.path.exists(shm_path):
        os.remove(shm_path)

    print("[reset] Re-initialising database...")
    init_db(db_path)
    print("[reset] Fresh database created with default demo accounts.")
    print("[reset] Restart the BruteShield server to pick up the clean database.")
    return 0


def cmd_verify():
    """Pre-flight health check for faculty demonstration."""
    errors = 0
    print("[verify] Running pre-flight checks...\n")

    # 1. Database
    if os.path.exists(Config.DB_PATH):
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            result = conn.execute("PRAGMA integrity_check;").fetchone()[0]
            conn.close()
            status = "OK" if result == "ok" else f"FAIL ({result})"
            print(f"  [{'OK' if result == 'ok' else 'FAIL'}] Database integrity: {status}")
            if result != "ok":
                errors += 1
        except Exception as e:
            print(f"  [FAIL] Database: {e}")
            errors += 1
    else:
        print(f"  [WARN] Database not found at {Config.DB_PATH} — will be created on server start")

    # 2. ML model
    if os.path.exists(Config.MODEL_PATH):
        size_kb = os.path.getsize(Config.MODEL_PATH) / 1024
        print(f"  [OK]   ML model: {Config.MODEL_PATH} ({size_kb:.0f} KB)")
    else:
        print(f"  [FAIL] ML model not found: {Config.MODEL_PATH}")
        errors += 1

    # 3. Waitress
    try:
        import waitress  # noqa: F401
        print("  [OK]   Waitress installed")
    except ImportError:
        print("  [FAIL] Waitress not installed (pip install waitress)")
        errors += 1

    # 4. Flask app import
    try:
        from bruteshield import create_app
        app = create_app(Config)
        print("  [OK]   Flask application factory")
    except Exception as e:
        print(f"  [FAIL] Flask app: {e}")
        errors += 1

    # 5. HIBP reachability
    try:
        import requests
        r = requests.get("https://api.pwnedpasswords.com/range/5BAA6", timeout=3)
        print(f"  [OK]   HIBP API reachable (HTTP {r.status_code})")
    except Exception:
        print("  [WARN] HIBP API unreachable — offline fallback will apply")

    print(f"\n[verify] {errors} error(s) found.")
    return 1 if errors > 0 else 0


def cmd_backup():
    """Create a SQLite backup using the backup API."""
    if not os.path.exists(Config.DB_PATH):
        print(f"[backup] Database not found: {Config.DB_PATH}")
        return 1

    backup_dir = os.path.join(os.path.dirname(Config.DB_PATH), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"bruteshield_{stamp}.db")

    src = sqlite3.connect(Config.DB_PATH)
    dst = sqlite3.connect(backup_path)
    src.backup(dst)
    dst.close()
    src.close()

    # Verify backup integrity
    verify_conn = sqlite3.connect(backup_path)
    result = verify_conn.execute("PRAGMA integrity_check;").fetchone()[0]
    verify_conn.close()

    if result == "ok":
        size_kb = os.path.getsize(backup_path) / 1024
        print(f"[backup] Created: {backup_path} ({size_kb:.0f} KB)")
        print(f"[backup] Integrity: OK")
    else:
        print(f"[backup] WARNING: Backup integrity check returned: {result}")
        return 1

    return 0


COMMANDS = {
    "setup":  cmd_setup,
    "reset":  cmd_reset,
    "verify": cmd_verify,
    "backup": cmd_backup,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python {sys.argv[0]} <{'|'.join(COMMANDS.keys())}>")
        sys.exit(1)
    sys.exit(COMMANDS[sys.argv[1]]())
