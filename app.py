"""
BruteShield - Phase 1 Prototype
--------------------------------
Ek simple Flask web app jo login attempts ko log karta hai aur
threshold-based brute-force detection karta hai (fail2ban-style baseline).

Isme 3 main cheezein ho rahi hain:
1. /login route - user login try karta hai
2. Har attempt database me log hota hai (log_attempt function)
3. Agar ek IP se bahut zyada failed attempts aa jaayein, to us IP ko block kar dete hain
"""

from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import time
import os
import random
import joblib
from zxcvbn import zxcvbn

app = Flask(__name__)
app.secret_key = "bruteshield-demo-secret"   # sirf demo ke liye, real project me ye secret rakhte hain

ADMIN_USERNAME = "dashadmin"
ADMIN_PASSWORD_HASH = generate_password_hash("Dash@Admin1")

DB_PATH = "logs/bruteshield.db"
os.makedirs("logs", exist_ok=True)

# --- Fake user database (real project me ye asli DB se aayega) ---
# Password already hashed rakha hai - kabhi bhi plain text password store nahi karte
FAKE_USERS = {
    "admin": generate_password_hash("Secure@123")
}
ml_model = joblib.load("trained_model.pkl")

# --- Detection settings (ye hi tumhara "threshold rule" hai) ---
MAX_FAILED_ATTEMPTS = 5      # itne wrong attempts allowed hain
TIME_WINDOW_SECONDS = 60     # ... itne seconds ke andar
BLOCK_DURATION_SECONDS = 60  # block hone ke baad itni der wait karni hogi
BLOCK_DURATIONS = [60, 300, 900, 3600]   # 1 min, 5 min, 15 min, 1 ghanta
CAPTCHA_SCORE_LIMIT = 0.06   # score 0 se is limit ke beech ho to CAPTCHA


