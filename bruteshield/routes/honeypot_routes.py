from flask import Blueprint, request, render_template
from bruteshield.security import get_client_ip
from bruteshield.ml.engine import (
    log_honeypot_attempt,
    is_ip_blocked,
    block_ip,
    create_alert
)

honeypot_bp = Blueprint("honeypot", __name__)

@honeypot_bp.route("/admin-login", methods=["GET", "POST"])
def admin_honeypot():
    """
    Decoy trap endpoint. Any traffic attempting to authenticate against
    this decoy is automatically blacklisted across the entire application.
    """
    if request.method == "POST":
        ip = get_client_ip(request)
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Log attempt safely without cleartext credential leakage
        log_honeypot_attempt(ip, username, password)

        # Immediate system-wide IP quarantine
        blocked, _ = is_ip_blocked(ip)
        if not blocked:
            duration = block_ip(ip)
            create_alert("HIGH", f"IP {ip} tripped honeypot decoy at /admin-login (tried '{username}') - blocked for {duration}s")

        return render_template("login.html", message="Invalid username or password.", blocked=False)

    return render_template("login.html", message=None, blocked=False)
