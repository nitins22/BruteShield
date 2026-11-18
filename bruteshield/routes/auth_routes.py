import time
from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from zxcvbn import zxcvbn

from bruteshield.database import get_db
from bruteshield.security import (
    get_client_ip,
    generate_captcha_challenge,
    calculate_shannon_entropy,
    check_hibp_breached
)
from bruteshield.ml.engine import (
    is_ip_blocked,
    needs_captcha,
    is_suspicious_by_ml,
    block_ip,
    log_attempt,
    create_alert
)

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET"])
def home():
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    ip = get_client_ip(request)
    
    # 1. Check if IP is currently blocked
    blocked, until = is_ip_blocked(ip)
    if blocked:
        wait_seconds = max(1, int(until - time.time()))
        return render_template(
            "login.html",
            message=f"Too many failed attempts. Try again in {wait_seconds} seconds.",
            blocked=True
        )

    captcha_question = None
    if needs_captcha(ip):
        challenge = generate_captcha_challenge()
        session["captcha_answer"] = challenge["answer"]
        captcha_question = challenge["question"]

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Input length validation
        if len(username) > 64 or len(password) > 256:
            return render_template("login.html", message="Invalid username or password format.", blocked=False)
        
        # 2. Verify CAPTCHA if challenge was required
        captcha_ok = True
        if needs_captcha(ip):
            user_captcha = request.form.get("captcha", "").strip()
            expected = session.get("captcha_answer")
            captcha_ok = bool(expected and user_captcha == expected)
            
        # 3. Authenticate against database `users` table
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        password_ok = bool(user and check_password_hash(user["password_hash"], password))
        success = captcha_ok and password_ok

        # 4. Telemetry logging
        log_attempt(ip, username, success)

        if success:
            session.clear()  # Session fixation defense: regenerate session state
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                session["is_admin"] = True
            return render_template("login.html", message="Login successful! Welcome.", blocked=False, authenticated=True)

        # 5. Handle Failed Login: Anomaly Evaluation
        if is_suspicious_by_ml(ip):
            duration = block_ip(ip)
            create_alert("HIGH", f"IP {ip} blocked for {duration}s - ML detected brute-force attack pattern")
            return render_template(
                "login.html",
                message=f"Suspicious pattern detected by ML model. Blocked for {duration} seconds.",
                blocked=True
            )

        if needs_captcha(ip):
            challenge = generate_captcha_challenge()
            session["captcha_answer"] = challenge["answer"]
            create_alert("MEDIUM", f"IP {ip} suspicious pattern - CAPTCHA challenge presented")
            
            if not captcha_ok:
                msg = "CAPTCHA verification incorrect. Please solve the challenge."
            else:
                msg = "Invalid credentials. Please solve the CAPTCHA."
            return render_template("login.html", message=msg, blocked=False, captcha_question=challenge["question"])

        return render_template("login.html", message="Invalid username or password.", blocked=False)

    return render_template("login.html", message=None, blocked=False, captcha_question=captcha_question)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    label = None
    score = None
    suggestion = None
    accepted = False
    entropy_info = None
    hibp_info = None
    error_message = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error_message = "Username and password are required."
        elif len(username) > 64:
            error_message = "Username must not exceed 64 characters."
        elif len(password) > 256:
            error_message = "Password must not exceed 256 characters."
        else:
            # 1. zxcvbn evaluation
            analysis = zxcvbn(password)
            score = analysis["score"]
            labels = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Strong", 4: "Very Strong"}
            label = labels.get(score, "Unknown")
            suggestions = analysis["feedback"]["suggestions"]
            suggestion = " ".join(suggestions) if suggestions else "Password complexity is acceptable."

            # 2. Shannon entropy computation
            entropy_info = calculate_shannon_entropy(password)

            # 3. HaveIBeenPwned k-Anonymity breach lookup
            hibp_info = check_hibp_breached(password)

            # Policy: zxcvbn score >= 2 AND not severely breached in HIBP (> 50 occurrences)
            if score < 2:
                accepted = False
                error_message = "Password too weak. Please choose a stronger password."
            elif hibp_info.get("is_breached") and hibp_info.get("breach_count", 0) > 50:
                accepted = False
                error_message = f"Critical Security Warning: This password was found in {hibp_info['breach_count']} public data breaches (HIBP). Choose a unique password."
            else:
                # 4. Persist user into database
                conn = get_db()
                existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
                if existing:
                    accepted = False
                    error_message = f"Username '{username}' is already taken. Please choose another."
                    conn.close()
                else:
                    now = time.time()
                    conn.execute(
                        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                        (username, generate_password_hash(password), "user", now)
                    )
                    conn.commit()
                    conn.close()
                    accepted = True

    return render_template(
        "signup.html",
        label=label,
        score=score,
        suggestion=suggestion,
        accepted=accepted,
        entropy_info=entropy_info,
        hibp_info=hibp_info,
        error_message=error_message
    )


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
