import time
import os
import joblib
from bruteshield.config import Config
from bruteshield.database import get_db
from bruteshield.security import mask_password

_cached_model = None

def get_ml_model():
    """Loads the serialized Isolation Forest model, caching it in memory."""
    global _cached_model
    if _cached_model is None:
        if os.path.exists(Config.MODEL_PATH):
            try:
                _cached_model = joblib.load(Config.MODEL_PATH)
            except Exception as e:
                print(f"[WARN] Failed to load ML model from {Config.MODEL_PATH}: {e}")
                _cached_model = None
        else:
            print(f"[WARN] Model file not found at {Config.MODEL_PATH}")
    return _cached_model


def get_features_for_ip(ip: str, window_seconds: int = None) -> list[list[float]]:
    """
    Extracts the 6 behavioral features for an IP address within a sliding time window.
    
    Feature Vector:
    [total_attempts, failed_attempts, distinct_usernames, avg_gap, min_gap, failure_ratio]
    """
    conn = get_db()
    window = window_seconds if window_seconds is not None else Config.SLIDING_WINDOW_SECONDS
    
    if window and window > 0:
        since_time = time.time() - window
        rows = conn.execute(
            "SELECT username, success, timestamp FROM login_attempts WHERE ip = ? AND timestamp >= ? ORDER BY timestamp ASC",
            (ip, since_time)
        ).fetchall()
        # If no attempts in the sliding window, fallback to all-time count if needed, or return empty features
        if not rows:
            conn.close()
            return [[0, 0, 0, 0.0, 0.0, 0.0]]
    else:
        rows = conn.execute(
            "SELECT username, success, timestamp FROM login_attempts WHERE ip = ? ORDER BY timestamp ASC",
            (ip,)
        ).fetchall()
        
    conn.close()

    total_attempts = len(rows)
    if total_attempts == 0:
        return [[0, 0, 0, 0.0, 0.0, 0.0]]

    failed_attempts = sum(1 for r in rows if r["success"] == 0)
    distinct_usernames = len(set(r["username"] for r in rows))

    timestamps = [r["timestamp"] for r in rows]
    if len(timestamps) > 1:
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        avg_gap = round(sum(gaps) / len(gaps), 3)
        min_gap = round(min(gaps), 3)
    else:
        avg_gap = 0.0
        min_gap = 0.0

    failure_ratio = round(failed_attempts / total_attempts, 3)

    return [[total_attempts, failed_attempts, distinct_usernames, avg_gap, min_gap, failure_ratio]]


def is_suspicious_by_ml(ip: str) -> bool:
    """Evaluates whether an IP shows anomalous brute-force or credential-stuffing behavior."""
    model = get_ml_model()
    features = get_features_for_ip(ip)
    
    # If no recorded history yet, cannot be suspicious
    if features[0][0] == 0:
        return False
        
    if model is not None:
        try:
            prediction = model.predict(features)
            return bool(prediction[0] == -1)
        except Exception as e:
            print(f"[ERROR] ML prediction failed: {e}")
            
    # Fallback to threshold rule if model unavailable
    return is_suspicious_by_rule(ip)


def is_suspicious_by_rule(ip: str) -> bool:
    """Baseline fallback detection: flags if failed attempts exceed limit within time window."""
    conn = get_db()
    since = time.time() - Config.TIME_WINDOW_SECONDS
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts WHERE ip = ? AND success = 0 AND timestamp >= ?",
        (ip, since)
    ).fetchone()
    conn.close()
    return bool(row and row["cnt"] >= Config.MAX_FAILED_ATTEMPTS)


def needs_captcha(ip: str) -> bool:
    """Determines if an IP score falls in the borderline warning band requiring CAPTCHA challenge."""
    features = get_features_for_ip(ip)
    if features[0][0] == 0:
        return False
        
    model = get_ml_model()
    if model is not None:
        try:
            score = model.decision_function(features)[0]
            # score < 0 means anomaly (hard block handled elsewhere).
            # 0 <= score < CAPTCHA_SCORE_LIMIT indicates suspicious borderline pattern
            return bool(0 <= score < Config.CAPTCHA_SCORE_LIMIT)
        except Exception as e:
            print(f"[ERROR] Decision function error: {e}")
            
    # Rule-based borderline check: 3 or 4 failures in window
    conn = get_db()
    since = time.time() - Config.TIME_WINDOW_SECONDS
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts WHERE ip = ? AND success = 0 AND timestamp >= ?",
        (ip, since)
    ).fetchone()
    conn.close()
    return bool(row and 3 <= row["cnt"] < Config.MAX_FAILED_ATTEMPTS)


def is_ip_blocked(ip: str) -> tuple[bool, float | None]:
    """Checks whether the specified IP is actively blocked in the database."""
    conn = get_db()
    row = conn.execute(
        "SELECT blocked_until FROM blocked_ips WHERE ip = ?", (ip,)
    ).fetchone()
    conn.close()
    
    if row and row["blocked_until"] > time.time():
        return True, row["blocked_until"]
    return False, None


