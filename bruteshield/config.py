import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("BRUTESHIELD_SECRET_KEY", "bruteshield-demo-secret-key-change-in-prod-32bytes!")
    DB_PATH = os.getenv("BRUTESHIELD_DB_PATH", os.path.join(BASE_DIR, "logs", "bruteshield.db"))
    MODEL_PATH = os.getenv("BRUTESHIELD_MODEL_PATH", os.path.join(BASE_DIR, "trained_model.pkl"))
    
    # 256-bit AES-GCM master key for vault item encryption
    VAULT_MASTER_KEY = os.getenv("BRUTESHIELD_VAULT_KEY", "bruteshield-vault-master-key-32b").encode("utf-8")[:32].ljust(32, b"0")

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
