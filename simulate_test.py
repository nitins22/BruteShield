from app import app, init_db
from features import extract_features, print_as_table
import time
import random

init_db()
client = app.test_client()

# 15 "normal users" - sab sahi password, alag alag IPs se
for i in range(15):
    fake_ip = f"192.168.1.{i+10}"
    client.post("/login", data={"username": "admin", "password": "Secure@123"},
                environ_base={"REMOTE_ADDR": fake_ip})

# ek "attacker" jaisa behavior - jaldi jaldi, alag alag usernames, sab galat
attacker_usernames = ["admin", "root", "test", "user", "guest"]
for uname in attacker_usernames:
    client.post("/login", data={"username": uname, "password": "wrongpass"},
                environ_base={"REMOTE_ADDR": "45.33.12.9"})
    time.sleep(0.1)

print("Simulated data generated. Feature table:\n")
print_as_table(extract_features())