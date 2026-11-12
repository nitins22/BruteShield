import pytest
from bruteshield import create_app
from bruteshield.config import Config
from bruteshield.database import init_db, get_db

@pytest.fixture
def app_client(tmp_path, monkeypatch):
    test_db = str(tmp_path / "app_test.db")
    monkeypatch.setattr(Config, "DB_PATH", test_db)
    init_db(test_db)
    
    app = create_app(Config)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_login_success_and_failure(app_client):
    # Success with default user seeded in DB
    resp_ok = app_client.post("/login", data={"username": "admin", "password": "Secure@123"})
    assert resp_ok.status_code == 200
    assert b"Login successful" in resp_ok.data

    # Failure with bad password
    resp_fail = app_client.post("/login", data={"username": "admin", "password": "WrongPassword!"})
    assert resp_fail.status_code == 200
    assert b"Invalid username or password" in resp_fail.data

def test_signup_persists_user(app_client):
    # Register with a strong, non-breached password
    username = "alice_crypto"
    password = "K8#mQ9!vL2$xP5@wR7"
    
    resp = app_client.post("/signup", data={"username": username, "password": password})
    assert resp.status_code == 200
    assert b"Account Created Successfully" in resp.data

    # Verify user can log in with new credentials!
    login_resp = app_client.post("/login", data={"username": username, "password": password})
    assert login_resp.status_code == 200
    assert b"Login successful" in login_resp.data

def test_honeypot_triggers_block(app_client):
    # Post credentials to the honeypot decoy
    resp_decoy = app_client.post("/admin-login", data={"username": "root", "password": "compromised_pass"})
    assert resp_decoy.status_code == 200

    # Attempt to access standard login from the same IP should now be blocked!
    resp_login = app_client.get("/login")
    assert resp_login.status_code == 200
    assert b"Too many failed attempts" in resp_login.data

def test_vault_crud(app_client):
    # Login as admin
    app_client.post("/login", data={"username": "admin", "password": "Secure@123"})

    # Add item to vault
    add_resp = app_client.post("/vault/", data={
        "service_name": "AWS Production",
        "username": "devops_admin",
        "password": "SuperSecretCloudPass99!",
        "notes": "Prod server access"
    }, follow_redirects=True)
    assert add_resp.status_code == 200
    assert b"AWS Production" in add_resp.data

    # Decrypt item
    decrypt_resp = app_client.get("/vault/decrypt/1")
    assert decrypt_resp.status_code == 200
    data = decrypt_resp.get_json()
    assert data["success"] is True
    assert data["password"] == "SuperSecretCloudPass99!"

def test_api_password_analyze(app_client):
    resp = app_client.post("/api/password-analyze", json={"password": "TestPassword#2026"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "zxcvbn" in data
    assert "shannon_entropy" in data
    assert data["shannon_entropy"]["total_entropy"] > 40
    assert "hibp" in data
