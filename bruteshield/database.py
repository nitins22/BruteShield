import os
import sqlite3
import time
from werkzeug.security import generate_password_hash
from bruteshield.config import Config

_pg_pool = None


def is_postgres_target(target=None) -> bool:
    """Checks whether the database target is a PostgreSQL URL."""
    url = (target or Config.DATABASE_URL or "").strip()
    return url.startswith("postgresql://") or url.startswith("postgres://")


def convert_placeholders(sql: str) -> str:
    """Converts SQLite ? placeholders to PostgreSQL %s placeholders outside of string literals."""
    parts = []
    in_single = False
    in_double = False
    i = 0
    while i < len(sql):
        c = sql[i]
        if c == "'" and not in_double:
            in_single = not in_single
            parts.append(c)
        elif c == '"' and not in_single:
            in_double = not in_double
            parts.append(c)
        elif c == '?' and not in_single and not in_double:
            parts.append('%s')
        else:
            parts.append(c)
        i += 1
    return ''.join(parts)


class DummyPragmaCursor:
    """Simulates SQLite PRAGMA query results on PostgreSQL."""
    def __init__(self, result=None):
        self._result = result

    def fetchone(self):
        return self._result

    def fetchall(self):
        return [self._result] if self._result is not None else []

    def close(self):
        pass


