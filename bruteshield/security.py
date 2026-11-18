import math
import hashlib
import os
import time
import base64
import requests
from collections import Counter
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from bruteshield.config import Config

# --- 1. SHANNON ENTROPY CALCULATION ---
def calculate_shannon_entropy(password: str) -> dict:
    """
    Computes Shannon Information Entropy H(X) = - sum(p(x) * log2(p(x)))
    and theoretical pool entropy L * log2(N) based on character diversity.
    """
    if not password:
        return {
            "entropy_per_char": 0.0,
            "total_entropy": 0.0,
            "pool_size": 0,
            "theoretical_entropy": 0.0,
            "rating": "None"
        }
    
    length = len(password)
    frequencies = Counter(password)
    
    # Shannon entropy: H(X) = -sum(p * log2(p))
    shannon_h = 0.0
    for count in frequencies.values():
        p = count / length
        shannon_h -= p * math.log2(p)
    
    total_entropy = shannon_h * length
    
    # Theoretical pool size calculation
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    pool_size = 0
    if has_lower: pool_size += 26
    if has_upper: pool_size += 26
    if has_digit: pool_size += 10
    if has_special: pool_size += 33  # standard printable symbols
    
    theoretical_entropy = length * math.log2(pool_size) if pool_size > 0 else 0.0

    # Categorization based on total bits of entropy
    if total_entropy < 28:
        rating = "Very Weak"
    elif total_entropy < 36:
        rating = "Weak"
    elif total_entropy < 60:
        rating = "Moderate"
    elif total_entropy < 80:
        rating = "Strong"
    else:
        rating = "Cryptographically Strong"
        
    return {
        "entropy_per_char": round(shannon_h, 3),
        "total_entropy": round(total_entropy, 2),
        "pool_size": pool_size,
        "theoretical_entropy": round(theoretical_entropy, 2),
        "rating": rating
    }

# --- 2. HAVEIBEENPWNED (HIBP) k-ANONYMITY INTEGRATION ---
def check_hibp_breached(password: str, timeout: float = 2.0) -> dict:
    """
    Checks if a password has appeared in known data breaches using the
    HaveIBeenPwned k-Anonymity API.
    
    Security: The plain password is NEVER sent over the network.
    Only the 5-character prefix of the SHA-1 hash is queried.
    """
    if not password:
        return {"is_breached": False, "breach_count": 0, "status": "empty"}
        
    # usedforsecurity=False indicates SHA-1 is used solely for the external HIBP k-Anonymity protocol
    sha1 = hashlib.sha1(password.encode("utf-8"), usedforsecurity=False).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    headers = {"User-Agent": "BruteShield-CyberSecurity-Audit/1.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            lines = response.text.splitlines()
            for line in lines:
                if ":" in line:
                    entry_suffix, count_str = line.split(":", 1)
                    if entry_suffix.strip() == suffix:
                        count = int(count_str.strip())
                        return {
                            "is_breached": True,
                            "breach_count": count,
                            "sha1_prefix": prefix,
                            "status": "breached"
                        }
            return {
                "is_breached": False,
                "breach_count": 0,
                "sha1_prefix": prefix,
                "status": "clean"
            }
        else:
            return {
                "is_breached": False,
                "breach_count": 0,
                "status": f"api_error_{response.status_code}"
            }
    except Exception as e:
        # Graceful degradation: never block application operation if offline or rate-limited
        return {
            "is_breached": False,
            "breach_count": 0,
            "status": "offline_mode",
            "message": "HIBP check skipped (network offline or rate-limited)"
        }

# --- 3. PASSWORD MASKING FOR HONEYPOT / AUDIT LOGS ---
def mask_password(password: str) -> str:
    """Masks credentials to avoid plain-text leakage in logs while retaining length context."""
    if not password:
        return "[EMPTY]"
    length = len(password)
    if length <= 2:
        return "**"
    elif length <= 5:
        return f"{password[0]}***{password[-1]}"
    else:
        return f"{password[:2]}***{password[-2:]} ({length} chars)"

# --- 4. SECURE PASSWORD VAULT ENCRYPTION (AES-256-GCM) ---
def encrypt_vault_secret(plaintext: str, key: bytes = None) -> tuple[str, str]:
    """
    Encrypts a vault credential using AES-256-GCM authenticated encryption.
    Returns (base64_ciphertext, base64_nonce).
    """
    enc_key = key or Config.VAULT_MASTER_KEY
    aesgcm = AESGCM(enc_key)
    nonce = os.urandom(12)  # 96-bit standard GCM nonce
    
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    
    b64_cipher = base64.b64encode(ciphertext).decode("utf-8")
    b64_nonce = base64.b64encode(nonce).decode("utf-8")
    return b64_cipher, b64_nonce

def decrypt_vault_secret(b64_cipher: str, b64_nonce: str, key: bytes = None) -> str:
    """
    Decrypts an AES-256-GCM encrypted credential.
    """
    enc_key = key or Config.VAULT_MASTER_KEY
    aesgcm = AESGCM(enc_key)
    
    ciphertext = base64.b64decode(b64_cipher.encode("utf-8"))
    nonce = base64.b64decode(b64_nonce.encode("utf-8"))
    
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode("utf-8")

# --- 5. SECURE CLIENT IP RESOLUTION ---
def get_client_ip(req) -> str:
    """
    Resolves client IP securely, honoring X-Forwarded-For only when the direct
    remote_addr is a trusted reverse proxy.
    """
    remote_addr = req.remote_addr or "127.0.0.1"
    
    # If the direct requester is in trusted proxies, check X-Forwarded-For
    if remote_addr in Config.TRUSTED_PROXIES:
        forwarded_for = req.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Client IP is the leftmost non-internal IP
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            for ip in ips:
                if ip and ip not in Config.TRUSTED_PROXIES:
                    return ip
        real_ip = req.headers.get("X-Real-IP")
        if real_ip and real_ip.strip():
            return real_ip.strip()
            
    return remote_addr

# --- 6. SECURE CAPTCHA GENERATOR ---
def generate_captcha_challenge() -> dict:
    """Generates an arithmetic verification challenge using cryptographically secure random integers."""
    a = secrets.randbelow(7) + 3  # 3 to 9
    b = secrets.randbelow(8) + 2  # 2 to 9
    op = secrets.choice(["+", "*", "-"])
    if op == "-":
        if a < b: a, b = b, a
        answer = a - b
    elif op == "*":
        answer = a * b
    else:
        answer = a + b
        
    return {
        "question": f"{a} {op} {b} = ?",
        "answer": str(answer),
        "timestamp": time.time()
    }
