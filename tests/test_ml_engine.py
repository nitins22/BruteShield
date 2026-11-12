import time
import pytest
from bruteshield.database import init_db, get_db
from bruteshield.ml.engine import (
    get_features_for_ip,
    block_ip,
    is_ip_blocked,
    log_attempt
)
from bruteshield.config import Config

@pytest.fixture
def temp_ml_db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_ml.db")
    init_db(db_file)
    monkeypatch.setattr(Config, "DB_PATH", db_file)
    return db_file

def test_sliding_window_features(temp_ml_db):
    ip = "198.51.100.99"
    now = time.time()

    conn = get_db(temp_ml_db)
    # Insert old attempt outside 15 min window (1800s ago)
    conn.execute(
        "INSERT INTO login_attempts (ip, username, success, timestamp) VALUES (?, ?, ?, ?)",
        (ip, "user1", 0, now - 1800)
    )
    # Insert 3 recent failed attempts (within window)
    conn.execute(
        "INSERT INTO login_attempts (ip, username, success, timestamp) VALUES (?, ?, ?, ?)",
        (ip, "user2", 0, now - 50)
    )
    conn.execute(
        "INSERT INTO login_attempts (ip, username, success, timestamp) VALUES (?, ?, ?, ?)",
        (ip, "user3", 0, now - 30)
    )
    conn.execute(
        "INSERT INTO login_attempts (ip, username, success, timestamp) VALUES (?, ?, ?, ?)",
        (ip, "user4", 0, now - 10)
    )
    conn.commit()
    conn.close()

    # Features with 900s sliding window should only see the 3 recent attempts
    features_windowed = get_features_for_ip(ip, window_seconds=900)
    assert features_windowed[0][0] == 3  # total_attempts in window
    assert features_windowed[0][1] == 3  # failed_attempts
    assert features_windowed[0][2] == 3  # distinct_usernames (user2, user3, user4)
    assert features_windowed[0][5] == 1.0  # failure_ratio

    # Features without window should see all 4
    features_all = get_features_for_ip(ip, window_seconds=0)
    assert features_all[0][0] == 4

def test_cooldown_escalation(temp_ml_db):
    ip = "203.0.113.88"
    
    # 1st block -> 60s
    d1 = block_ip(ip)
    assert d1 == 60
    blocked, until1 = is_ip_blocked(ip)
    assert blocked is True

    # 2nd block -> 300s
    d2 = block_ip(ip)
    assert d2 == 300

    # 3rd block -> 900s
    d3 = block_ip(ip)
    assert d3 == 900

    # 4th block -> 3600s
    d4 = block_ip(ip)
    assert d4 == 3600
