import sqlite3

conn = sqlite3.connect("logs/bruteshield.db")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT ip, username_tried, password_tried, timestamp FROM honeypot_logs"
).fetchall()

if not rows:
    print("Abhi tak honeypot me koi attempt record nahi hua.")
else:
    print(f"Total honeypot attempts: {len(rows)}\n")
    for r in rows:
        print(f"IP: {r['ip']}  |  Username tried: {r['username_tried']}  |  "
              f"Password tried: {r['password_tried']}")

conn.close()