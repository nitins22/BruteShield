import os
import secrets

from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DEFAULT_DEMO_SECRET = "bruteshield-demo-secret-key-change-in-prod-32bytes!"
DEFAULT_DEMO_VAULT = "bruteshield-vault-master-key-32b"

class Config:
    BASE_DIR = BASE_DIR
    ENV = os.getenv("BRUTESHIELD_ENV", os.getenv("FLASK_ENV", "development")).lower()
    
    # In production, require explicit non-default secret keys
    SECRET_KEY = os.getenv("BRUTESHIELD_SECRET_KEY", DEFAULT_DEMO_SECRET)
    if ENV == "production" and (SECRET_KEY == DEFAULT_DEMO_SECRET or not SECRET_KEY):
        raise RuntimeError("CRITICAL: Production deployment requires non-default BRUTESHIELD_SECRET_KEY.")

    DB_PATH = os.getenv("BRUTESHIELD_DB_PATH", os.path.join(BASE_DIR, "logs", "bruteshield.db"))
    MODEL_PATH = os.getenv("BRUTESHIELD_MODEL_PATH", os.path.join(BASE_DIR, "trained_model.pkl"))
    
    # 256-bit AES-GCM master key for vault item encryption
    _vault_key_raw = os.getenv("BRUTESHIELD_VAULT_KEY", DEFAULT_DEMO_VAULT)
    if ENV == "production" and (_vault_key_raw == DEFAULT_DEMO_VAULT or not _vault_key_raw):
        raise RuntimeError("CRITICAL: Production deployment requires non-default BRUTESHIELD_VAULT_KEY.")
    VAULT_MASTER_KEY = _vault_key_raw.encode("utf-8")[:32].ljust(32, b"0")

    # Session Hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (ENV == "production")
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload / payload limit (anti-DoS)

    # Threat detection settings
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
    TIME_WINDOW_SECONDS = int(os.getenv("TIME_WINDOW_SECONDS", "60"))
    BLOCK_DURATIONS = [60, 300, 900, 3600]
    CAPTCHA_SCORE_LIMIT = float(os.getenv("CAPTCHA_SCORE_LIMIT", "0.06"))
    
    # Sliding window for feature extraction (15 minutes default)
    SLIDING_WINDOW_SECONDS = int(os.getenv("SLIDING_WINDOW_SECONDS", "900"))
    
    # Trusted proxies for client IP resolution
    TRUSTED_PROXIES = [ip.strip() for ip in os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1").split(",") if ip.strip()]

    # Default initial accounts
    DEFAULT_ADMIN_USER = os.getenv("DEFAULT_ADMIN_USER", "dashadmin")
    DEFAULT_ADMIN_PASS = os.getenv("DEFAULT_ADMIN_PASS", "Dash@Admin1")
    DEFAULT_DEMO_USER = os.getenv("DEFAULT_DEMO_USER", "admin")
    DEFAULT_DEMO_PASS = os.getenv("DEFAULT_DEMO_PASS", "Secure@123")
