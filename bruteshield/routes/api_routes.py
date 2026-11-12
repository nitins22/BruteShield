import time
from flask import Blueprint, request, jsonify
from zxcvbn import zxcvbn
from bruteshield.database import get_db
from bruteshield.security import calculate_shannon_entropy, check_hibp_breached

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/password-analyze", methods=["POST"])
def analyze_password():
    """
    JSON API for real-time client-side password entropy, zxcvbn strength scoring,
    and HIBP k-Anonymity breach audit.
    """
    data = request.get_json(silent=True) or request.form
    password = data.get("password", "")

    if not password:
        return jsonify({"error": "No password provided"}), 400

    # 1. zxcvbn score
    zx = zxcvbn(password)
    labels = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Strong", 4: "Very Strong"}
    calc_time = zx.get("calc_time", 0)
    calc_seconds = calc_time.total_seconds() if hasattr(calc_time, "total_seconds") else float(calc_time or 0)
    
    zxcvbn_result = {
        "score": zx["score"],
        "label": labels.get(zx["score"], "Unknown"),
        "guesses": zx.get("guesses", 0),
        "calc_time_seconds": round(calc_seconds, 6),
        "warning": zx["feedback"].get("warning", ""),
        "suggestions": zx["feedback"].get("suggestions", [])
    }

    # 2. Shannon information entropy
    shannon_result = calculate_shannon_entropy(password)

    # 3. HIBP breach check (k-anonymity)
    hibp_result = check_hibp_breached(password, timeout=2.0)

    return jsonify({
        "password_length": len(password),
        "zxcvbn": zxcvbn_result,
        "shannon_entropy": shannon_result,
        "hibp": hibp_result
    })


@api_bp.route("/stats", methods=["GET"])
def live_stats():
    """Returns current live security telemetry counts."""
    conn = get_db()
    total_attempts = conn.execute("SELECT COUNT(*) as cnt FROM login_attempts").fetchone()["cnt"]
    blocked_count = conn.execute("SELECT COUNT(*) as cnt FROM blocked_ips WHERE blocked_until > ?", (time.time(),)).fetchone()["cnt"]
    honeypot_count = conn.execute("SELECT COUNT(*) as cnt FROM honeypot_logs").fetchone()["cnt"]
    user_count = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
    conn.close()

    return jsonify({
        "total_attempts": total_attempts,
        "blocked_ips": blocked_count,
        "honeypot_triggers": honeypot_count,
        "registered_users": user_count,
        "timestamp": time.time()
    })
