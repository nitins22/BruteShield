# BruteShield — Comprehensive Test Matrix
**Execution Date:** 2026-11-18  
**Test Suite:** Automated Pytest Test Harness (`tests/`)  
**Environment:** Python 3.12.10, Pytest 9.2.0, Windows x64  
**Summary:** **50 Total Tests | 50 Passed | 0 Failed | 0 Skipped (100% Green)**

---

## 1. Test Summary by Category

| Category | Test File | Test Count | Passed | Failed | Skipped | Status |
|---|---|---|---|---|---|---|
| **Security Audit & Hardening** | `tests/test_security_audit.py` | 20 | 20 | 0 | 0 | **PASS** |
| **SOC Dashboard & Live APIs** | `tests/test_dashboard_ui.py` | 9 | 9 | 0 | 0 | **PASS** |
| **Web Routes & Authentication** | `tests/test_routes.py` | 5 | 5 | 0 | 0 | **PASS** |
| **Cryptography & Security Helpers**| `tests/test_security.py` | 5 | 5 | 0 | 0 | **PASS** |
| **ML Engine & Cooldown Ladder** | `tests/test_ml_engine.py` | 2 | 2 | 0 | 0 | **PASS** |
| **Database Architecture & WAL** | `tests/test_database.py` | 2 | 2 | 0 | 0 | **PASS** |
| **LANL Real-World Pipeline** | `tests/test_lanl_pipeline.py` | 7 | 7 | 0 | 0 | **PASS** |
| **TOTAL** | — | **50** | **50** | **0** | **0** | **100% PASS** |

---

## 2. Complete Detailed Test Inventory

### A. Security Audit & Hardening Suite (`tests/test_security_audit.py`)
1. `test_signup_input_validation`: Verifies length bounds on username (≤64) and password (≤256), and duplicate username rejection. (**PASSED**)
2. `test_session_fixation_mitigation`: Verifies `session.clear()` is called on successful login, preventing session fixation. (**PASSED**)
3. `test_logout_session_invalidation`: Verifies complete session invalidation upon user logout. (**PASSED**)
4. `test_unauthenticated_protected_routes_blocked`: Verifies unauthenticated access to `/vault/` and `/dashboard` redirects or returns 401. (**PASSED**)
5. `test_vault_idor_cross_user_isolation`: Verifies User B cannot decrypt or delete User A's vault entries. (**PASSED**)
6. `test_normal_user_cannot_access_admin_portal`: Verifies standard users cannot access the SOC dashboard or admin APIs. (**PASSED**)
7. `test_csrf_protection_when_enabled`: Verifies state-changing POST requests require valid session CSRF tokens when enabled. (**PASSED**)
8. `test_sql_injection_resistance`: Verifies SQLi payloads are parameterized safely without compromising tables, triggering ML blocks. (**PASSED**)
9. `test_xss_safe_rendering`: Verifies stored XSS payloads are safely escaped in JSON and HTML DOM rendering. (**PASSED**)
10. `test_vault_aes_gcm_tamper_detection`: Verifies bit-flipping, truncation, and wrong keys trigger `InvalidTag` in AES-256-GCM. (**PASSED**)
11. `test_vault_nonce_uniqueness`: Verifies 50 consecutive encryptions generate 50 unique 96-bit random nonces. (**PASSED**)
12. `test_vault_database_stores_no_plaintext`: Verifies canary secrets never appear in plaintext inside the database. (**PASSED**)
13. `test_production_secret_enforcement`: Verifies default secrets raise `RuntimeError` if activated in production. (**PASSED**)
14. `test_hibp_privacy_guarantee`: Verifies only the 5-character SHA-1 prefix is transmitted to HaveIBeenPwned. (**PASSED**)
15. `test_hibp_network_failure_graceful_degradation`: Verifies HIBP network errors degrade gracefully to `offline_mode`. (**PASSED**)
16. `test_honeypot_privacy_guarantee`: Verifies raw passwords submitted to `/admin-login` are masked before storage. (**PASSED**)
17. `test_security_headers_present`: Verifies CSP, X-Frame-Options, X-Content-Type-Options, and Referrer-Policy headers. (**PASSED**)
18. `test_ml_unseen_ip_returns_valid_features`: Verifies unseen IPs return a clean default 6D feature vector. (**PASSED**)
19. `test_ml_decision_score_orientation`: Verifies decision score orientation and continuous scoring alignment. (**PASSED**)
20. `test_protected_artifact_hashes`: Verifies SHA-256 integrity of `trained_model.pkl` is strictly preserved. (**PASSED**)

