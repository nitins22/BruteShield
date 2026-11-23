import json
import os
import re
import secrets
import tempfile
import time
import pytest
from werkzeug.security import generate_password_hash, check_password_hash

from bruteshield import create_app
from bruteshield.config import Config
from bruteshield.database import (
    convert_placeholders,
    get_db,
    init_db,
    is_postgres_target,
    PostgresCursorWrapper,
    DummyPragmaCursor
)
from bruteshield.security import encrypt_vault_secret, decrypt_vault_secret


class CloudTestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    ENV = "development"
    SESSION_COOKIE_SECURE = False


@pytest.fixture
def cloud_app():
    """Creates a temporary test application with an isolated SQLite database."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    class CustomConfig(CloudTestConfig):
        DB_PATH = db_path
        DATABASE_URL = ""

    app = create_app(CustomConfig)
    yield app

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


@pytest.fixture
def client(cloud_app):
    return cloud_app.test_client()


# ==============================================================================
# 1. Health Check Endpoint Tests
# ==============================================================================
def test_health_check_endpoint(client):
    """Verifies that the /health endpoint returns 200 OK with database and ML status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "database_engine" in data
    assert data["model_loaded"] is True
    assert "timestamp" in data


# ==============================================================================
# 2. Database Dialect & Abstraction Tests
# ==============================================================================
def test_postgres_detection_and_placeholder_conversion():
    """Tests URL detection and ? -> %s SQL parameter translation."""
    assert is_postgres_target("postgresql://user:pass@localhost:5432/brutedb") is True
    assert is_postgres_target("postgres://user:pass@localhost:5432/brutedb") is True
    assert is_postgres_target("logs/bruteshield.db") is False
    assert is_postgres_target("") is False

    sql_in = "SELECT * FROM users WHERE username = ? AND status = 'active ?' AND age > ?"
    sql_out = convert_placeholders(sql_in)
    assert sql_out == "SELECT * FROM users WHERE username = %s AND status = 'active ?' AND age > %s"


def test_dummy_pragma_cursor():
    """Verifies that DummyPragmaCursor simulates SQLite pragmas cleanly."""
    c = DummyPragmaCursor(("PostgreSQL-WAL",))
    assert c.fetchone() == ("PostgreSQL-WAL",)
    assert c.fetchall() == [("PostgreSQL-WAL",)]


# ==============================================================================
# 3. Real User Registration with Email and Duplicate Rejection
# ==============================================================================
def test_user_registration_with_email_and_duplicates(client):
    """Verifies registration with email, unique email enforcement, and duplicate handling."""
    # 1. Register Alice with email
    res1 = client.post("/signup", data={
        "username": "alice_test",
        "password": "StrongPassword!2026",
        "email": "alice@example.com"
    }, follow_redirects=True)
    assert res1.status_code == 200
    assert b"Account Created Successfully" in res1.data

    # 2. Duplicate username rejection
    res2 = client.post("/signup", data={
        "username": "alice_test",
        "password": "StrongPassword!2026",
        "email": "other_alice@example.com"
    }, follow_redirects=True)
    assert res2.status_code == 200
    assert b"is already taken" in res2.data

    # 3. Duplicate email rejection
    res3 = client.post("/signup", data={
        "username": "alice_imposter",
        "password": "StrongPassword!2026",
        "email": "alice@example.com"
    }, follow_redirects=True)
    assert res3.status_code == 200
    assert b"already registered" in res3.data


