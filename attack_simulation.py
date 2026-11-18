"""
BruteShield — Safe Attack Simulation Tool
============================================
Controlled, bounded, local-only demonstration and testing of BruteShield's
defensive controls.  Designed for authorized faculty demonstrations and
developer testing on localhost.

SAFETY RESTRICTIONS:
  - Default target is 127.0.0.1 — public IPs and external domains are rejected.
  - Maximum request count is bounded (default 20, hard cap 50).
  - Configurable inter-request delay (default 0.3s, minimum 0.1s).
  - Uses only disposable demonstration passwords (never real credential lists).
  - Interacts with legitimate application flows including CSRF.
  - Never stores session tokens or CSRF tokens in output/logs.
  - Provides a --dry-run mode that shows what WOULD be sent.

USAGE:
    python attack_simulation.py login               # Fast brute force on /login
    python attack_simulation.py admin               # Credential stuffing on /dashboard-login
    python attack_simulation.py honeypot             # Scanner probes on /admin-login
    python attack_simulation.py spray               # Password spraying on /login
    python attack_simulation.py login --dry-run      # Preview without sending
    python attack_simulation.py --help               # Full option listing
"""

import sys
import time
import re
import argparse
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Demonstration password and username lists (synthetic, non-sensitive)
# ---------------------------------------------------------------------------
DEMO_PASSWORDS = [
    "123456", "password", "admin", "qwerty", "letmein",
    "welcome", "admin123", "iloveyou", "abc123", "monkey",
    "dragon", "football", "sunshine", "master", "shadow",
    "12345678", "trustno1", "superman", "killer", "charlie",
]

SPRAY_USERNAMES = [
    "testuser1", "testuser2", "testuser3", "testuser4",
    "testuser5", "testuser6", "testuser7",
]

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_csrf(html: str) -> str | None:
    """Extract the CSRF token from an HTML response body."""
    m = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html)
    if not m:
        m = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html)
    return m.group(1) if m else None


