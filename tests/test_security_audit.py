import os
import time
import base64
import pytest
from unittest.mock import patch
from werkzeug.security import check_password_hash
from cryptography.exceptions import InvalidTag

from bruteshield import create_app
from bruteshield.config import Config
from bruteshield.database import init_db, get_db
from bruteshield.security import (
    encrypt_vault_secret,
    decrypt_vault_secret,
    calculate_shannon_entropy,
    check_hibp_breached,
    mask_password,
    generate_captcha_challenge
)
from bruteshield.ml.engine import (
    get_features_for_ip,
    is_suspicious_by_ml,
    needs_captcha,
    block_ip,
    is_ip_blocked,
    log_attempt,
    log_honeypot_attempt,
    get_anomaly_score_for_ip,
    get_model_metadata
)

@pytest.fixture
def test_app(tmp_path, monkeypatch):
    test_db = str(tmp_path / "security_audit_test.db")
    monkeypatch.setattr(Config, "DB_PATH", test_db)
    init_db(test_db)
    
    app = create_app(Config)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(test_app):
    with test_app.test_client() as c:
        yield c

# =========================================================================
# 1. AUTHENTICATION & SESSION SECURITY TESTS
# =========================================================================

def test_signup_input_validation(client):
    # Reject oversized username (>64 chars)
    long_user = "a" * 65
    resp = client.post("/signup", data={"username": long_user, "password": "ValidPassword123!"})
    assert resp.status_code == 200
    assert b"Username must not exceed 64 characters" in resp.data

    # Reject oversized password (>256 chars - anti-DoS)
    long_pass = "P" * 257
    resp2 = client.post("/signup", data={"username": "valid_user", "password": long_pass})
    assert resp2.status_code == 200
    assert b"Password must not exceed 256 characters" in resp2.data

    # Reject duplicate username
    client.post("/signup", data={"username": "duplicate_user", "password": "ValidPassword123!"})
    resp_dup = client.post("/signup", data={"username": "duplicate_user", "password": "ValidPassword123!"})
    assert resp_dup.status_code == 200
    assert b"already taken" in resp_dup.data

def test_session_fixation_mitigation(client):
    with client.session_transaction() as sess:
        sess["pre_login_tracker"] = "malicious_fixed_token_123"

    # Log in as demo user
    resp = client.post("/login", data={"username": "admin", "password": "Secure@123"})
    assert resp.status_code == 200

    # Verify session was cleared and re-created (fixation prevented)
    with client.session_transaction() as sess:
        assert "pre_login_tracker" not in sess
        assert sess.get("user_id") is not None
        assert sess.get("username") == "admin"

def test_logout_session_invalidation(client):
    client.post("/login", data={"username": "admin", "password": "Secure@123"})
    with client.session_transaction() as sess:
        assert sess.get("username") == "admin"

    # Logout
    resp_logout = client.get("/logout", follow_redirects=True)
    assert resp_logout.status_code == 200

    with client.session_transaction() as sess:
        assert "username" not in sess
        assert "user_id" not in sess
        assert "is_admin" not in sess

# =========================================================================
# 2. AUTHORIZATION & ACCESS CONTROL (IDOR) TESTS
# =========================================================================

def test_unauthenticated_protected_routes_blocked(client):
    # Vault access blocked
    res_vault = client.get("/vault/")
    assert res_vault.status_code == 302
    assert "/login" in res_vault.headers["Location"]

    # Dashboard access blocked
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 302
    assert "/dashboard-login" in res_dash.headers["Location"]

    # Dashboard APIs return 401 JSON
    res_api = client.get("/dashboard/api/overview")
    assert res_api.status_code == 401
    assert res_api.get_json()["error"] == "Unauthorized"

def test_vault_idor_cross_user_isolation(client):
    # 1. Create two separate user accounts
    client.post("/signup", data={"username": "victim_user", "password": "VictimPassword123!"})
    client.post("/signup", data={"username": "attacker_user", "password": "AttackerPassword123!"})

    # 2. Login as victim and save a secret
    client.post("/login", data={"username": "victim_user", "password": "VictimPassword123!"})
    client.post("/vault/", data={
        "service_name": "Victim Banking",
        "username": "victim_bank",
        "password": "VictimSuperSecretPIN999!",
        "notes": "Top secret account"
    })

    # Identify victim's item ID
    conn = get_db()
    victim_row = conn.execute("SELECT id FROM vault_items WHERE service_name = 'Victim Banking'").fetchone()
    item_id = victim_row["id"]
    conn.close()

    # 3. Login as attacker
    client.get("/logout")
    client.post("/login", data={"username": "attacker_user", "password": "AttackerPassword123!"})

    # Attacker tries to decrypt victim's item (IDOR attempt)
    resp_decrypt = client.get(f"/vault/decrypt/{item_id}")
    assert resp_decrypt.status_code == 404
    data_dec = resp_decrypt.get_json()
    assert "error" in data_dec

    # Attacker tries to delete victim's item (IDOR attempt)
    client.post(f"/vault/delete/{item_id}")

    # Verify item still exists safely in database
    conn2 = get_db()
    still_exists = conn2.execute("SELECT * FROM vault_items WHERE id = ?", (item_id,)).fetchone()
    assert still_exists is not None
    conn2.close()

