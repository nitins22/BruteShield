import time
import pytest
from bruteshield import create_app
from bruteshield.config import Config
from bruteshield.database import init_db, get_db
from bruteshield.ml.engine import block_ip, log_attempt, create_alert, log_honeypot_attempt

@pytest.fixture
def app_client(tmp_path, monkeypatch):
    test_db = str(tmp_path / "dashboard_test.db")
    monkeypatch.setattr(Config, "DB_PATH", test_db)
    init_db(test_db)
    
    app = create_app(Config)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_dashboard_login_flow(app_client):
    # 1. Invalid credentials
    resp_fail = app_client.post("/dashboard-login", data={"username": "dashadmin", "password": "WrongPassword"})
    assert resp_fail.status_code == 200
    assert b"Invalid admin credentials" in resp_fail.data

    # 2. Valid credentials
    resp_ok = app_client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    }, follow_redirects=False)
    assert resp_ok.status_code == 302
    assert "/dashboard" in resp_ok.headers["Location"]

def test_dashboard_access_control(app_client):
    # Unauthenticated access redirects to login
    resp_anon = app_client.get("/dashboard")
    assert resp_anon.status_code == 302
    assert "/dashboard-login" in resp_anon.headers["Location"]

    # Normal user role cannot access admin dashboard
    app_client.post("/login", data={"username": "admin", "password": "Secure@123"})
    resp_user = app_client.get("/dashboard")
    assert resp_user.status_code == 302
    assert "/dashboard-login" in resp_user.headers["Location"]

    # Authenticated admin access succeeds
    app_client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    })
    resp_admin = app_client.get("/dashboard")
    assert resp_admin.status_code == 200
    assert b"BruteShield" in resp_admin.data
    assert b"Security Overview" in resp_admin.data

def test_dashboard_api_authentication_required(app_client):
    endpoints = [
        "/dashboard/api/overview",
        "/dashboard/api/live-feed",
        "/dashboard/api/threats",
        "/dashboard/api/analytics",
        "/dashboard/api/benchmarks",
        "/dashboard/api/honeypot",
        "/dashboard/api/system",
        "/dashboard/api/investigate/192.168.1.50"
    ]
    for ep in endpoints:
        res = app_client.get(ep)
        assert res.status_code == 401
        data = res.get_json()
        assert data["error"] == "Unauthorized"

def test_dashboard_api_overview_and_live_feed(app_client):
    # Log some attempts first
    log_attempt("10.0.0.1", "alice", True)
    log_attempt("10.0.0.2", "bob", False)
    log_attempt("10.0.0.2", "charlie", False)

    # Login as admin
    app_client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    })

    # Test Overview API
    res_ov = app_client.get("/dashboard/api/overview")
    assert res_ov.status_code == 200
    data_ov = res_ov.get_json()
    assert data_ov["success"] is True
    assert data_ov["metrics"]["total_attempts"] >= 3
    assert data_ov["metrics"]["failed_attempts"] >= 2
    assert "timeline" in data_ov
    assert len(data_ov["timeline"]["labels"]) == 12

    # Test Live Feed API
    res_feed = app_client.get("/dashboard/api/live-feed?limit=10&page=1")
    assert res_feed.status_code == 200
    data_feed = res_feed.get_json()
    assert data_feed["success"] is True
    assert len(data_feed["items"]) >= 3
    assert data_feed["pagination"]["total"] >= 3

    # Test Live Feed Filtering
    res_failed = app_client.get("/dashboard/api/live-feed?filter=failed")
    assert res_failed.status_code == 200
    for item in res_failed.get_json()["items"]:
        assert item["success"] is False