def block_ip(ip: str) -> int:
    """
    Blocks the specified IP using adaptive cooldown.
    Block durations escalate: 1m -> 5m -> 15m -> 1h.
    """
    conn = get_db()
    row = conn.execute("SELECT count FROM block_counts WHERE ip = ?", (ip,)).fetchone()
    previous_blocks = row["count"] if row else 0

    duration = Config.BLOCK_DURATIONS[min(previous_blocks, len(Config.BLOCK_DURATIONS) - 1)]
    until = time.time() + duration

    conn.execute(
        "INSERT INTO blocked_ips (ip, blocked_until) VALUES (?, ?) "
        "ON CONFLICT(ip) DO UPDATE SET blocked_until = excluded.blocked_until",
        (ip, until)
    )
    conn.execute(
        "INSERT INTO block_counts (ip, count) VALUES (?, 1) "
        "ON CONFLICT(ip) DO UPDATE SET count = count + 1",
        (ip,)
    )
    conn.commit()
    conn.close()
    return duration


def log_attempt(ip: str, username: str, success: bool):
    """Logs a login attempt to the telemetry database."""
    conn = get_db()
    conn.execute(
        "INSERT INTO login_attempts (ip, username, success, timestamp) VALUES (?, ?, ?, ?)",
        (ip, username, int(success), time.time())
    )
    conn.commit()
    conn.close()


def create_alert(level: str, message: str):
    """Records a security alert into the database and audit trail."""
    conn = get_db()
    conn.execute(
        "INSERT INTO alerts (level, message, timestamp) VALUES (?, ?, ?)",
        (level, message, time.time())
    )
    conn.commit()
    conn.close()
    print(f"[ALERT-{level}] {message}")


def log_honeypot_attempt(ip: str, username: str, password: str):
    """
    Logs an unauthorized access attempt to the honeypot decoy.
    Vulnerability Fix: Never stores plaintext passwords in the database!
    Stores masked representation while preserving password length context.
    """
    conn = get_db()
    masked = mask_password(password)
    length = len(password) if password else 0
    conn.execute(
        "INSERT INTO honeypot_logs (ip, username_tried, password_tried, password_length, timestamp) VALUES (?, ?, ?, ?, ?)",
        (ip, username, masked, length, time.time())
    )
    conn.commit()
    conn.close()


def get_anomaly_score_for_ip(ip: str) -> dict:
    """
    Computes continuous anomaly score and feature breakdown for an IP.
    Returns feature dictionary, raw score, anomaly verdict, and rule-based fallback status.
    """
    features = get_features_for_ip(ip)
    feat_names = ["total_attempts", "failed_attempts", "distinct_usernames", "avg_gap", "min_gap", "failure_ratio"]
    feat_dict = dict(zip(feat_names, features[0]))

    model = get_ml_model()
    raw_score = None
    is_anomaly = False
    decision = "NORMAL"

    if features[0][0] > 0 and model is not None:
        try:
            raw_score = float(model.decision_function(features)[0])
            pred = int(model.predict(features)[0])
            is_anomaly = (pred == -1)
            if is_anomaly:
                decision = "ANOMALY_BLOCKED"
            elif 0 <= raw_score < Config.CAPTCHA_SCORE_LIMIT:
                decision = "SUSPICIOUS_CAPTCHA"
            else:
                decision = "NORMAL"
        except Exception as e:
            print(f"[ERROR] Anomaly scoring failed: {e}")

    # Fallback to rule if model didn't run
    if raw_score is None and features[0][0] > 0:
        if is_suspicious_by_rule(ip):
            is_anomaly = True
            decision = "RULE_BLOCKED"

    return {
        "ip": ip,
        "features": feat_dict,
        "raw_score": round(raw_score, 4) if raw_score is not None else None,
        "is_anomaly": is_anomaly,
        "decision": decision
    }


def unblock_ip_manual(ip: str) -> bool:
    """Removes an IP from the blocked list."""
    conn = get_db()
    conn.execute("DELETE FROM blocked_ips WHERE ip = ?", (ip,))
    conn.commit()
    conn.close()
    return True


def acknowledge_alert(alert_id: int, admin_user: str) -> bool:
    """Marks a security alert as acknowledged by an operator."""
    conn = get_db()
    conn.execute(
        "INSERT INTO alert_acknowledgements (alert_id, acknowledged_by, acknowledged_at) "
        "VALUES (?, ?, ?) ON CONFLICT(alert_id) DO UPDATE SET acknowledged_by = excluded.acknowledged_by, acknowledged_at = excluded.acknowledged_at",
        (alert_id, admin_user, time.time())
    )
    conn.commit()
    conn.close()
    return True


def get_model_metadata() -> dict:
    """Returns metadata and verified integrity for the loaded ML model."""
    import hashlib
    model = get_ml_model()
    exists = os.path.exists(Config.MODEL_PATH)
    sha256 = None
    if exists:
        try:
            with open(Config.MODEL_PATH, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest().upper()
        except (OSError, IOError) as e:
            print(f"[WARN] Failed to compute model hash: {e}")
            sha256 = None

    return {
        "loaded": model is not None,
        "model_type": type(model).__name__ if model is not None else "None",
        "model_path": Config.MODEL_PATH,
        "sha256": sha256,
        "feature_count": 6,
        "features": [
            "total_attempts",
            "failed_attempts",
            "distinct_usernames",
            "avg_gap_seconds",
            "min_gap_seconds",
            "failure_ratio"
        ],
        "sliding_window_seconds": Config.SLIDING_WINDOW_SECONDS,
        "captcha_score_limit": Config.CAPTCHA_SCORE_LIMIT
    }