def _is_safe_target(url: str) -> bool:
    """Return True only when the URL resolves to a local address."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return hostname in ALLOWED_HOSTS


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def run_simulation(
    target_mode: str,
    base_url: str,
    delay: float,
    max_attempts: int,
    dry_run: bool,
) -> int:
    """Execute a bounded attack simulation.  Returns 0 on success, 1 on error."""

    # --- Safety gate ---
    if not _is_safe_target(base_url):
        print(
            f"[BLOCKED] Target host '{urlparse(base_url).hostname}' is not a "
            f"permitted local address.\n"
            f"  Allowed hosts: {', '.join(sorted(ALLOWED_HOSTS))}\n"
            f"  This tool must ONLY target a local BruteShield instance.",
            file=sys.stderr,
        )
        return 1

    # Resolve target path
    paths = {
        "login":    ("/login",           "User Login Portal"),
        "admin":    ("/dashboard-login", "SOC Dashboard Login"),
        "honeypot": ("/admin-login",     "Decoy Honeypot Trap"),
        "spray":    ("/login",           "Password Spraying"),
    }
    target_path, target_name = paths[target_mode]
    target_url = f"{base_url.rstrip('/')}{target_path}"

    # Determine attempt list
    if target_mode == "spray":
        attempt_list = [(u, "DemoSpray2026!") for u in SPRAY_USERNAMES]  # nosec B105
    else:
        attempt_list = [("admin", p) for p in DEMO_PASSWORDS]
    attempt_list = attempt_list[:max_attempts]

    # Header
    print("=" * 70)
    print(" BruteShield — Attack Simulation Tool")
    print(f" Mode         : {target_mode.upper()} — {target_name}")
    print(f" Target       : {target_url}")
    print(f" Max Attempts : {len(attempt_list)}")
    print(f" Delay        : {delay}s")
    print(f" Dry Run      : {'YES (no requests will be sent)' if dry_run else 'No'}")
    print("=" * 70)

    if dry_run:
        print("\n[DRY RUN] Planned requests:\n")
        for idx, (user, pwd) in enumerate(attempt_list, 1):
            print(f"  [{idx:02d}] POST {target_url}  user={user}  pass=***")
        print(f"\n[DRY RUN] Complete.  {len(attempt_list)} requests would be sent.")
        return 0

    # --- Live execution ---
    try:
        import requests  # noqa: delay import so --help/--dry-run work without it
    except ImportError:
        print("[FATAL] The 'requests' library is required.  pip install requests", file=sys.stderr)
        return 1

    session = requests.Session()

    # Initial GET for session cookie + CSRF token
    try:
        init_resp = session.get(target_url, timeout=5)
        csrf_token = _extract_csrf(init_resp.text)
    except Exception as exc:
        print(f"\n[ERROR] Cannot connect to {target_url}: {exc}")
        print("  Ensure the BruteShield server is running (python wsgi.py or run_production.bat).")
        return 1

    blocked_at = None
    captcha_at = None
    start_time = time.time()

    for idx, (user, pwd) in enumerate(attempt_list, 1):
        form = {"username": user, "password": pwd}
        if csrf_token:
            form["csrf_token"] = csrf_token

        try:
            resp = session.post(target_url, data=form, timeout=5, allow_redirects=True)
            body = resp.text
        except Exception as exc:
            print(f"[{idx:02d}] Connection error: {exc}")
            break

        # --- Classify response ---
        if "Try again in" in body or "temporarily blocked" in body.lower():
            print(f"[{idx:02d}] {user}:*** -> [BLOCKED] Cooldown active")
            blocked_at = idx
            break
        elif "Suspicious pattern" in body or "Too many failed" in body:
            print(f"[{idx:02d}] {user}:*** -> [ML BLOCK] Defense triggered")
            blocked_at = idx
            break
        elif "CAPTCHA" in body or "captcha" in body:
            print(f"[{idx:02d}] {user}:*** -> [CAPTCHA] Friction challenge")
            if not captcha_at:
                captcha_at = idx
            t = _extract_csrf(body)
            if t:
                csrf_token = t
        elif target_mode == "honeypot":
            print(f"[{idx:02d}] {user}:*** -> [HONEYPOT] Probe logged")
        elif "successful" in body.lower():
            print(f"[{idx:02d}] {user}:*** -> [LOGIN OK] Credentials matched")
            break
        else:
            print(f"[{idx:02d}] {user}:*** -> [FAILED]   HTTP {resp.status_code}")
            t = _extract_csrf(body)
            if t:
                csrf_token = t

        time.sleep(delay)

    elapsed = round(time.time() - start_time, 2)

    # --- Summary ---
    print("\n" + "=" * 70)
    print(" SIMULATION RESULTS")
    print("=" * 70)
    print(f" Attempts Sent  : {min(idx, len(attempt_list))}")
    print(f" Elapsed        : {elapsed}s")
    if blocked_at:
        print(f" Outcome        : DEFENSE SUCCESS — blocked at attempt #{blocked_at}")
    elif target_mode == "honeypot":
        print(" Outcome        : HONEYPOT — probes captured silently")
    else:
        print(" Outcome        : No block triggered within attempt window")
    if captcha_at:
        print(f" CAPTCHA At     : Attempt #{captcha_at}")
    print("\n Verify in SOC Dashboard:")
    print("   URL  : http://127.0.0.1:5000/dashboard-login")
    print("   User : dashadmin")
    print("=" * 70)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="BruteShield — Safe Attack Simulation Tool",
        epilog=(
            "SAFETY: This tool targets localhost only.  Public IPs and "
            "external domains are rejected.  All passwords are synthetic "
            "demo values, never real credential lists."
        ),
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="login",
        choices=["login", "admin", "honeypot", "spray"],
        help="Attack vector (default: login)",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:5000",
        help="Base URL of local BruteShield instance (default: http://127.0.0.1:5000)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Seconds between requests (default: 0.3, minimum: 0.1)",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=20,
        help="Maximum number of requests to send (default: 20, hard cap: 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned requests without actually sending them",
    )
    args = parser.parse_args()

    # Enforce bounds
    args.delay = max(0.1, args.delay)
    args.max_attempts = max(1, min(50, args.max_attempts))

    sys.exit(
        run_simulation(
            target_mode=args.target,
            base_url=args.url,
            delay=args.delay,
            max_attempts=args.max_attempts,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