def test_dashboard_threats_and_acknowledgement(app_client):
    # Create an alert and block an IP
    block_ip("192.168.100.99")
    create_alert("HIGH", "Automated threat detection test alert")

    # Login as admin
    app_client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    })

    # Check Threats API
    res_thr = app_client.get("/dashboard/api/threats")
    assert res_thr.status_code == 200
    data_thr = res_thr.get_json()
    assert data_thr["success"] is True
    assert any(b["ip"] == "192.168.100.99" for b in data_thr["active_blocks"])
    assert any("Automated threat detection test alert" in a["message"] for a in data_thr["alerts"])

    # Acknowledge the alert
    alert_id = data_thr["alerts"][0]["id"]
    res_ack = app_client.post(f"/dashboard/api/threats/acknowledge/{alert_id}")
    assert res_ack.status_code == 200
    assert res_ack.get_json()["success"] is True

    # Re-verify alert shows acknowledged
    res_thr2 = app_client.get("/dashboard/api/threats")
    alert_updated = [a for a in res_thr2.get_json()["alerts"] if a["id"] == alert_id][0]
    assert alert_updated["is_acknowledged"] is True
    assert alert_updated["acknowledged_by"] == Config.DEFAULT_ADMIN_USER

def test_dashboard_investigate_and_unblock(app_client):
    test_ip = "172.16.0.45"
    log_attempt(test_ip, "root", False)
    log_attempt(test_ip, "admin", False)
    block_ip(test_ip)

    # Login as admin
    app_client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    })

    # Investigate IP
    res_inv = app_client.get(f"/dashboard/api/investigate/{test_ip}")
    assert res_inv.status_code == 200
    data_inv = res_inv.get_json()
    assert data_inv["success"] is True
    assert data_inv["ip"] == test_ip
    assert data_inv["is_blocked"] is True
    assert "features" in data_inv["analysis"]
    assert data_inv["analysis"]["features"]["total_attempts"] == 2
    assert data_inv["analysis"]["features"]["failed_attempts"] == 2
    assert data_inv["analysis"]["features"]["distinct_usernames"] == 2

    # Unblock IP
    res_unblock = app_client.post("/dashboard/api/unblock-ip", json={"ip": test_ip})
    assert res_unblock.status_code == 200
    assert res_unblock.get_json()["success"] is True

    # Confirm unblocked
    res_inv2 = app_client.get(f"/dashboard/api/investigate/{test_ip}")
    assert res_inv2.get_json()["is_blocked"] is False

def test_dashboard_benchmarks_strict_partitioning(app_client):
    app_client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    })

    res = app_client.get("/dashboard/api/benchmarks")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "synthetic" in data["data"]
    assert "lanl" in data["data"]

    # Verify Synthetic baseline counts
    synth = data["data"]["synthetic"]
    assert synth["sample_counts"]["normal_ips"] == 300
    assert synth["sample_counts"]["attacker_ips"] == 190
    assert synth["metrics_comparison"]["accuracy"]["ml"] == 0.965

    # Verify LANL Empirical Benchmark
    lanl = data["data"]["lanl"]
    assert lanl["ingestion_audit"]["retained_auth_events"] == 21255459
    assert lanl["redteam_audit"]["exact_matches_in_slice"] == 10
    assert "Days 0 to 2.31 Empirical Slice" in lanl["coverage_disclosure"]

def test_dashboard_system_and_no_secret_leakage(app_client):
    app_client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    })

    res = app_client.get("/dashboard/api/system")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "users" in data
    assert len(data["users"]) >= 2

    # Ensure no sensitive hash or token leakage!
    for user in data["users"]:
        assert "password_hash" not in user
        assert "password" not in user
        assert "secret" not in user

def test_dashboard_honeypot_api(app_client):
    # Log honeypot hit
    log_honeypot_attempt("198.51.100.12", "superadmin", "AttackerPlaintextPassword123!")

    # Login as admin
    app_client.post("/dashboard-login", data={
        "username": Config.DEFAULT_ADMIN_USER,
        "password": Config.DEFAULT_ADMIN_PASS
    })

    res = app_client.get("/dashboard/api/honeypot")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["items"]) >= 1
    
    hit = [h for h in data["items"] if h["ip"] == "198.51.100.12"][0]
    assert hit["username_tried"] == "superadmin"
    # Guaranteed never raw plaintext!
    assert "AttackerPlaintextPassword123!" not in hit["password_masked"]
    assert "***" in hit["password_masked"]
