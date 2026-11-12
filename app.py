"""
BruteShield - Adaptive Cybersecurity Protection Platform
---------------------------------------------------------
Modular entry point with complete backward compatibility for
Phase 1/2 test scripts, simulations, and API clients.
"""

from bruteshield import create_app
from bruteshield.config import Config
from bruteshield.database import get_db, init_db
from bruteshield.security import generate_captcha_challenge
from bruteshield.ml.engine import (
    get_features_for_ip,
    is_suspicious_by_ml,
    needs_captcha,
    is_ip_blocked,
    block_ip,
    log_attempt,
    create_alert,
    log_honeypot_attempt,
    get_ml_model
)

# App instance
app = create_app()

# Backward-compatibility aliases for legacy scripts and test harnesses
ml_model = get_ml_model()
BLOCK_DURATIONS = Config.BLOCK_DURATIONS
CAPTCHA_SCORE_LIMIT = Config.CAPTCHA_SCORE_LIMIT
ADMIN_USERNAME = Config.DEFAULT_ADMIN_USER

def count_recent_failures(ip):
    """Legacy helper maintained for backward compatibility."""
    import time
    conn = get_db()
    since = time.time() - Config.TIME_WINDOW_SECONDS
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts WHERE ip = ? AND success = 0 AND timestamp > ?",
        (ip, since)
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0

def new_captcha():
    """Legacy helper maintained for backward compatibility."""
    challenge = generate_captcha_challenge()
    return challenge["question"]

# Legacy user dictionary alias (backed by real database authentication)
FAKE_USERS = {
    "admin": "Secure@123"
}

if __name__ == "__main__":
    init_db()
    print("=" * 65)
    print(" BruteShield Defense Engine - Running at http://127.0.0.1:5000")
    print(" Default Admin:   dashadmin  /  Dash@Admin1  (/dashboard-login)")
    print(" Demo User:       admin      /  Secure@123  (/login)")
    print(" Honeypot Decoy:  /admin-login (traps & blacklists attackers)")
    print(" Password Vault:  /vault (AES-256-GCM encrypted credential vault)")
    print(" Strength/Breach: /signup (zxcvbn + Shannon entropy + HIBP)")
    print("=" * 65)
    app.run(debug=True, port=5000)
