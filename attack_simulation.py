import sys
import time
import requests

# python attack_simulation.py          -> /login pe attack
# python attack_simulation.py admin    -> /dashboard-login pe attack
# sirf apna local server - kisi aur ke server pe kabhi mat chalana
target = sys.argv[1] if len(sys.argv) > 1 else "login"
URL = "http://127.0.0.1:5000/dashboard-login" if target == "admin" else "http://127.0.0.1:5000/login"

# chhoti si common passwords ki list (real attack me lakhon hote hain)
passwords = [
    "123456", "password", "admin", "qwerty", "letmein",
    "welcome", "admin123", "iloveyou", "abc123", "monkey",
    "dragon", "football", "sunshine", "master", "shadow",
]

print(f"Attack simulation started on {URL}\n")

blocked_at = None
start = time.time()

for i, pwd in enumerate(passwords, start=1):
    resp = requests.post(URL, data={"username": "admin", "password": pwd})
    text = resp.text

    if "Try again in" in text:
        print(f"Attempt {i:2d}: IP pehle se blocked hai (purane test ka block). "
              f"Block khatam hone ka wait karo ya bruteshield.db delete karo.")
        break
    elif "Suspicious pattern" in text or "Too many failed" in text:
        print(f"Attempt {i:2d}: '{pwd}' -> BLOCKED by BruteShield")
        blocked_at = i
        break
    elif "CAPTCHA" in text:
        print(f"Attempt {i:2d}: '{pwd}' -> CAPTCHA challenge (bot solve nahi kar sakta)")
    elif "successful" in text:
        print(f"Attempt {i:2d}: '{pwd}' -> login SUCCESS (password guess ho gaya!)")
        break
    else:
        print(f"Attempt {i:2d}: '{pwd}' -> rejected")

    time.sleep(0.2)

elapsed = round(time.time() - start, 1)
print("\n--- Summary ---")
if blocked_at:
    print(f"BruteShield ne attacker ko {blocked_at} attempts ke baad block kar diya ({elapsed} seconds me).")
else:
    print(f"{len(passwords)} attempts ke baad bhi block nahi hua ({elapsed} seconds).")
    print("Dashboard (/dashboard) check karo aur neeche wali notes padho.")