# ==============================================================================
# 4. CRITICAL: Multi-User Vault Isolation Tests
# ==============================================================================
def test_multi_user_vault_isolation(client, cloud_app):
    """
    CRITICAL SECURITY INVARIANT:
    User A cannot view, decrypt, or delete User B's vault items.
    Enforced at database query level (WHERE user_id = ?).
    """
    with cloud_app.app_context():
        # Setup: Create Alice and Bob
        client.post("/signup", data={
            "username": "alice_vault",
            "password": "AliceStrongKey!999",
            "email": "alice_v@example.com"
        })
        client.post("/signup", data={
            "username": "bob_vault",
            "password": "BobStrongKey!999",
            "email": "bob_v@example.com"
        })

        conn = get_db()
        alice = conn.execute("SELECT id FROM users WHERE username = 'alice_vault'").fetchone()
        bob = conn.execute("SELECT id FROM users WHERE username = 'bob_vault'").fetchone()
        alice_id = alice["id"]
        bob_id = bob["id"]

        # Alice creates a vault item
        cipher_a, nonce_a = encrypt_vault_secret("AliceConfidentialSecret!")
        now = time.time()
        conn.execute("""
            INSERT INTO vault_items (user_id, service_name, username, encrypted_password, nonce, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (alice_id, "AliceBanking", "alice_acc", cipher_a, nonce_a, "Top secret bank note", now, now))
        conn.commit()

        alice_item = conn.execute("SELECT id FROM vault_items WHERE user_id = ?", (alice_id,)).fetchone()
        alice_item_id = alice_item["id"]
        conn.close()

    # 1. Bob logs in
    login_bob = client.post("/login", data={
        "username": "bob_vault",
        "password": "BobStrongKey!999"
    }, follow_redirects=True)
    assert login_bob.status_code == 200

    # 2. Bob views vault: Alice's item must NOT appear
    bob_vault_res = client.get("/vault/")
    assert bob_vault_res.status_code == 200
    assert b"AliceBanking" not in bob_vault_res.data
    assert b"Top secret bank note" not in bob_vault_res.data

    # 3. Bob attempts to decrypt Alice's vault item by ID: must fail (404/Access Denied)
    decrypt_res = client.get(f"/vault/decrypt/{alice_item_id}")
    assert decrypt_res.status_code == 404
    data = decrypt_res.get_json()
    assert "error" in data
    assert "AliceConfidentialSecret!" not in str(decrypt_res.data)

    # 4. Bob attempts to delete Alice's vault item by ID: must not delete Alice's item
    delete_res = client.post(f"/vault/delete/{alice_item_id}", follow_redirects=True)
    assert delete_res.status_code == 200

    # Verify Alice's item is STILL present in database
    conn2 = get_db(cloud_app.config["DB_PATH"])
    still_exists = conn2.execute("SELECT id FROM vault_items WHERE id = ? AND user_id = ?", (alice_item_id, alice_id)).fetchone()
    conn2.close()
    assert still_exists is not None

    # 5. Alice logs in and can successfully decrypt her item
    client.get("/logout")
    client.post("/login", data={
        "username": "alice_vault",
        "password": "AliceStrongKey!999"
    })
    alice_decrypt = client.get(f"/vault/decrypt/{alice_item_id}")
    assert alice_decrypt.status_code == 200
    alice_data = alice_decrypt.get_json()
    assert alice_data["success"] is True
    assert alice_data["password"] == "AliceConfidentialSecret!"


# ==============================================================================
# 5. Separation of Duties: Ordinary Users Cannot Access SOC Dashboard
# ==============================================================================
def test_ordinary_user_cannot_access_soc_dashboard(client):
    """Verifies that ordinary users cannot access the SOC dashboard or APIs."""
    # Register and login as ordinary user
    client.post("/signup", data={
        "username": "regular_user",
        "password": "RegularUserPass!2026"
    })
    client.post("/login", data={
        "username": "regular_user",
        "password": "RegularUserPass!2026"
    })

    # Ordinary user tries to access /dashboard
    dash_res = client.get("/dashboard", follow_redirects=False)
    # Should be redirected to /dashboard-login
    assert dash_res.status_code == 302
    assert "/dashboard-login" in dash_res.headers["Location"]

    # Ordinary user tries to access dashboard API
    api_res = client.get("/dashboard/api/overview")
    assert api_res.status_code == 401
    assert api_res.get_json()["error"] == "Unauthorized"


# ==============================================================================
# 6. Password Reset Workflow Tests
# ==============================================================================
def test_password_reset_workflow(client, cloud_app):
    """Tests the full token-based password reset workflow."""
    with cloud_app.app_context():
        # Register a test account
        client.post("/signup", data={
            "username": "reset_user",
            "password": "OldPassword!2026",
            "email": "reset@example.com"
        })

    # 1. Non-existent user forgot-password returns generic message (no enumeration)
    res_fake = client.post("/forgot-password", data={"identifier": "nonexistent_person"}, follow_redirects=True)
    assert res_fake.status_code == 200
    assert b"password reset instructions have been generated" in res_fake.data

    # 2. Existing user forgot-password
    res_real = client.post("/forgot-password", data={"identifier": "reset@example.com"}, follow_redirects=True)
    assert res_real.status_code == 200
    assert b"password reset instructions have been generated" in res_real.data

    # Retrieve generated token from database
    conn = get_db(cloud_app.config["DB_PATH"])
    user_row = conn.execute("SELECT reset_token, reset_token_expiry FROM users WHERE email = 'reset@example.com'").fetchone()
    conn.close()
    token = user_row["reset_token"]
    assert token is not None
    assert user_row["reset_token_expiry"] > time.time()

    # 3. Invalid token access returns error
    res_inv = client.get("/reset-password/totally_invalid_token")
    assert res_inv.status_code == 200
    assert b"link is invalid or has expired" in res_inv.data

    # 4. Valid token renders form
    res_form = client.get(f"/reset-password/{token}")
    assert res_form.status_code == 200
    assert b"Set New Password" in res_form.data

    # 5. Weak password rejected
    res_weak = client.post(f"/reset-password/{token}", data={
        "password": "123",
        "confirm_password": "123"
    })
    assert b"too weak" in res_weak.data

    # 6. Mismatched confirmation rejected
    res_mismatch = client.post(f"/reset-password/{token}", data={
        "password": "NewStrongPassword!2026",
        "confirm_password": "DifferentPassword!2026"
    })
    assert b"Passwords do not match" in res_mismatch.data

    # 7. Successful reset
    res_success = client.post(f"/reset-password/{token}", data={
        "password": "NewStrongPassword!2026",
        "confirm_password": "NewStrongPassword!2026"
    })
    assert b"Password Updated Successfully" in res_success.data

    # Verify reset token is wiped
    conn2 = get_db(cloud_app.config["DB_PATH"])
    updated_user = conn2.execute("SELECT reset_token FROM users WHERE email = 'reset@example.com'").fetchone()
    conn2.close()
    assert updated_user["reset_token"] is None

    # 8. User can now log in with NEW password from clean IP
    clean_env = {"REMOTE_ADDR": "10.0.0.99"}
    res_login_new = client.post("/login", data={
        "username": "reset_user",
        "password": "NewStrongPassword!2026"
    }, environ_base=clean_env, follow_redirects=True)
    assert res_login_new.status_code == 200
    assert b"Login successful" in res_login_new.data

    # 9. Old password fails
    client.get("/logout")
    res_login_old = client.post("/login", data={
        "username": "reset_user",
        "password": "OldPassword!2026"
    }, environ_base=clean_env, follow_redirects=True)
    assert b"Invalid username or password" in res_login_old.data
