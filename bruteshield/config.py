import os
import secrets
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DEFAULT_DEMO_SECRET = "bruteshield-demo-secret-key-change-in-prod-32bytes!"  # nosec B105
DEFAULT_DEMO_VAULT = "bruteshield-vault-master-key-32b"  # nosec B105


class Config:
    BASE_DIR = BASE_DIR
    ENV = os.getenv("BRUTESHIELD_ENV", os.getenv("FLASK_ENV", "development")).lower()

    # In production, require explicit non-default secret keys
    SECRET_KEY = os.getenv("BRUTESHIELD_SECRET_KEY", DEFAULT_DEMO_SECRET)
    if ENV == "production" and (SECRET_KEY == DEFAULT_DEMO_SECRET or not SECRET_KEY):
        raise RuntimeError("CRITICAL: Production deployment requires non-default BRUTESHIELD_SECRET_KEY.")

    DB_PATH = os.getenv("BRUTESHIELD_DB_PATH", os.path.join(BASE_DIR, "logs", "bruteshield.db"))

    # Database connection URL (PostgreSQL in production, SQLite fallback in dev/test)
    raw_db_url = os.getenv("DATABASE_URL", os.getenv("BRUTESHIELD_DATABASE_URL", "")).strip()
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = raw_db_url
    DATABASE_POOL_MIN = int(os.getenv("DATABASE_POOL_MIN", "1"))
    DATABASE_POOL_MAX = int(os.getenv("DATABASE_POOL_MAX", "10"))

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

    # Reverse proxy support (Render / Cloudflare / Nginx)
    BEHIND_PROXY = os.getenv(
        "BEHIND_PROXY",
        "true" if (os.getenv("RENDER") or ENV == "production") else "false"
    ).lower() in ("true", "1", "yes")

    # Threat detection settings
    MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
    TIME_WINDOW_SECONDS = int(os.getenv("TIME_WINDOW_SECONDS", "60"))
    BLOCK_DURATIONS = [60, 300, 900, 3600]
    CAPTCHA_SCORE_LIMIT = float(os.getenv("CAPTCHA_SCORE_LIMIT", "0.06"))

    # Sliding window for feature extraction (15 minutes default)
    SLIDING_WINDOW_SECONDS = int(os.getenv("SLIDING_WINDOW_SECONDS", "900"))

    # Trusted proxies for client IP resolution
    TRUSTED_PROXIES = [ip.strip() for ip in os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1").split(",") if ip.strip()]

    # Production Admin Credentials (in production, only seeded if explicitly supplied)
    INITIAL_ADMIN_USER = os.getenv("INITIAL_ADMIN_USER", os.getenv("DEFAULT_ADMIN_USER", "dashadmin"))
    INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "")

    # Non-production default initial accounts (for test suite and local dev)
    DEFAULT_ADMIN_USER = os.getenv("DEFAULT_ADMIN_USER", "dashadmin")
    DEFAULT_ADMIN_PASS = os.getenv("DEFAULT_ADMIN_PASS", "Dash@Admin1")
    DEFAULT_DEMO_USER = os.getenv("DEFAULT_DEMO_USER", "admin")
    DEFAULT_DEMO_PASS = os.getenv("DEFAULT_DEMO_PASS", "Secure@123")

    # Rate Limiting Settings
    LOGIN_RATE_LIMIT_MAX = int(os.getenv("LOGIN_RATE_LIMIT_MAX", "20"))
    LOGIN_RATE_LIMIT_WINDOW = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW", "300"))
    SIGNUP_RATE_LIMIT_MAX = int(os.getenv("SIGNUP_RATE_LIMIT_MAX", "10"))
    SIGNUP_RATE_LIMIT_WINDOW = int(os.getenv("SIGNUP_RATE_LIMIT_WINDOW", "3600"))

    # Email / SMTP Settings (Optional, for password reset)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587")) if os.getenv("MAIL_PORT") else 587
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@bruteshield.local")