### B. SOC Dashboard & REST APIs Suite (`tests/test_dashboard_ui.py`)
21. `test_dashboard_login_flow`: Tests admin credentials validation and redirection to `/dashboard`. (**PASSED**)
22. `test_dashboard_access_control`: Tests role-based access control protecting dashboard views. (**PASSED**)
23. `test_dashboard_api_authentication_required`: Tests 8 dashboard APIs reject unauthenticated access with 401 Unauthorized. (**PASSED**)
24. `test_dashboard_api_overview_and_live_feed`: Tests telemetry aggregation, timeline buckets, and live stream filtering. (**PASSED**)
25. `test_dashboard_threats_and_acknowledgement`: Tests active IP quarantine listing and operator alert acknowledgement. (**PASSED**)
26. `test_dashboard_investigate_and_unblock`: Tests 6D behavioral IP deep-dive query and administrative unblock action. (**PASSED**)
27. `test_dashboard_benchmarks_strict_partitioning`: Tests strict separation between synthetic and LANL empirical benchmarks. (**PASSED**)
28. `test_dashboard_system_and_no_secret_leakage`: Tests user listing exposes zero password hashes or internal secrets. (**PASSED**)
29. `test_dashboard_honeypot_api`: Tests honeypot logs API returns masked passwords (`password_masked`), never plaintext. (**PASSED**)

### C. Web Routes & Core Authentication Suite (`tests/test_routes.py`)
30. `test_login_success_and_failure`: Tests standard login success and rejection with invalid credentials. (**PASSED**)
31. `test_signup_persists_user`: Tests user account registration with strong password and subsequent login. (**PASSED**)
32. `test_honeypot_triggers_block`: Tests posting to `/admin-login` traps and blacklists the client IP. (**PASSED**)
33. `test_vault_crud`: Tests adding, listing, decrypting, and deleting credentials in the password vault. (**PASSED**)
34. `test_api_password_analyze`: Tests JSON API for zxcvbn strength, Shannon entropy, and HIBP k-Anonymity. (**PASSED**)

### D. Cryptography & Security Helpers Suite (`tests/test_security.py`)
35. `test_shannon_entropy_calculation`: Tests mathematical Shannon entropy formula $H(X) = -\sum p(x)\log_2 p(x)$. (**PASSED**)
36. `test_mask_password`: Tests password masking preserving structural length context while concealing secret. (**PASSED**)
37. `test_vault_encryption_decryption`: Tests AES-256-GCM encryption and decryption round-trip. (**PASSED**)
38. `test_hibp_k_anonymity`: Tests mock k-Anonymity range check and breach detection counting. (**PASSED**)
39. `test_client_ip_resolution`: Tests secure client IP resolution honoring reverse proxy trust configurations. (**PASSED**)

### E. Machine Learning Engine Suite (`tests/test_ml_engine.py`)
40. `test_sliding_window_features`: Tests sliding 15-minute window extraction of the 6 behavioral anomaly dimensions. (**PASSED**)
41. `test_cooldown_escalation`: Tests adaptive escalation cooldown ladder (`60s` → `300s` → `900s` → `3600s`). (**PASSED**)

### F. Database Architecture Suite (`tests/test_database.py`)
42. `test_db_init_and_default_users`: Tests table initialization, schema integrity, and initial account seeding. (**PASSED**)
43. `test_wal_mode_enabled`: Tests SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL`) configuration. (**PASSED**)

### G. LANL Real-World Benchmark Pipeline Suite (`tests/test_lanl_pipeline.py`)
44. `test_data_quality_and_missing_value_handling`: Tests parsing and rejection of malformed Active Directory records. (**PASSED**)
45. `test_distinct_usernames_excludes_question_mark`: Tests strict exclusion of anonymous placeholder tokens (`'?'`). (**PASSED**)
46. `test_deterministic_matcher_tie_breaking`: Tests deterministic 1-to-1 matching tie-breakers on red-team records. (**PASSED**)
47. `test_hopcroft_karp_diagnostic`: Tests bipartite matching verification on red-team ground truth. (**PASSED**)
48. `test_boundary_embargo_guard`: Tests 24-hour partition boundary embargo guard isolation. (**PASSED**)
49. `test_episode_censoring_asymmetry`: Tests asymmetric left and right boundary episode censoring definitions. (**PASSED**)
50. `test_custom_fail2ban_simulation`: Tests custom Fail2ban state machine baseline on Active Directory telemetry. (**PASSED**)