class PostgresCursorWrapper:
    """Wraps psycopg2 DictCursor for compatibility with SQLite execute syntax."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        sql_stripped = sql.strip()
        upper_sql = sql_stripped.upper()

        # Intercept SQLite PRAGMA statements
        if upper_sql.startswith("PRAGMA"):
            if "JOURNAL_MODE" in upper_sql:
                return DummyPragmaCursor(("PostgreSQL-WAL",))
            return DummyPragmaCursor(None)

        converted_sql = convert_placeholders(sql_stripped)
        if params is not None:
            if isinstance(params, list):
                params = tuple(params)
            elif not isinstance(params, (tuple, dict)):
                params = (params,)
            self._cursor.execute(converted_sql, params)
        else:
            self._cursor.execute(converted_sql)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class PostgresConnectionWrapper:
    """Wraps psycopg2 connection to mimic sqlite3.Connection with connection pool release."""
    def __init__(self, conn, pool=None):
        self._conn = conn
        self._pool = pool
        self._closed = False

    def cursor(self):
        import psycopg2.extras
        raw_cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return PostgresCursorWrapper(raw_cur)

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if not self._closed:
            self._closed = True
            if self._pool is not None:
                self._pool.putconn(self._conn)
            else:
                self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_pg_pool(db_url: str):
    """Initializes and returns the singleton psycopg2 ThreadedConnectionPool."""
    global _pg_pool
    if _pg_pool is None:
        import psycopg2.pool
        normalized_url = db_url.replace("postgres://", "postgresql://", 1)
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=Config.DATABASE_POOL_MIN,
            maxconn=Config.DATABASE_POOL_MAX,
            dsn=normalized_url
        )
    return _pg_pool


def close_db_pool():
    """Closes all connections in the PostgreSQL connection pool."""
    global _pg_pool
    if _pg_pool is not None:
        _pg_pool.closeall()
        _pg_pool = None


def get_db(db_path_or_url=None):
    """
    Establishes a connection to PostgreSQL (if configured) or SQLite.
    Returns a unified connection object supporting .execute(), .commit(), .rollback(), and .close().
    """
    try:
        from flask import current_app, has_app_context
        if not db_path_or_url and has_app_context():
            target = current_app.config.get("DATABASE_URL") or current_app.config.get("DB_PATH")
        else:
            target = db_path_or_url or Config.DATABASE_URL or Config.DB_PATH
    except ImportError:
        target = db_path_or_url or Config.DATABASE_URL or Config.DB_PATH

    target = (target or "").strip()

    if is_postgres_target(target):
        pool = get_pg_pool(target)
        raw_conn = pool.getconn()
        return PostgresConnectionWrapper(raw_conn, pool)

    # Fallback to SQLite
    sqlite_path = target if target and not is_postgres_target(target) else Config.DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)), exist_ok=True)

    conn = sqlite3.connect(sqlite_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path_or_url=None):
    """Initializes database tables, columns, indexes, and initial accounts."""
    try:
        from flask import current_app, has_app_context
        if not db_path_or_url and has_app_context():
            target = current_app.config.get("DATABASE_URL") or current_app.config.get("DB_PATH")
        else:
            target = db_path_or_url or Config.DATABASE_URL or Config.DB_PATH
    except ImportError:
        target = db_path_or_url or Config.DATABASE_URL or Config.DB_PATH

    target = (target or "").strip()
    is_pg = is_postgres_target(target)

    conn = get_db(target)
    cur = conn.cursor()

    if is_pg:
        # PostgreSQL Schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                role VARCHAR(32) NOT NULL DEFAULT 'user',
                created_at DOUBLE PRECISION NOT NULL,
                email VARCHAR(120) UNIQUE,
                email_verified BOOLEAN DEFAULT FALSE,
                reset_token VARCHAR(128),
                reset_token_expiry DOUBLE PRECISION
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id SERIAL PRIMARY KEY,
                ip VARCHAR(64) NOT NULL,
                username VARCHAR(64) NOT NULL,
                success INTEGER NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blocked_ips (
                ip VARCHAR(64) PRIMARY KEY,
                blocked_until DOUBLE PRECISION NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS block_counts (
                ip VARCHAR(64) PRIMARY KEY,
                count INTEGER NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS honeypot_logs (
                id SERIAL PRIMARY KEY,
                ip VARCHAR(64) NOT NULL,
                username_tried VARCHAR(64) NOT NULL,
                password_tried VARCHAR(256) NOT NULL,
                password_length INTEGER DEFAULT 0,
                timestamp DOUBLE PRECISION NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                level VARCHAR(16) NOT NULL,
                message TEXT NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alert_acknowledgements (
                alert_id INTEGER PRIMARY KEY REFERENCES alerts(id) ON DELETE CASCADE,
                acknowledged_by VARCHAR(64) NOT NULL,
                acknowledged_at DOUBLE PRECISION NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vault_items (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                service_name VARCHAR(128) NOT NULL,
                username VARCHAR(128) NOT NULL,
                encrypted_password TEXT NOT NULL,
                nonce TEXT NOT NULL,
                notes TEXT,
                created_at DOUBLE PRECISION NOT NULL,
                updated_at DOUBLE PRECISION NOT NULL
            );
        """)
    else:
        # SQLite Schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at REAL NOT NULL,
                email TEXT,
                email_verified INTEGER DEFAULT 0,
                reset_token TEXT,
                reset_token_expiry REAL
            );
        """)

        # Migration: Ensure email & reset fields exist if table was previously created
        existing_cols = [row["name"] for row in cur.execute("PRAGMA table_info(users)").fetchall()]
        if "email" not in existing_cols:
            cur.execute("ALTER TABLE users ADD COLUMN email TEXT;")
        if "email_verified" not in existing_cols:
            cur.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0;")
        if "reset_token" not in existing_cols:
            cur.execute("ALTER TABLE users ADD COLUMN reset_token TEXT;")
        if "reset_token_expiry" not in existing_cols:
            cur.execute("ALTER TABLE users ADD COLUMN reset_token_expiry REAL;")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                username TEXT NOT NULL,
                success INTEGER NOT NULL,
                timestamp REAL NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blocked_ips (
                ip TEXT PRIMARY KEY,
                blocked_until REAL NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS block_counts (
                ip TEXT PRIMARY KEY,
                count INTEGER NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS honeypot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                username_tried TEXT NOT NULL,
                password_tried TEXT NOT NULL,
                password_length INTEGER DEFAULT 0,
                timestamp REAL NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp REAL NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alert_acknowledgements (
                alert_id INTEGER PRIMARY KEY,
                acknowledged_by TEXT NOT NULL,
                acknowledged_at REAL NOT NULL,
                FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE
            );
        """)
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
            );
        """)

    # Performance & Lookup Indexes (Common)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time ON login_attempts(ip, timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_honeypot_time ON honeypot_logs(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vault_user ON vault_items(user_id);")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);")

    now = time.time()

    # User Account Seeding
    if Config.ENV == "production":
        # In production: Do NOT seed demo accounts. Only seed initial admin if explicitly configured.
        if Config.INITIAL_ADMIN_PASSWORD:
            cur.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?) ON CONFLICT (username) DO NOTHING",
                (Config.INITIAL_ADMIN_USER, generate_password_hash(Config.INITIAL_ADMIN_PASSWORD), "admin", now)
            )
    else:
        # Non-production (dev/test): Seed default admin and demo user accounts for testing convenience
        cur.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?) ON CONFLICT (username) DO NOTHING",
            (Config.DEFAULT_ADMIN_USER, generate_password_hash(Config.DEFAULT_ADMIN_PASS), "admin", now)
        )
        cur.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?) ON CONFLICT (username) DO NOTHING",
            (Config.DEFAULT_DEMO_USER, generate_password_hash(Config.DEFAULT_DEMO_PASS), "user", now)
        )

    conn.commit()
    conn.close()
