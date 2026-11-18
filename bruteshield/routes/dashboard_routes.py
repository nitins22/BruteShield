import os
import time
from functools import wraps
from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash

from bruteshield.config import Config
from bruteshield.database import get_db
from bruteshield.security import get_client_ip, generate_captcha_challenge
from bruteshield.ml.engine import (
    is_ip_blocked,
    needs_captcha,
    is_suspicious_by_ml,
    block_ip,
    log_attempt,
    create_alert,
    get_features_for_ip,
    get_anomaly_score_for_ip,
    get_model_metadata,
    unblock_ip_manual,
    acknowledge_alert
)
from bruteshield.benchmarks import get_benchmarks_data

dashboard_bp = Blueprint("dashboard", __name__)


def admin_required(func):
    """Ensures caller has valid administrative session."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            if request.path.startswith("/dashboard/api") or request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized", "message": "Admin credentials required"}), 401
            return redirect(url_for("dashboard.dashboard_login"))
        return func(*args, **kwargs)
    return wrapper


@dashboard_bp.route("/dashboard-login", methods=["GET", "POST"])
def dashboard_login():
    ip = get_client_ip(request)

    blocked, until = is_ip_blocked(ip)
    if blocked:
        wait_seconds = max(1, int(until - time.time()))
        return render_template(
            "dashboard_login.html",
            message=f"Too many failed attempts. Try again in {wait_seconds} seconds.",
            blocked=True
        )

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) > 64 or len(password) > 256:
            return render_template("dashboard_login.html", message="Invalid admin credentials format.", blocked=False)

        captcha_ok = True
        if needs_captcha(ip):
            user_captcha = request.form.get("captcha", "").strip()
            expected = session.get("captcha_answer")
            captcha_ok = bool(expected and user_captcha == expected)

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        password_ok = bool(user and user["role"] == "admin" and check_password_hash(user["password_hash"], password))
        success = captcha_ok and password_ok

        log_attempt(ip, username, success)

        if success:
            session.clear()  # Session fixation defense
            session["is_admin"] = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = "admin"
            return redirect(url_for("dashboard.dashboard_view"))

        if is_suspicious_by_ml(ip):
            duration = block_ip(ip)
            create_alert("HIGH", f"IP {ip} blocked for {duration}s - brute-force on ADMIN dashboard login")
            return render_template(
                "dashboard_login.html",
                message=f"Suspicious pattern detected by ML model. Blocked for {duration} seconds.",
                blocked=True
            )

        if needs_captcha(ip):
            challenge = generate_captcha_challenge()
            session["captcha_answer"] = challenge["answer"]
            create_alert("MEDIUM", f"IP {ip} suspicious pattern on ADMIN login - CAPTCHA challenge presented")
            msg = "CAPTCHA incorrect. Please try again." if not captcha_ok else "Invalid admin credentials. Please solve the CAPTCHA."
            return render_template("dashboard_login.html", message=msg, blocked=False, captcha_question=challenge["question"])

        return render_template("dashboard_login.html", message="Invalid admin credentials.", blocked=False)

    question = None
    if needs_captcha(ip):
        challenge = generate_captcha_challenge()
        session["captcha_answer"] = challenge["answer"]
        question = challenge["question"]

    return render_template("dashboard_login.html", message=None, blocked=False, captcha_question=question)


@dashboard_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard_view():
    """Renders the comprehensive enterprise SOC dashboard."""
    conn = get_db()
    total_attempts = conn.execute("SELECT COUNT(*) as cnt FROM login_attempts").fetchone()["cnt"]
    blocked_count = conn.execute("SELECT COUNT(*) as cnt FROM blocked_ips WHERE blocked_until > ?", (time.time(),)).fetchone()["cnt"]
    honeypot_count = conn.execute("SELECT COUNT(*) as cnt FROM honeypot_logs").fetchone()["cnt"]
    user_count = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]

    recent_attempts = conn.execute(
        "SELECT ip, username, success, timestamp FROM login_attempts ORDER BY timestamp DESC LIMIT 15"
    ).fetchall()

    recent_honeypot = conn.execute(
        "SELECT ip, username_tried, password_tried, timestamp FROM honeypot_logs ORDER BY timestamp DESC LIMIT 15"
    ).fetchall()

    recent_alerts = [
        {
            "id": r["id"],
            "level": r["level"],
            "message": r["message"],
            "time": time.strftime("%d %b %H:%M:%S", time.localtime(r["timestamp"])),
            "timestamp": r["timestamp"]
        }
        for r in conn.execute("SELECT id, level, message, timestamp FROM alerts ORDER BY timestamp DESC LIMIT 15").fetchall()
    ]
    conn.close()

    model_meta = get_model_metadata()

    return render_template(
        "dashboard.html",
        admin_username=session.get("username", "Administrator"),
        total_attempts=total_attempts,
        blocked_count=blocked_count,
        honeypot_count=honeypot_count,
        user_count=user_count,
        recent_attempts=recent_attempts,
        recent_honeypot=recent_honeypot,
        recent_alerts=recent_alerts,
        model_meta=model_meta
    )


# -------------------------------------------------------------------------
# REST APIs for Live SOC Dashboard
# -------------------------------------------------------------------------

@dashboard_bp.route("/dashboard/api/overview", methods=["GET"])
@admin_required
def api_overview():
    """Aggregated operational metrics for Security Overview card and status."""
    now = time.time()
    conn = get_db()
    
    total = conn.execute("SELECT COUNT(*) as cnt FROM login_attempts").fetchone()["cnt"]
    failed = conn.execute("SELECT COUNT(*) as cnt FROM login_attempts WHERE success = 0").fetchone()["cnt"]
    success = total - failed
    fail_rate = round((failed / total * 100), 1) if total > 0 else 0.0

    active_blocks = conn.execute("SELECT COUNT(*) as cnt FROM blocked_ips WHERE blocked_until > ?", (now,)).fetchone()["cnt"]
    honeypot_hits = conn.execute("SELECT COUNT(*) as cnt FROM honeypot_logs").fetchone()["cnt"]
    user_count = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
    
    # Active/Unacknowledged alert count
    unacked_alerts = conn.execute("""
        SELECT COUNT(*) as cnt FROM alerts a
        LEFT JOIN alert_acknowledgements ack ON a.id = ack.alert_id
        WHERE ack.alert_id IS NULL
    """).fetchone()["cnt"]

    # System Status Determination:
    # UNDER_ATTACK if >5 active blocks or >10 failures in last 5 minutes
    five_min_ago = now - 300
    recent_fails = conn.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts WHERE success = 0 AND timestamp >= ?", (five_min_ago,)
    ).fetchone()["cnt"]
    
    if active_blocks >= 3 or recent_fails >= 10:
        system_status = "ELEVATED_THREAT"
        status_color = "#f43f5e"
    elif active_blocks > 0 or recent_fails > 0:
        system_status = "GUARDED"
        status_color = "#f59e0b"
    else:
        system_status = "NORMAL_SECURE"
        status_color = "#10b981"

    # Hourly Trend - buckets of last 12 hours (or available recent data)
    hours = 12
    bucket_size = 3600
    start_time = now - (hours * bucket_size)
    trend_rows = conn.execute("""
        SELECT 
            CAST((timestamp - ?) / ? AS INTEGER) as bucket,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as ok_cnt,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as fail_cnt
        FROM login_attempts
        WHERE timestamp >= ?
        GROUP BY bucket
        ORDER BY bucket ASC
    """, (start_time, bucket_size, start_time)).fetchall()

    bucket_dict = {r["bucket"]: (r["ok_cnt"], r["fail_cnt"]) for r in trend_rows}
    timeline_labels = []
    timeline_success = []
    timeline_fail = []

    for b in range(hours):
        t_instant = start_time + (b * bucket_size)
        label = time.strftime("%H:%M", time.localtime(t_instant))
        ok_c, fail_c = bucket_dict.get(b, (0, 0))
        timeline_labels.append(label)
        timeline_success.append(ok_c)
        timeline_fail.append(fail_c)

    # Recent security events (last 10 merged chronologically)
    recent_events = []
    
    # 1. Recent logins
    logins = conn.execute(
        "SELECT 'AUTH' as type, ip, username as detail, success, timestamp FROM login_attempts ORDER BY timestamp DESC LIMIT 6"
    ).fetchall()
    for l in logins:
        recent_events.append({
            "type": "AUTHENTICATION",
            "source": l["ip"],
            "detail": f"User '{l['detail']}' - {'Success' if l['success'] else 'Failed'}",
            "status": "success" if l["success"] else "failure",
            "time": time.strftime("%H:%M:%S", time.localtime(l["timestamp"])),
            "timestamp": l["timestamp"]
        })

    # 2. Recent honeypot hits
    honey = conn.execute(
        "SELECT 'HONEYPOT' as type, ip, username_tried as detail, timestamp FROM honeypot_logs ORDER BY timestamp DESC LIMIT 4"
    ).fetchall()
    for h in honey:
        recent_events.append({
            "type": "HONEYPOT_HIT",
            "source": h["ip"],
            "detail": f"Decoy hit on /admin-login (tried '{h['detail']}')",
            "status": "critical",
            "time": time.strftime("%H:%M:%S", time.localtime(h["timestamp"])),
            "timestamp": h["timestamp"]
        })

    recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_events = recent_events[:10]

    conn.close()

    return jsonify({
        "success": True,
        "timestamp": now,
        "metrics": {
            "total_attempts": total,
            "failed_attempts": failed,
            "success_attempts": success,
            "failure_rate": fail_rate,
            "active_blocks": active_blocks,
            "unacknowledged_alerts": unacked_alerts,
            "honeypot_triggers": honeypot_hits,
            "registered_users": user_count,
            "system_status": system_status,
            "status_color": status_color
        },
        "timeline": {
            "labels": timeline_labels,
            "success": timeline_success,
            "failures": timeline_fail
        },
        "recent_activity": recent_events
    })


@dashboard_bp.route("/dashboard/api/live-feed", methods=["GET"])
@admin_required
def api_live_feed():
    """Live streaming authentication telemetry with search, filtering, and pagination."""
    now = time.time()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(5, int(request.args.get("limit", 20))))
    offset = (page - 1) * limit
    status_filter = request.args.get("filter", "all").lower()
    search = request.args.get("search", "").strip()

    conn = get_db()
    
    search_param = f"%{search}%" if search else None

    count_query = """
        SELECT COUNT(*) as cnt 
        FROM login_attempts la
        LEFT JOIN blocked_ips b ON la.ip = b.ip
        WHERE (? = 'all' 
               OR (? = 'failed' AND la.success = 0)
               OR (? = 'success' AND la.success = 1)
               OR (? = 'blocked' AND b.blocked_until > ?))
          AND (? IS NULL OR la.ip LIKE ? OR la.username LIKE ?)
    """
    total_count = conn.execute(count_query, (
        status_filter, status_filter, status_filter, status_filter, now,
        search_param, search_param, search_param
    )).fetchone()["cnt"]

    query = """
        SELECT 
            la.id, la.ip, la.username, la.success, la.timestamp,
            CASE WHEN b.blocked_until > ? THEN 1 ELSE 0 END as is_blocked,
            b.blocked_until
        FROM login_attempts la
        LEFT JOIN blocked_ips b ON la.ip = b.ip
        WHERE (? = 'all' 
               OR (? = 'failed' AND la.success = 0)
               OR (? = 'success' AND la.success = 1)
               OR (? = 'blocked' AND b.blocked_until > ?))
          AND (? IS NULL OR la.ip LIKE ? OR la.username LIKE ?)
        ORDER BY la.timestamp DESC
        LIMIT ? OFFSET ?
    """
    
    rows = conn.execute(query, (
        now,
        status_filter, status_filter, status_filter, status_filter, now,
        search_param, search_param, search_param,
        limit, offset
    )).fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "ip": r["ip"],
            "username": r["username"],
            "success": bool(r["success"]),
            "timestamp": r["timestamp"],
            "time_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["timestamp"])),
            "is_blocked": bool(r["is_blocked"]),
            "blocked_until": r["blocked_until"]
        })

    conn.close()

    return jsonify({
        "success": True,
        "items": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1
        }
    })


@dashboard_bp.route("/dashboard/api/threats", methods=["GET"])
@admin_required
def api_threats():
    """Returns detected alerts, active IP quarantine table, and anomaly statistics."""
    now = time.time()
    conn = get_db()

    # Active blocked IPs
    blocked_rows = conn.execute("""
        SELECT b.ip, b.blocked_until, COALESCE(bc.count, 1) as block_count
        FROM blocked_ips b
        LEFT JOIN block_counts bc ON b.ip = bc.ip
        WHERE b.blocked_until > ?
        ORDER BY b.blocked_until DESC
    """, (now,)).fetchall()

    blocked_list = []
    for r in blocked_rows:
        remaining_secs = max(0, int(r["blocked_until"] - now))
        blocked_list.append({
            "ip": r["ip"],
            "blocked_until": r["blocked_until"],
            "remaining_seconds": remaining_secs,
            "remaining_formatted": f"{remaining_secs // 60}m {remaining_secs % 60}s",
            "block_count": r["block_count"],
            "features": get_anomaly_score_for_ip(r["ip"])
        })

    # Alerts with acknowledgement status
    alert_rows = conn.execute("""
        SELECT a.id, a.level, a.message, a.timestamp, ack.acknowledged_by, ack.acknowledged_at
        FROM alerts a
        LEFT JOIN alert_acknowledgements ack ON a.id = ack.alert_id
        ORDER BY a.timestamp DESC
        LIMIT 50
    """).fetchall()

    alerts_list = []
    for a in alert_rows:
        alerts_list.append({
            "id": a["id"],
            "level": a["level"],
            "message": a["message"],
            "timestamp": a["timestamp"],
            "time_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a["timestamp"])),
            "is_acknowledged": a["acknowledged_by"] is not None,
            "acknowledged_by": a["acknowledged_by"],
            "acknowledged_at": a["acknowledged_at"]
        })

    conn.close()

    return jsonify({
        "success": True,
        "timestamp": now,
        "active_blocks": blocked_list,
        "alerts": alerts_list
    })


@dashboard_bp.route("/dashboard/api/threats/acknowledge/<int:alert_id>", methods=["POST"])
@admin_required
def api_acknowledge_alert(alert_id):
    """Marks an alert as acknowledged by the current admin user."""
    admin_user = session.get("username", "admin")
    acknowledge_alert(alert_id, admin_user)
    return jsonify({
        "success": True,
        "message": f"Alert #{alert_id} acknowledged by {admin_user}",
        "alert_id": alert_id,
        "acknowledged_by": admin_user,
        "timestamp": time.time()
    })


@dashboard_bp.route("/dashboard/api/analytics", methods=["GET"])
@admin_required
def api_analytics():
    """Detailed telemetry analytics: target accounts, attacker distribution, and failure rates."""
    conn = get_db()

    # Top targeted usernames
    targeted_users = conn.execute("""
        SELECT username, 
               COUNT(*) as total_attempts,
               SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
        FROM login_attempts
        GROUP BY username
        ORDER BY total_attempts DESC
        LIMIT 8
    """).fetchall()

    targeted_list = [
        {
            "username": r["username"],
            "total": r["total_attempts"],
            "failures": r["failures"],
            "successes": r["successes"],
            "fail_rate": round(r["failures"] / r["total_attempts"] * 100, 1) if r["total_attempts"] > 0 else 0
        }
        for r in targeted_users
    ]

    # Top source IPs by failure count
    source_ips = conn.execute("""
        SELECT ip,
               COUNT(*) as total_attempts,
               SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures,
               COUNT(DISTINCT username) as distinct_users,
               MAX(timestamp) as last_seen
        FROM login_attempts
        GROUP BY ip
        ORDER BY failures DESC, total_attempts DESC
        LIMIT 8
    """).fetchall()

    source_list = [
        {
            "ip": r["ip"],
            "total": r["total_attempts"],
            "failures": r["failures"],
            "distinct_users": r["distinct_users"],
            "last_seen_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["last_seen"])),
            "fail_rate": round(r["failures"] / r["total_attempts"] * 100, 1) if r["total_attempts"] > 0 else 0
        }
        for r in source_ips
    ]

    # Daily aggregation over the last 7 days
    now = time.time()
    seven_days_ago = now - (7 * 86400)
    daily_rows = conn.execute("""
        SELECT 
            strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch', 'localtime')) as day,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as ok_cnt,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as fail_cnt
        FROM login_attempts
        WHERE timestamp >= ?
        GROUP BY day
        ORDER BY day ASC
    """, (seven_days_ago,)).fetchall()

    daily_labels = [r["day"] for r in daily_rows]
    daily_ok = [r["ok_cnt"] for r in daily_rows]
    daily_fail = [r["fail_cnt"] for r in daily_rows]

    conn.close()

    return jsonify({
        "success": True,
        "targeted_users": targeted_list,
        "source_ips": source_list,
        "daily_trend": {
            "labels": daily_labels,
            "success": daily_ok,
            "failures": daily_fail
        }
    })


@dashboard_bp.route("/dashboard/api/benchmarks", methods=["GET"])
@admin_required
def api_benchmarks():
    """
    Returns verified benchmark evaluation data strictly partitioned by source:
    1. Synthetic Benchmark (Phase 1 Baseline)
    2. LANL Real-World Enterprise Benchmark (Phase 2B Empirical Slice)
    """
    data = get_benchmarks_data()
    return jsonify({
        "success": True,
        "data": data,
        "notice": "Benchmark data is strictly separate from live operational telemetry. Never mixed."
    })


@dashboard_bp.route("/dashboard/api/honeypot", methods=["GET"])
@admin_required
def api_honeypot():
    """Returns honeypot decoy logs with masked credentials (zero plain-text password leakage)."""
    now = time.time()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(5, int(request.args.get("limit", 20))))
    offset = (page - 1) * limit
    search = request.args.get("search", "").strip()

    conn = get_db()
    
    search_param = f"%{search}%" if search else None

    count_query = """
        SELECT COUNT(*) as cnt FROM honeypot_logs h
        WHERE (? IS NULL OR h.ip LIKE ? OR h.username_tried LIKE ?)
    """
    total = conn.execute(count_query, (search_param, search_param, search_param)).fetchone()["cnt"]

    query = """
        SELECT h.id, h.ip, h.username_tried, h.password_tried, h.password_length, h.timestamp,
               CASE WHEN b.blocked_until > ? THEN 1 ELSE 0 END as is_blocked,
               b.blocked_until
        FROM honeypot_logs h
        LEFT JOIN blocked_ips b ON h.ip = b.ip
        WHERE (? IS NULL OR h.ip LIKE ? OR h.username_tried LIKE ?)
        ORDER BY h.timestamp DESC
        LIMIT ? OFFSET ?
    """
    rows = conn.execute(query, (now, search_param, search_param, search_param, limit, offset)).fetchall()

    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "ip": r["ip"],
            "username_tried": r["username_tried"],
            "password_masked": r["password_tried"],  # Guaranteed masked at DB write time
            "password_length": r["password_length"],
            "timestamp": r["timestamp"],
            "time_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["timestamp"])),
            "is_blocked": bool(r["is_blocked"]),
            "blocked_until": r["blocked_until"]
        })

    conn.close()

    return jsonify({
        "success": True,
        "items": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1
        }
    })


@dashboard_bp.route("/dashboard/api/system", methods=["GET"])
@admin_required
def api_system():
    """Returns system administration configuration, user accounts, model health, and DB status."""
    conn = get_db()

    # User management list (never exposing password hash or secrets)
    user_rows = conn.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at ASC").fetchall()
    users_list = [
        {
            "id": u["id"],
            "username": u["username"],
            "role": u["role"],
            "created_at": u["created_at"],
            "created_formatted": time.strftime("%Y-%m-%d %H:%M", time.localtime(u["created_at"]))
        }
        for u in user_rows
    ]

    # Database table row counts & disk size
    db_path = Config.DB_PATH
    db_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    wal_path = db_path + "-wal"
    wal_size_bytes = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0

    journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]

    table_counts = {
        "users": conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"],
        "login_attempts": conn.execute("SELECT COUNT(*) as cnt FROM login_attempts").fetchone()["cnt"],
        "blocked_ips": conn.execute("SELECT COUNT(*) as cnt FROM blocked_ips").fetchone()["cnt"],
        "block_counts": conn.execute("SELECT COUNT(*) as cnt FROM block_counts").fetchone()["cnt"],
        "honeypot_logs": conn.execute("SELECT COUNT(*) as cnt FROM honeypot_logs").fetchone()["cnt"],
        "alerts": conn.execute("SELECT COUNT(*) as cnt FROM alerts").fetchone()["cnt"],
        "vault_items": conn.execute("SELECT COUNT(*) as cnt FROM vault_items").fetchone()["cnt"],
    }
    conn.close()

    # Model metadata
    model_meta = get_model_metadata()

    # Security policies
    policies = {
        "max_failed_attempts": Config.MAX_FAILED_ATTEMPTS,
        "time_window_seconds": Config.TIME_WINDOW_SECONDS,
        "block_durations_seconds": Config.BLOCK_DURATIONS,
        "captcha_score_limit": Config.CAPTCHA_SCORE_LIMIT,
        "sliding_window_seconds": Config.SLIDING_WINDOW_SECONDS,
        "trusted_proxies": Config.TRUSTED_PROXIES
    }

    return jsonify({
        "success": True,
        "users": users_list,
        "database": {
            "path": db_path,
            "size_kb": round(db_size_bytes / 1024, 1),
            "wal_size_kb": round(wal_size_bytes / 1024, 1),
            "journal_mode": journal_mode,
            "tables": table_counts
        },
        "model": model_meta,
        "policies": policies
    })


@dashboard_bp.route("/dashboard/api/investigate/<path:ip>", methods=["GET"])
@admin_required
def api_investigate_ip(ip):
    """Deep-dive investigation for a specific IP: 6 behavioral features, ML score, attempt history."""
    now = time.time()
    conn = get_db()

    # Query login attempts for this IP
    attempts = conn.execute(
        "SELECT id, username, success, timestamp FROM login_attempts WHERE ip = ? ORDER BY timestamp DESC LIMIT 30",
        (ip,)
    ).fetchall()

    history = [
        {
            "id": r["id"],
            "username": r["username"],
            "success": bool(r["success"]),
            "timestamp": r["timestamp"],
            "time_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["timestamp"]))
        }
        for r in attempts
    ]

    # Check honeypot hits
    honey_hits = conn.execute(
        "SELECT username_tried, password_tried, timestamp FROM honeypot_logs WHERE ip = ? ORDER BY timestamp DESC LIMIT 10",
        (ip,)
    ).fetchall()
    
    honey_history = [
        {
            "username_tried": h["username_tried"],
            "password_masked": h["password_tried"],
            "timestamp": h["timestamp"],
            "time_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(h["timestamp"]))
        }
        for h in honey_hits
    ]

    # Block status
    blocked_row = conn.execute("SELECT blocked_until FROM blocked_ips WHERE ip = ?", (ip,)).fetchone()
    is_blocked = bool(blocked_row and blocked_row["blocked_until"] > now)
    blocked_until = blocked_row["blocked_until"] if blocked_row else None
    remaining_secs = max(0, int(blocked_until - now)) if is_blocked else 0

    block_count_row = conn.execute("SELECT count FROM block_counts WHERE ip = ?", (ip,)).fetchone()
    historical_block_count = block_count_row["count"] if block_count_row else 0

    conn.close()

    # Compute behavioral features & ML score
    anomaly_analysis = get_anomaly_score_for_ip(ip)

    return jsonify({
        "success": True,
        "ip": ip,
        "is_blocked": is_blocked,
        "blocked_until": blocked_until,
        "remaining_seconds": remaining_secs,
        "historical_block_count": historical_block_count,
        "analysis": anomaly_analysis,
        "attempt_history": history,
        "honeypot_history": honey_history,
        "total_recorded_attempts": len(history)
    })


@dashboard_bp.route("/dashboard/api/unblock-ip", methods=["POST"])
@admin_required
def api_unblock_ip():
    """Administrative action to manually unblock an IP address with audit trail."""
    data = request.get_json(silent=True) or request.form
    ip = data.get("ip", "").strip()

    if not ip:
        return jsonify({"error": "Missing IP parameter"}), 400

    admin_user = session.get("username", "admin")
    unblock_ip_manual(ip)
    create_alert("INFO", f"Admin '{admin_user}' manually unblocked IP {ip}")

    return jsonify({
        "success": True,
        "message": f"IP {ip} has been unblocked successfully by {admin_user}",
        "ip": ip,
        "unblocked_by": admin_user,
        "timestamp": time.time()
    })