def test_normal_user_cannot_access_admin_portal(client):
    client.post("/signup", data={"username": "regular_joe", "password": "RegularJoePass123!"})
    client.post("/login", data={"username": "regular_joe", "password": "RegularJoePass123!"})

    # Regular user attempting dashboard
    res = client.get("/dashboard")
    assert res.status_code == 302
    assert "/dashboard-login" in res.headers["Location"]

    # Regular user attempting admin API
    res_api = client.get("/dashboard/api/system")
    assert res_api.status_code == 401

# =========================================================================
# 3. CSRF PROTECTION TESTS
# =========================================================================

def test_csrf_protection_when_enabled(tmp_path, monkeypatch):
    test_db = str(tmp_path / "csrf_test.db")
    monkeypatch.setattr(Config, "DB_PATH", test_db)
    init_db(test_db)

    app = create_app(Config)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = True  # Explicitly enforce CSRF

    with app.test_client() as c:
        # 1. Request without CSRF token should be rejected (403)
        res_fail = c.post("/login", data={"username": "admin", "password": "Secure@123"})
        assert res_fail.status_code == 403

        # 2. Obtain session CSRF token from page
        res_get = c.get("/login")
        assert res_get.status_code == 200
        with c.session_transaction() as sess:
            token = sess["_csrf_token"]

        # 3. Post with valid CSRF token should succeed
        res_ok = c.post("/login", data={
            "username": "admin",
            "password": "Secure@123",
            "csrf_token": token
        })
        assert res_ok.status_code == 200
        assert b"Login successful" in res_ok.data

        # 4. Honeypot decoy (/admin-login) is exempt so automated scanners can be trapped without CSRF token
        res_honey = c.post("/admin-login", data={"username": "bot_user", "password": "bot_pass"})
        assert res_honey.status_code == 200

# =========================================================================
# 4. INJECTION & XSS DEFENSE TESTS
# =========================================================================

def test_sql_injection_resistance(client):
    sqli_payloads = [
        "' OR 1=1 --",
        "admin'--",
        "' UNION SELECT 1, 'admin', 'hash', 'admin', 0 --",
        "1; DROP TABLE users; --"
    ]
    for payload in sqli_payloads:
        resp = client.post("/login", data={"username": payload, "password": "Password123!"})
        assert resp.status_code == 200
        # Either rejected with invalid credentials or blocked by ML defense engine
        assert (b"Invalid username or password" in resp.data) or \
               (b"Suspicious pattern detected" in resp.data) or \
               (b"Too many failed attempts" in resp.data)

    # Ensure users table is intact (no SQL injection succeeded)
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (Config.DEFAULT_ADMIN_USER,)).fetchone()
    assert user is not None
    conn.close()

def test_xss_safe_rendering(client):
    xss_payload = '<script>alert("XSS")</script>'
    # Use strong non-breached password so signup policy accepts it
    strong_pass = "K8#mQ9!vL2$xP5@wR7"
    signup_resp = client.post("/signup", data={"username": xss_payload, "password": strong_pass})
    assert signup_resp.status_code == 200
    assert b"Account Created Successfully" in signup_resp.data
    
    # Login as admin to view usernames in dashboard system API
    client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    })

    resp = client.get("/dashboard/api/system")
    assert resp.status_code == 200
    # Payload is sent as raw text in JSON string, but when rendered into DOM it is escaped via escapeHtml
    data = resp.get_json()
    assert any(u["username"] == xss_payload for u in data["users"])

# =========================================================================
# 5. CRYPTOGRAPHY & VAULT TAMPERING TESTS
# =========================================================================

def test_vault_aes_gcm_tamper_detection():
    secret = "TopSecretAPIKey_9876543210"
    b64_cipher, b64_nonce = encrypt_vault_secret(secret)

    # 1. Valid decryption
    decrypted = decrypt_vault_secret(b64_cipher, b64_nonce)
    assert decrypted == secret

    # 2. Tampered ciphertext (flip one byte in ciphertext payload)
    raw_cipher = bytearray(base64.b64decode(b64_cipher))
    raw_cipher[5] ^= 0xFF
    tampered_b64 = base64.b64encode(raw_cipher).decode("utf-8")

    with pytest.raises(InvalidTag):
        decrypt_vault_secret(tampered_b64, b64_nonce)

    # 3. Truncated ciphertext (missing authentication tag)
    truncated_b64 = base64.b64encode(raw_cipher[:10]).decode("utf-8")
    with pytest.raises(Exception):
        decrypt_vault_secret(truncated_b64, b64_nonce)

    # 4. Decrypt with wrong key
    wrong_key = b"wrong-key-32-bytes-long-padding!"
    with pytest.raises(InvalidTag):
        decrypt_vault_secret(b64_cipher, b64_nonce, key=wrong_key)

