import os
import pytest
from werkzeug.security import check_password_hash
from bruteshield.database import get_db, init_db
from bruteshield.config import Config

@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_shield.db")
    init_db(db_file)
    return db_file

def test_db_init_and_default_users(temp_db):
    conn = get_db(temp_db)
    cur = conn.cursor()

    # Verify tables exist
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "users" in tables
    assert "login_attempts" in tables
    assert "blocked_ips" in tables
    assert "block_counts" in tables
    assert "honeypot_logs" in tables
    assert "alerts" in tables
    assert "vault_items" in tables

    # Verify default users seeded
    admin_user = cur.execute("SELECT * FROM users WHERE username = ?", (Config.DEFAULT_ADMIN_USER,)).fetchone()
    assert admin_user is not None
    assert admin_user["role"] == "admin"
    assert check_password_hash(admin_user["password_hash"], Config.DEFAULT_ADMIN_PASS)

    demo_user = cur.execute("SELECT * FROM users WHERE username = ?", (Config.DEFAULT_DEMO_USER,)).fetchone()
    assert demo_user is not None
    assert demo_user["role"] == "user"
    assert check_password_hash(demo_user["password_hash"], Config.DEFAULT_DEMO_PASS)

    conn.close()

def test_wal_mode_enabled(temp_db):
    conn = get_db(temp_db)
    mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    assert mode.lower() == "wal"
    conn.close()
