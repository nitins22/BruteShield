import os
import re
import secrets
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from zxcvbn import zxcvbn

from bruteshield.config import Config
from bruteshield.database import get_db
from bruteshield.ml.engine import (
    block_ip,
    create_alert,
    is_ip_blocked,
    is_suspicious_by_ml,
    log_attempt,
    needs_captcha,
)
from bruteshield.security import (
    calculate_shannon_entropy,
    check_hibp_breached,
    generate_captcha_challenge,
    get_client_ip,
)

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

_login_ip_history = {}
_signup_history = {}
_forgot_history = {}


def check_ip_rate_limit(history_dict: dict, ip: str, max_limit: int, window_sec: int) -> bool:
    """Sliding-window rate limiter per client IP address."""
    now = time.time()
    cutoff = now - window_sec
    timestamps = [t for t in history_dict.get(ip, []) if t >= cutoff]
    if len(timestamps) >= max_limit:
        history_dict[ip] = timestamps
        return False
    timestamps.append(now)
    history_dict[ip] = timestamps
    return True


def send_reset_email(to_email: str, reset_url: str) -> bool:
    """Sends a password reset email if SMTP is configured."""
    if not Config.MAIL_SERVER or not Config.MAIL_USERNAME:
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = Config.MAIL_DEFAULT_SENDER
        msg["To"] = to_email
        msg["Subject"] = "BruteShield - Password Reset Request"
        body = (
            f"Hello,\n\n"
            f"A password reset was requested for your BruteShield account.\n"
            f"Click the link below to set a new password (valid for 30 minutes):\n\n"
            f"{reset_url}\n\n"
            f"If you did not request this reset, you can safely ignore this email.\n\n"
            f"— BruteShield Security Team\n"
        )
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=10) as server:
            if Config.MAIL_USE_TLS:
                server.starttls()
            if Config.MAIL_PASSWORD:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[WARN] Failed to send password reset email to {to_email}: {e}")
        return False


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

    # 2. Sliding window IP rate limit check
    if not current_app.config.get("TESTING") and not check_ip_rate_limit(
        _login_ip_history, ip, Config.LOGIN_RATE_LIMIT_MAX, Config.LOGIN_RATE_LIMIT_WINDOW
    ):
        return render_template(
            "login.html",
            message="Too many requests from your IP. Please wait before retrying.",
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

        # Verify CAPTCHA if challenge was required
        captcha_ok = True
        if needs_captcha(ip):
            user_captcha = request.form.get("captcha", "").strip()
            expected = session.get("captcha_answer")
            captcha_ok = bool(expected and user_captcha == expected)

        # Authenticate against database `users` table
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        password_ok = bool(user and check_password_hash(user["password_hash"], password))
        success = captcha_ok and password_ok

        # Telemetry logging
        log_attempt(ip, username, success)

        if success:
            session.clear()  # Session fixation defense: regenerate session state
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                session["is_admin"] = True
            return render_template("login.html", message="Login successful! Welcome.", blocked=False, authenticated=True)

        # Handle Failed Login: Anomaly Evaluation
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

        # Generic failure message to prevent account enumeration
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
        ip = get_client_ip(request)
        if not current_app.config.get("TESTING") and not check_ip_rate_limit(
            _signup_history, ip, Config.SIGNUP_RATE_LIMIT_MAX, Config.SIGNUP_RATE_LIMIT_WINDOW
        ):
            return render_template(
                "signup.html",
                label=None,
                score=None,
                suggestion=None,
                accepted=False,
                entropy_info=None,
                hibp_info=None,
                error_message="Too many registration attempts. Please try again later."
            )

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip().lower()

        if not username or not password:
            error_message = "Username and password are required."
        elif len(username) > 64:
            error_message = "Username must not exceed 64 characters."
        elif len(password) > 256:
            error_message = "Password must not exceed 256 characters."
        elif email and (len(email) > 120 or not EMAIL_REGEX.match(email)):
            error_message = "Invalid email format."
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
                existing_user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
                existing_email = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone() if email else None

                if existing_user:
                    accepted = False
                    error_message = f"Username '{username}' is already taken. Please choose another."
                    conn.close()
                elif existing_email:
                    accepted = False
                    error_message = f"Email '{email}' is already registered."
                    conn.close()
                else:
                    now = time.time()
                    conn.execute(
                        "INSERT INTO users (username, password_hash, role, created_at, email) VALUES (?, ?, ?, ?, ?)",
                        (username, generate_password_hash(password), "user", now, email or None)
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


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Generates password reset token and sends email or displays local test link."""
    ip = get_client_ip(request)
    message = None
    reset_link_dev = None

    if request.method == "POST":
        if not current_app.config.get("TESTING") and not check_ip_rate_limit(
            _forgot_history, ip, 10, 3600
        ):
            return render_template(
                "forgot_password.html",
                message="Too many password reset requests. Please try again later.",
                reset_link_dev=None
            )

        identifier = request.form.get("identifier", "").strip()
        if identifier:
            conn = get_db()
            user = conn.execute(
                "SELECT id, username, email FROM users WHERE username = ? OR email = ?",
                (identifier, identifier)
            ).fetchone()

            if user:
                token = secrets.token_urlsafe(32)
                expiry = time.time() + 1800  # 30 minutes
                conn.execute(
                    "UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE id = ?",
                    (token, expiry, user["id"])
                )
                conn.commit()

                reset_url = url_for("auth.reset_password", token=token, _external=True)
                email_sent = False
                if user["email"]:
                    email_sent = send_reset_email(user["email"], reset_url)

                if not email_sent:
                    # Provide on-screen direct link for local and cloud demo environments
                    reset_link_dev = reset_url

            conn.close()

        # Consistent confirmation message to prevent account enumeration
        message = "If an account with that username or email exists, password reset instructions have been generated."

    return render_template("forgot_password.html", message=message, reset_link_dev=reset_link_dev)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Validates reset token and allows the user to set a new password."""
    conn = get_db()
    user = conn.execute(
        "SELECT id, username, reset_token_expiry FROM users WHERE reset_token = ?",
        (token,)
    ).fetchone()

    if not user or (user["reset_token_expiry"] and user["reset_token_expiry"] < time.time()):
        conn.close()
        return render_template(
            "reset_password.html",
            invalid_token=True,
            error_message="The password reset link is invalid or has expired.",
            success=False,
            token=token
        )

    error_message = None
    success = False

    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not new_password or not confirm_password:
            error_message = "All fields are required."
        elif new_password != confirm_password:
            error_message = "Passwords do not match."
        elif len(new_password) > 256:
            error_message = "Password must not exceed 256 characters."
        else:
            analysis = zxcvbn(new_password)
            score = analysis["score"]
            hibp_info = check_hibp_breached(new_password)

            if score < 2:
                error_message = "Password is too weak. Please choose a stronger password."
            elif hibp_info.get("is_breached") and hibp_info.get("breach_count", 0) > 50:
                error_message = f"Password found in {hibp_info['breach_count']} public data breaches (HIBP). Choose a unique password."
            else:
                new_hash = generate_password_hash(new_password)
                conn.execute(
                    "UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?",
                    (new_hash, user["id"])
                )
                conn.commit()
                success = True

    conn.close()
    return render_template(
        "reset_password.html",
        invalid_token=False,
        error_message=error_message,
        success=success,
        token=token
    )


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