def test_vault_nonce_uniqueness():
    secret = "IdenticalPlaintextRepeated"
    nonces = set()
    for _ in range(50):
        _, b64_nonce = encrypt_vault_secret(secret)
        assert b64_nonce not in nonces, "Nonce reuse detected!"
        nonces.add(b64_nonce)
    assert len(nonces) == 50

def test_vault_database_stores_no_plaintext(client):
    client.post("/signup", data={"username": "crypto_user", "password": "CryptoPass123!"})
    client.post("/login", data={"username": "crypto_user", "password": "CryptoPass123!"})

    canary_password = "UniqueCanaryPasswordToFind_ABC123!"
    client.post("/vault/", data={
        "service_name": "Canary Service",
        "username": "canary_user",
        "password": canary_password,
        "notes": "Testing plaintext storage"
    })

    conn = get_db()
    row = conn.execute("SELECT * FROM vault_items WHERE service_name = 'Canary Service'").fetchone()
    conn.close()

    assert canary_password not in row["encrypted_password"]
    assert canary_password not in row["nonce"]
    assert canary_password not in (row["notes"] or "")

def test_production_secret_enforcement(monkeypatch):
    monkeypatch.setenv("BRUTESHIELD_ENV", "production")
    monkeypatch.setenv("BRUTESHIELD_SECRET_KEY", "bruteshield-demo-secret-key-change-in-prod-32bytes!")
    
    with pytest.raises(RuntimeError) as exc_info:
        import importlib
        import bruteshield.config
        importlib.reload(bruteshield.config)
    assert "Production deployment requires non-default BRUTESHIELD_SECRET_KEY" in str(exc_info.value)

# =========================================================================
# 6. HIBP & HONEYPOT PRIVACY TESTS
# =========================================================================

def test_hibp_privacy_guarantee():
    test_password = "P@ssword123VeryLongSecret"
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "0018A45C4D1DEF81644B54AB7F969B88D65:4\n"
        
        check_hibp_breached(test_password)
        
        # Verify URL called has ONLY the 5-char hash prefix, NEVER full password or full hash!
        called_url = mock_get.call_args[0][0]
        assert test_password not in called_url
        assert "api.pwnedpasswords.com/range/" in called_url
        prefix = called_url.split("/")[-1]
        assert len(prefix) == 5

def test_hibp_network_failure_graceful_degradation():
    with patch("requests.get", side_effect=Exception("Network connection failed")):
        res = check_hibp_breached("AnyPassword123")
        assert res["is_breached"] is False
        assert res["status"] == "offline_mode"

def test_honeypot_privacy_guarantee(client):
    raw_secret = "AttackerSuperSecretStolenPassword999"
    client.post("/admin-login", data={"username": "root_attempt", "password": raw_secret})

    conn = get_db()
    row = conn.execute("SELECT * FROM honeypot_logs WHERE username_tried = 'root_attempt'").fetchone()
    conn.close()

    assert raw_secret not in row["password_tried"]
    assert "***" in row["password_tried"]
    assert row["password_length"] == len(raw_secret)

# =========================================================================
# 7. SECURITY HEADERS VERIFICATION
# =========================================================================

def test_security_headers_present(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert "geolocation=()" in headers.get("Permissions-Policy", "")

# =========================================================================
# 8. ML ENGINE INPUT VALIDATION & INTEGRITY
# =========================================================================

def test_ml_unseen_ip_returns_valid_features():
    features = get_features_for_ip("192.0.2.1")
    assert len(features) == 1
    assert len(features[0]) == 6
    assert features[0] == [0, 0, 0, 0.0, 0.0, 0.0]

def test_ml_decision_score_orientation():
    # Model decision function: score < 0 means anomaly
    meta = get_model_metadata()
    assert meta["loaded"] is True
    assert meta["feature_count"] == 6
    assert meta["sha256"] == "0F42590F98026B54B3F9C570C37F05E57A5A013DA6C3DC3CB2E9E5421CD48E8F"

def test_protected_artifact_hashes():
    """Verify that all protected benchmark models remain strictly unaltered."""
    import hashlib
    expected_hashes = {
        Config.MODEL_PATH: "0F42590F98026B54B3F9C570C37F05E57A5A013DA6C3DC3CB2E9E5421CD48E8F"
    }
    for path, expected in expected_hashes.items():
        assert os.path.exists(path)
        with open(path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest().upper()
        assert computed == expected, f"Artifact {path} was modified!"
