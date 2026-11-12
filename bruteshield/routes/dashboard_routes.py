import time
from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import check_password_hash
from bruteshield.database import get_db
from bruteshield.security import get_client_ip, generate_captcha_challenge
from bruteshield.ml.engine import (
    is_ip_blocked,
    needs_captcha,
    is_suspicious_by_ml,
    block_ip,
    log_attempt,
    create_alert
)

dashboard_bp = Blueprint("dashboard", __name__)

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
            session.pop("captcha_answer", None)
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
def dashboard_view():
    if not session.get("is_admin"):
        return redirect(url_for("dashboard.dashboard_login"))

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
            "level": r["level"],
            "message": r["message"],
            "time": time.strftime("%d %b %H:%M:%S", time.localtime(r["timestamp"]))
        }
        for r in conn.execute("SELECT level, message, timestamp FROM alerts ORDER BY timestamp DESC LIMIT 15").fetchall()
    ]

    conn.close()

    return render_template(
        "dashboard.html",
        total_attempts=total_attempts,
        blocked_count=blocked_count,
        honeypot_count=honeypot_count,
        user_count=user_count,
        recent_attempts=recent_attempts,
        recent_honeypot=recent_honeypot,
        recent_alerts=recent_alerts
    )
