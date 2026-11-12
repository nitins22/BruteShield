import pytest
from bruteshield.security import (
    calculate_shannon_entropy,
    check_hibp_breached,
    mask_password,
    encrypt_vault_secret,
    decrypt_vault_secret,
    get_client_ip
)

def test_shannon_entropy_calculation():
    # Empty string test
    res_empty = calculate_shannon_entropy("")
    assert res_empty["total_entropy"] == 0.0

    # Low entropy repeat character
    res_repeat = calculate_shannon_entropy("aaaaaaaa")
    assert res_repeat["entropy_per_char"] == 0.0
    assert res_repeat["total_entropy"] == 0.0
    assert res_repeat["rating"] == "Very Weak"

    # Diverse character password
    res_strong = calculate_shannon_entropy("C0mpl3x#P@ssw0rd!2026")
    assert res_strong["total_entropy"] > 60
    assert res_strong["pool_size"] == 26 + 26 + 10 + 33
    assert res_strong["rating"] in ["Strong", "Cryptographically Strong"]

def test_mask_password():
    assert mask_password("") == "[EMPTY]"
    assert mask_password("a") == "**"
    assert mask_password("abc") == "a***c"
    masked = mask_password("SuperSecretPassword123")
    assert "SuperSecretPassword123" not in masked
    assert masked.startswith("Su***23")
    assert "22 chars" in masked

def test_vault_encryption_decryption():
    secret = "MyUltraSecretApiKey12345!@#"
    b64_cipher, b64_nonce = encrypt_vault_secret(secret)
    assert b64_cipher != secret
    assert b64_nonce is not None

    decrypted = decrypt_vault_secret(b64_cipher, b64_nonce)
    assert decrypted == secret

def test_hibp_k_anonymity():
    # Known compromised password ("password123")
    res = check_hibp_breached("password123")
    assert res["status"] in ["breached", "offline_mode"]
    if res["status"] == "breached":
        assert res["is_breached"] is True
        assert res["breach_count"] > 1000

    # Cryptographically random password (unlikely to be breached)
    res_clean = check_hibp_breached("zQ9#mK2$vL8!xP4@wR7^")
    assert res_clean["status"] in ["clean", "offline_mode"]

def test_client_ip_resolution():
    class DummyRequest:
        def __init__(self, remote_addr, headers=None):
            self.remote_addr = remote_addr
            self.headers = headers or {}

    # Direct client connection
    req1 = DummyRequest("203.0.113.19")
    assert get_client_ip(req1) == "203.0.113.19"

    # Behind trusted proxy with X-Forwarded-For
    req2 = DummyRequest("127.0.0.1", {"X-Forwarded-For": "198.51.100.42, 127.0.0.1"})
    assert get_client_ip(req2) == "198.51.100.42"
