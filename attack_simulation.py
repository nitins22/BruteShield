"""
BruteShield - Live Attack Simulation Tool
-------------------------------------------
Simulates realistic cyber attack vectors against a local BruteShield server
to demonstrate adaptive rate limiting, ML behavioral detection, and honeypot traps.

USAGE:
    python attack_simulation.py [target] [options]

TARGETS:
    login      : Fast brute force against user portal (/login) [Default]
    admin      : Credential stuffing against SOC portal (/dashboard-login)
    honeypot   : Attacker scanning decoy admin trap (/admin-login)
    spray      : Password spraying across multiple usernames

OPTIONS:
    --url <base_url> : Base URL (default: http://127.0.0.1:5000)
    --delay <sec>    : Inter-request delay in seconds (default: 0.2)
"""

import sys
import time
import re
import argparse
import requests

PASSWORDS = [
    "123456", "password", "admin", "qwerty", "letmein",
    "welcome", "admin123", "iloveyou", "abc123", "monkey",
    "dragon", "football", "sunshine", "master", "shadow",
    "12345678", "trustno1", "superman", "killer", "charlie"
]

USERNAMES = ["admin", "root", "support", "test", "manager", "operator", "guest"]

def extract_csrf_token(html_text):
    """Extract CSRF token from HTML form if present."""
    match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html_text)
    if not match:
        match = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html_text)
    return match.group(1) if match else None

def run_simulation(target_mode="login", base_url="http://127.0.0.1:5000", delay=0.2):
    session = requests.Session()
    
    if target_mode == "admin":
        target_path = "/dashboard-login"
        target_name = "SOC Dashboard Login Portal"
    elif target_mode == "honeypot":
        target_path = "/admin-login"
        target_name = "Decoy Honeypot Trap (/admin-login)"
    elif target_mode == "spray":
        target_path = "/login"
        target_name = "Password Spraying Vector (/login)"
    else:
        target_path = "/login"
        target_name = "User Login Portal (/login)"

    target_url = f"{base_url.rstrip('/')}{target_path}"

    print("=" * 70)
    print(" [!] BRUTESHIELD DEFENSE ENGINE -- LIVE ATTACK SIMULATION")
    print(f" Target Mode  : {target_mode.upper()} ({target_name})")
    print(f" Target URL   : {target_url}")
    print(f" Inter-delay  : {delay}s")
    print("=" * 70)

    # Initial GET to obtain session cookie and CSRF token
    try:
        init_resp = session.get(target_url, timeout=5)
        csrf_token = extract_csrf_token(init_resp.text)
    except requests.exceptions.RequestException as exc:
        print(f"\n[-] ERROR: Could not connect to BruteShield server at {target_url}")
        print(f"    Details: {exc}")
        print("    Ensure the BruteShield application is running (`python app.py` or `run_production.bat`).")
        return

    blocked_at = None
    captcha_at = None
    start_time = time.time()

    attempts = len(USERNAMES) if target_mode == "spray" else len(PASSWORDS)

    for i in range(1, attempts + 1):
        if target_mode == "spray":
            user = USERNAMES[(i - 1) % len(USERNAMES)]
            pwd = "Spring2026!"  # nosec B105
        else:
            user = "admin"
            pwd = PASSWORDS[i - 1]

        data = {"username": user, "password": pwd}
        if csrf_token:
            data["csrf_token"] = csrf_token

        try:
            resp = session.post(target_url, data=data, timeout=5)
            text = resp.text
            status = resp.status_code
        except requests.exceptions.RequestException as exc:
            print(f"[{i:02d}] Connection error: {exc}")
            break

        # Check for defense responses
        if "Try again in" in text or "temporarily blocked" in text.lower():
            print(f"[{i:02d}] '{user}:{pwd}' -> [BLOCKED] Active cooldown block in effect.")
            blocked_at = i
            break
        elif "Suspicious pattern detected" in text or "defense engine" in text.lower() or "Too many failed attempts" in text:
            print(f"[{i:02d}] '{user}:{pwd}' -> [TRIGGERED] ML/Threshold defense tripped! Attacker IP blocked.")
            blocked_at = i
            break
        elif "CAPTCHA" in text or "captcha" in text:
            print(f"[{i:02d}] '{user}:{pwd}' -> [CAPTCHA] Adaptive friction challenge triggered.")
            if not captcha_at:
                captcha_at = i
            # Fresh CSRF token from captcha response
            fresh_csrf = extract_csrf_token(text)
            if fresh_csrf:
                csrf_token = fresh_csrf
        elif target_mode == "honeypot" and ("Fake Admin" in text or "Invalid administrative credentials" in text or status == 200):
            print(f"[{i:02d}] '{user}:{pwd}' -> [HONEYPOT TRAPPED] Attempt logged silently in honeypot_logs.")
        elif "successful" in text.lower() or "/dashboard" in resp.url or "/vault" in resp.url:
            print(f"[{i:02d}] '{user}:{pwd}' -> [SUCCESS] Warning: Credentials succeeded!")
            break
        else:
            print(f"[{i:02d}] '{user}:{pwd}' -> [FAILED] Login failed (HTTP {status})")
            # Update CSRF token if session refreshed
            fresh_csrf = extract_csrf_token(text)
            if fresh_csrf:
                csrf_token = fresh_csrf

        time.sleep(delay)

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 70)
    print(" SIMULATION SUMMARY & DEFENSE EVALUATION")
    print("=" * 70)
    print(f" Total Attempts Sent : {min(i, attempts)}")
    print(f" Elapsed Time        : {elapsed} seconds")
    if blocked_at:
        print(f" Defense Result      : SUCCESS - Block triggered at attempt #{blocked_at}")
        print(" Escalation Status   : Escalation ladder active (IP blocked)")
    elif target_mode == "honeypot":
        print(" Defense Result      : SUCCESS - Honeypot captured attacker probes silently")
    else:
        print(" Defense Result      : Threshold not tripped (try lowering delay or increasing attempts)")

    if captcha_at:
        print(f" Friction Triggered  : CAPTCHA challenge at attempt #{captcha_at}")

    print("\n Recommended SOC Verification Steps:")
    print("   1. Open SOC Dashboard : http://127.0.0.1:5000/dashboard-login")
    print("   2. Credentials        : dashadmin / Dash@Admin1")
    print("   3. Check Live Feed    : Review real-time attempt logs & threat alerts")
    print("   4. Unblock / Reset    : Use 'Investigate' drawer to unblock test IP if desired")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BruteShield Attack Simulation Tool")
    parser.add_argument("target", nargs="?", default="login", choices=["login", "admin", "honeypot", "spray"],
                        help="Attack target vector (default: login)")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Base URL of BruteShield instance")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between attempts in seconds")
    args = parser.parse_args()

    run_simulation(args.target, args.url, args.delay)
