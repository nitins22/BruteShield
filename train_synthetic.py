import random

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

# same numbers har baar aaye taaki result repeat ho sake
random.seed(42)
np.random.seed(42)

# feature order (app.py ke get_features_for_ip jaisa hi):
# [total_attempts, failed_attempts, distinct_usernames, avg_gap, min_gap, failure_ratio]


def normal_user():
    # normal insaan: 1-5 attempts, kabhi kabhi typo, attempts ke beech kuch second ka gap
    # kuch log password bhool jaate hain (3-8 baar lagatar galat, par insaan ki speed se)
    if random.random() < 0.10:
        total = random.randint(3, 8)
        failed = total - random.randint(0, 1)
        avg_gap = random.uniform(4, 40)
        min_gap = avg_gap * random.uniform(0.5, 1.0)
        return [total, failed, 1, round(avg_gap, 2), round(min_gap, 2), round(failed / total, 2)]

    # kabhi kabhi double-click / password manager ki wajah se do attempts bahut jaldi aate hain
    if random.random() < 0.04:
        total = random.randint(2, 3)
        failed = random.randint(1, total)
        avg_gap = random.uniform(0.3, 1.5)
        min_gap = avg_gap * random.uniform(0.6, 1.0)
        return [total, failed, 1, round(avg_gap, 2), round(min_gap, 2), round(failed / total, 2)]

    total = random.choice([1, 1, 1, 2, 2, 3, 4, 5])
    failed = sum(1 for _ in range(total) if random.random() < 0.25)
    distinct = 1 if random.random() < 0.9 else 2
    if total > 1:
        avg_gap = 10 ** random.uniform(0.4, 2.5)   # lagbhag 2.5 se 300 seconds
        min_gap = avg_gap * random.uniform(0.5, 1.0)
    else:
        avg_gap = 0
        min_gap = 0
    return [total, failed, distinct, round(avg_gap, 2), round(min_gap, 2), round(failed / total, 2)]


# model ko sirf NORMAL behaviour dikhate hain - attacker ka koi example nahi
# jo bhi is normal pattern se bahut alag hoga, wo suspicious flag hoga
X = [normal_user() for _ in range(500)]

# contamination = training ke normal data ka kitna hissa 'sabse ajeeb' maan ke flag kare
model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
model.fit(X)
joblib.dump(model, "trained_model.pkl")
print(f"Model trained on {len(X)} simulated normal-behaviour records and saved to trained_model.pkl\n")

# sanity check: kuch jaane-pehchaane scenarios pe model ka jawab
scenarios = {
    "1 galat password (typo)":            [1, 1, 1, 0, 0, 1.0],
    "2 typos, 15 sec gap":                [2, 1, 1, 15, 15, 0.5],
    "3 galat, 10 sec gap":                [3, 2, 1, 10, 8, 0.67],
    "5 attempts, 3 galat, 20 sec gap":    [5, 3, 1, 20, 15, 0.6],
    "2 galat, 0.4 sec gap (bot jaisa)":   [2, 2, 1, 0.4, 0.4, 1.0],
    "3 galat, 0.4 sec gap":               [3, 3, 1, 0.4, 0.4, 1.0],
    "5 galat, 0.4 sec gap":               [5, 5, 1, 0.4, 0.4, 1.0],
    "10 galat, 0.4 sec gap":              [10, 10, 1, 0.4, 0.4, 1.0],
    "15 galat, 0.4 sec gap":              [15, 15, 1, 0.4, 0.4, 1.0],
    "30 galat, 5 alag usernames, tez":    [30, 30, 5, 0.3, 0.1, 1.0],
    "40 galat, slow (30 sec gap)":        [40, 40, 1, 30, 30, 1.0],
}
print("Sanity check:")
for name, row in scenarios.items():
    label = "SUSPICIOUS" if model.predict([row])[0] == -1 else "Normal"
    print(f"  {name:36s} -> {label}")