def get_db():
    """Database connection kholta hai. Har request pe naya connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Pehli baar app chalane pe tables bana deta hai (agar already nahi hain)."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            username TEXT NOT NULL,
            success INTEGER NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blocked_ips (
            ip TEXT PRIMARY KEY,
            blocked_until REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS honeypot_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            username_tried TEXT NOT NULL,
            password_tried TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS block_counts (
            ip TEXT PRIMARY KEY,
            count INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_attempt(ip, username, success):
    """Har login attempt ko database me save karta hai - ye humara 'Log Collector' hai."""
    conn = get_db()
    conn.execute(
        "INSERT INTO login_attempts (ip, username, success, timestamp) VALUES (?, ?, ?, ?)",
        (ip, username, int(success), time.time())
    )
    conn.commit()
    conn.close()


def is_ip_blocked(ip):
    """Check karta hai ki ye IP currently blocked hai ya nahi."""
    conn = get_db()
    row = conn.execute(
        "SELECT blocked_until FROM blocked_ips WHERE ip = ?", (ip,)
    ).fetchone()
    conn.close()
    if row and row["blocked_until"] > time.time():
        return True, row["blocked_until"]
    return False, None

# NOTE: Ye function ab live system me use nahi ho raha - ye Phase 1 ka purana
# threshold-based approach tha. Ab is_suspicious_by_ml() ye kaam karta hai (Phase 2 - ML).
# Comparison/demo ke liye rakha gaya hai.
def count_recent_failures(ip):
    """Pichle TIME_WINDOW_SECONDS me is IP ke kitne failed attempts hue, wo ginta hai."""
    conn = get_db()
    since = time.time() - TIME_WINDOW_SECONDS
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts "
        "WHERE ip = ? AND success = 0 AND timestamp > ?",
        (ip, since)
    ).fetchone()
    conn.close()
    return row["cnt"]

def get_features_for_ip(ip):
    # is IP ka pura history nikal ke, wahi 6 numbers banate hain jo features.py banata hai
    conn = get_db()
    rows = conn.execute(
        "SELECT username, success, timestamp FROM login_attempts WHERE ip = ?", (ip,)
    ).fetchall()
    conn.close()

    total_attempts = len(rows)
    failed_attempts = sum(1 for r in rows if r["success"] == 0)
    distinct_usernames = len(set(r["username"] for r in rows))

    timestamps = sorted(r["timestamp"] for r in rows)
    if len(timestamps) > 1:
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        avg_gap = sum(gaps) / len(gaps)
        min_gap = min(gaps)
    else:
        avg_gap = 0
        min_gap = 0

    failure_ratio = failed_attempts / total_attempts if total_attempts else 0

    return [[total_attempts, failed_attempts, distinct_usernames, avg_gap, min_gap, failure_ratio]]


def is_suspicious_by_ml(ip):
    features = get_features_for_ip(ip)
    prediction = ml_model.predict(features)
    return prediction[0] == -1

def needs_captcha(ip):
    features = get_features_for_ip(ip)
    if features[0][0] == 0:
        return False    # is IP ki koi history hi nahi
    score = ml_model.decision_function(features)[0]
    # score negative = block (upar wala function sambhalta hai), 0 ke paas = halka shak
    return 0 <= score < CAPTCHA_SCORE_LIMIT


def new_captcha():
    a, b = random.randint(1, 9), random.randint(1, 9)
    session["captcha_answer"] = str(a + b)
    return f"{a} + {b} = ?"

def block_ip(ip):
    conn = get_db()

    row = conn.execute("SELECT count FROM block_counts WHERE ip = ?", (ip,)).fetchone()
    previous_blocks = row["count"] if row else 0

    # jitni zyada baar pehle block hua, utna lamba is baar ka block
    duration = BLOCK_DURATIONS[min(previous_blocks, len(BLOCK_DURATIONS) - 1)]
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

def create_alert(level, message):
    conn = get_db()
    conn.execute(
        "INSERT INTO alerts (level, message, timestamp) VALUES (?, ?, ?)",
        (level, message, time.time())
    )
    conn.commit()
    conn.close()
    print(f"[ALERT-{level}] {message}")

def log_honeypot_attempt(ip, username, password):
    conn = get_db()
    conn.execute(
        "INSERT INTO honeypot_logs (ip, username_tried, password_tried, timestamp) VALUES (?, ?, ?, ?)",
        (ip, username, password, time.time())
    )
    conn.commit()
    conn.close()


@app.route("/admin-login", methods=["GET", "POST"])
def honeypot():
    if request.method == "POST":
        ip = request.remote_addr
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        log_honeypot_attempt(ip, username, password)

        # honeypot pe koi genuine user nahi aata, isliye is IP ko /login pe bhi block karo
        blocked, _ = is_ip_blocked(ip)
        if not blocked:
            block_ip(ip)
            create_alert("HIGH", f"IP {ip} tried honeypot login as '{username}' - blocked")

        return render_template("login.html", message="Invalid username or password.", blocked=False)

    return render_template("login.html", message=None, blocked=False)

@app.route("/dashboard-login", methods=["GET", "POST"])
def dashboard_login():
    ip = request.remote_addr

    blocked, until = is_ip_blocked(ip)
    if blocked:
        wait_seconds = int(until - time.time())
        return render_template("dashboard_login.html",
                               message=f"Too many failed attempts. Try again in {wait_seconds} seconds.",
                               blocked=True)

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # admin login bhi usi engine se protected hai: pehle CAPTCHA (agar halka shak ho)
        captcha_ok = True
        if needs_captcha(ip):
            captcha_ok = request.form.get("captcha", "").strip() == session.get("captcha_answer")

        password_ok = username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password)
        success = captcha_ok and password_ok

        log_attempt(ip, username, success)

        if success:
            session.pop("captcha_answer", None)
            session["is_admin"] = True
            return redirect(url_for("dashboard"))

        if is_suspicious_by_ml(ip):
            duration = block_ip(ip)
            create_alert("HIGH", f"IP {ip} blocked for {duration}s - brute-force on ADMIN login")
            return render_template("dashboard_login.html",
                                   message=f"Suspicious pattern detected by ML model. "
                                           f"Blocked for {duration} seconds.",
                                   blocked=True)

        if needs_captcha(ip):
            question = new_captcha()
            create_alert("MEDIUM", f"IP {ip} suspicious on ADMIN login - CAPTCHA challenge shown")
            if not captcha_ok:
                message = "CAPTCHA incorrect. Please try again."
            else:
                message = "Invalid admin credentials. Please solve the CAPTCHA."
            return render_template("dashboard_login.html", message=message, blocked=False,
                                   captcha_question=question)

        return render_template("dashboard_login.html", message="Invalid admin credentials.", blocked=False)

    question = new_captcha() if needs_captcha(ip) else None
    return render_template("dashboard_login.html", message=None, blocked=False, captcha_question=question)


@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("dashboard_login"))

@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("dashboard_login"))
    conn = get_db()

    total_attempts = conn.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts"
    ).fetchone()["cnt"]

    blocked_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM blocked_ips WHERE blocked_until > ?", (time.time(),)
    ).fetchone()["cnt"]

    honeypot_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM honeypot_logs"
    ).fetchone()["cnt"]

    recent_attempts = conn.execute(
        "SELECT ip, username, success FROM login_attempts ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()

    recent_honeypot = conn.execute(
        "SELECT ip, username_tried, password_tried FROM honeypot_logs ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()

    recent_alerts = [
        {"level": r["level"], "message": r["message"],
         "time": time.strftime("%d %b %H:%M:%S", time.localtime(r["timestamp"]))}
        for r in conn.execute(
            "SELECT level, message, timestamp FROM alerts ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()
    ]

    conn.close()

    return render_template("dashboard.html",
                           total_attempts=total_attempts,
                           blocked_count=blocked_count,
                           honeypot_count=honeypot_count,
                           recent_attempts=recent_attempts,
                            recent_honeypot=recent_honeypot,
                           recent_alerts=recent_alerts)

@app.route("/signup", methods=["GET", "POST"])
def check_password():
    label = None
    score = None
    suggestion = None
    accepted = False

    if request.method == "POST":
        password = request.form.get("password", "")
        analysis = zxcvbn(password)
        score = analysis["score"]

        labels = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Strong", 4: "Very Strong"}
        label = labels[score]

        suggestions = analysis["feedback"]["suggestions"]
        suggestion = " ".join(suggestions) if suggestions else "Good password!"

        # score 2 (Fair) ya usse zyada ho tabhi account accept karo
        if score >= 2:
            accepted = True

    return render_template("signup.html", label=label, score=score,
                           suggestion=suggestion, accepted=accepted)

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    ip = request.remote_addr

    blocked, until = is_ip_blocked(ip)
    if blocked:
        wait_seconds = int(until - time.time())
        return render_template("login.html",
                               message=f"Too many failed attempts. Try again in {wait_seconds} seconds.",
                               blocked=True)

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # agar is IP pe halka shak hai to pehle CAPTCHA ka jawab check karo
        captcha_ok = True
        if needs_captcha(ip):
            captcha_ok = request.form.get("captcha", "").strip() == session.get("captcha_answer")

        stored_hash = FAKE_USERS.get(username)
        password_ok = stored_hash is not None and check_password_hash(stored_hash, password)
        success = captcha_ok and password_ok

        log_attempt(ip, username, success)

        if success:
            session.pop("captcha_answer", None)
            return render_template("login.html", message="Login successful! Welcome.", blocked=False)

        # fail hua: pehle dekho ki hard block banta hai ya nahi
        if is_suspicious_by_ml(ip):
            duration = block_ip(ip)
            create_alert("HIGH", f"IP {ip} blocked for {duration}s - ML detected a brute-force pattern")
            return render_template("login.html",
                                   message=f"Suspicious pattern detected by ML model. "
                                           f"Blocked for {duration} seconds.",
                                   blocked=True)

        # block nahi, par halka shak ho to CAPTCHA dikhao
        if needs_captcha(ip):
            question = new_captcha()
            create_alert("MEDIUM", f"IP {ip} looks suspicious - CAPTCHA challenge shown")
            if not captcha_ok:
                message = "CAPTCHA incorrect. Please try again."
            else:
                message = "Invalid username or password. Please solve the CAPTCHA."
            return render_template("login.html", message=message, blocked=False,
                                   captcha_question=question)

        return render_template("login.html", message="Invalid username or password.", blocked=False)

    question = new_captcha() if needs_captcha(ip) else None
    return render_template("login.html", message=None, blocked=False, captcha_question=question)


if __name__ == "__main__":
    init_db()
    print("BruteShield Phase 1 prototype running at http://127.0.0.1:5000/login")
    print("Test credentials -> username: admin | password: Secure@123")
    app.run(debug=True, port=5000)
