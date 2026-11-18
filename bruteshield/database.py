import sqlite3
import time
import os
from werkzeug.security import generate_password_hash
from bruteshield.config import Config

def get_db(db_path=None):
    """Establishes a thread-safe connection to the SQLite database with WAL mode."""
    target_path = db_path or Config.DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    
    conn = sqlite3.connect(target_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency & avoid database locking issues
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db(db_path=None):
    """Initializes all database tables, indexes, and default admin/demo accounts."""
    conn = get_db(db_path)
    cur = conn.cursor()
    
    # 1. Users table (real database authentication)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at REAL NOT NULL
        )
    """)

    # 2. Login attempts log (telemetry for ML behavioral engine)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            username TEXT NOT NULL,
            success INTEGER NOT NULL,
            timestamp REAL NOT NULL
        )
    """)

    # 3. Blocked IPs with expiration timestamp
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocked_ips (
            ip TEXT PRIMARY KEY,
            blocked_until REAL NOT NULL
        )
    """)

    # 4. Repeat offender block counters (adaptive cool-down)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS block_counts (
            ip TEXT PRIMARY KEY,
            count INTEGER NOT NULL
        )
    """)

    # 5. Honeypot decoy access logs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS honeypot_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            username_tried TEXT NOT NULL,
            password_tried TEXT NOT NULL,
            password_length INTEGER DEFAULT 0,
            timestamp REAL NOT NULL
        )
    """)

    # 6. Security alerts (HIGH / MEDIUM / INFO)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)

    # 6b. Alert acknowledgements (SOC status management)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alert_acknowledgements (
            alert_id INTEGER PRIMARY KEY,
            acknowledged_by TEXT NOT NULL,
            acknowledged_at REAL NOT NULL,
            FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE
        )
    """)

    # 7. Secure Password Vault for registered users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vault_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            nonce TEXT NOT NULL,
            notes TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Performance indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time ON login_attempts(ip, timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_honeypot_time ON honeypot_logs(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vault_user ON vault_items(user_id);")

    # Seed default accounts if not already present
    now = time.time()
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (Config.DEFAULT_ADMIN_USER, generate_password_hash(Config.DEFAULT_ADMIN_PASS), "admin", now)
    )
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (Config.DEFAULT_DEMO_USER, generate_password_hash(Config.DEFAULT_DEMO_PASS), "user", now)
    )

    conn.commit()
    conn.close()
