import random

import joblib

# training (train_synthetic.py) me seed 42 tha - yahan alag seed, taaki test data naya ho
random.seed(2024)

MODEL = joblib.load("trained_model.pkl")

# har IP ek "episode" hai: attempts ki list, har attempt = (username, success, timestamp)


# ---------- normal users ----------
def normal_ok():
    return [("admin", 1, 0.0)]


def normal_typo():
    rows, t = [], 0.0
    for _ in range(random.randint(1, 3)):
        rows.append(("admin", 0, t))
        t += random.uniform(3, 40)
    rows.append(("admin", 1, t))
    return rows


def normal_forgetful():
    rows, t = [], 0.0
    for _ in range(random.randint(3, 8)):
        rows.append(("admin", 0, t))
        t += random.uniform(5, 60)
    if random.random() < 0.5:
        rows.append(("admin", 1, t))
    return rows


def normal_double_click():
    return [("admin", 0, 0.0), ("admin", 0, random.uniform(0.3, 1.5))]


# ---------- attackers ----------
def attack(n_lo, n_hi, gap_lo, gap_hi, users_lo, users_hi):
    n = random.randint(n_lo, n_hi)
    users = [f"user{i}" for i in range(random.randint(users_lo, users_hi))]
    rows, t = [], 0.0
    for _ in range(n):
        rows.append((random.choice(users), 0, t))
        t += random.uniform(gap_lo, gap_hi)
    return rows


NORMAL_KINDS = [
    ("seedha sahi login", normal_ok, 150),
    ("1-3 typo phir sahi", normal_typo, 90),
    ("password bhoolne wale (3-8 galat)", normal_forgetful, 40),
    ("double-click (2 jaldi attempts)", normal_double_click, 20),
]
ATTACK_KINDS = [
    ("fast brute-force", lambda: attack(8, 60, 0.1, 1.5, 1, 2), 60),
    ("credential stuffing (kai usernames)", lambda: attack(10, 60, 0.1, 1.5, 5, 40), 50),
    ("low-and-slow (dheere, 12-60 sec gap)", lambda: attack(20, 80, 12, 60, 1, 3), 50),
    ("stealthy (sirf 3-4 attempts)", lambda: attack(3, 4, 4, 15, 2, 3), 30),
]


# ---------- app.py wale features ka same formula ----------
def features(rows):
    n = len(rows)
    failed = sum(1 for r in rows if r[1] == 0)
    users = len(set(r[0] for r in rows))
    stamps = sorted(r[2] for r in rows)
    gaps = [stamps[i + 1] - stamps[i] for i in range(n - 1)]
    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    min_gap = min(gaps) if gaps else 0
    return [n, failed, users, avg_gap, min_gap, failed / n]


# ---------- detectors: jis attempt number pe block hua wo return karte hain, nahi hua to None ----------
def ml_detect(rows):
    # app me ML sirf galat attempt ke baad chalta hai
    idx = [i for i in range(1, len(rows) + 1) if rows[i - 1][1] == 0]
    if not idx:
        return None
    preds = MODEL.predict([features(rows[:i]) for i in idx])
    for i, p in zip(idx, preds):
        if p == -1:
            return i
    return None


def baseline_detect(rows, window=60, limit=5):
    # purana rule: pichle 60 sec me 5 galat attempts = block
    for i in range(1, len(rows) + 1):
        if rows[i - 1][1] == 1:
            continue
        t = rows[i - 1][2]
        recent = sum(1 for x in rows[:i] if x[1] == 0 and t - x[2] <= window)
        if recent >= limit:
            return i
    return None


def scores(tp, fp, fn, tn):
    acc = (tp + tn) / (tp + fp + fn + tn)
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    return acc, prec, rec, f1


# ---------- test chalao ----------
results = {"ML": {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "delay": []},
           "Rule": {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "delay": []}}
by_kind = {}

for kind, maker, count in NORMAL_KINDS + ATTACK_KINDS:
    is_attack = (kind, maker, count) in ATTACK_KINDS
    by_kind[kind] = {"attack": is_attack, "n": count, "ML": 0, "Rule": 0}
    for _ in range(count):
        rows = maker()
        for name, detect in (("ML", ml_detect), ("Rule", baseline_detect)):
            hit = detect(rows)
            r = results[name]
            if is_attack and hit:
                r["tp"] += 1
                r["delay"].append(hit)
            elif is_attack and not hit:
                r["fn"] += 1
            elif not is_attack and hit:
                r["fp"] += 1
            else:
                r["tn"] += 1
            if hit:
                by_kind[kind][name] += 1

n_normal = sum(c for _, _, c in NORMAL_KINDS)
n_attack = sum(c for _, _, c in ATTACK_KINDS)

lines = []
lines.append(f"EVALUATION - simulated test set: {n_normal} normal IPs, {n_attack} attacker IPs")
lines.append("(positive class = attacker; 'block' = system ne us IP ko block kiya)\n")

lines.append(f"{'':34s}{'BruteShield ML':>16s}{'Old 5-attempt rule':>20s}")
s_ml = scores(*(results["ML"][k] for k in ("tp", "fp", "fn", "tn")))
s_rule = scores(*(results["Rule"][k] for k in ("tp", "fp", "fn", "tn")))
for label, a, b in zip(("Accuracy", "Precision", "Recall", "F1-score"), s_ml, s_rule):
    lines.append(f"{label:34s}{a:>16.3f}{b:>20.3f}")


def avg(xs):
    return f"{sum(xs) / len(xs):.1f}" if xs else "-"


lines.append(f"{'Avg attempt jispe attacker block hua':34s}{avg(results['ML']['delay']):>16s}{avg(results['Rule']['delay']):>20s}")

lines.append("\nConfusion matrix (BruteShield ML):")
lines.append(f"                    block hua   block nahi hua")
lines.append(f"  asli attacker     {results['ML']['tp']:>9d}   {results['ML']['fn']:>14d}   (TP / FN)")
lines.append(f"  asli normal user  {results['ML']['fp']:>9d}   {results['ML']['tn']:>14d}   (FP / TN)")
lines.append("\nConfusion matrix (Old 5-attempt rule):")
lines.append(f"                    block hua   block nahi hua")
lines.append(f"  asli attacker     {results['Rule']['tp']:>9d}   {results['Rule']['fn']:>14d}   (TP / FN)")
lines.append(f"  asli normal user  {results['Rule']['fp']:>9d}   {results['Rule']['tn']:>14d}   (FP / TN)")

lines.append("\nAttacker types - kitne % pakde gaye:")
lines.append(f"  {'type':40s}{'ML':>8s}{'Old rule':>10s}")
for kind, info in by_kind.items():
    if info["attack"]:
        lines.append(f"  {kind:40s}{100 * info['ML'] / info['n']:>7.0f}%{100 * info['Rule'] / info['n']:>9.0f}%")

lines.append("\nNormal users - kitne % galti se block hue (kam = behtar):")
lines.append(f"  {'type':40s}{'ML':>8s}{'Old rule':>10s}")
for kind, info in by_kind.items():
    if not info["attack"]:
        lines.append(f"  {kind:40s}{100 * info['ML'] / info['n']:>7.0f}%{100 * info['Rule'] / info['n']:>9.0f}%")

report = "\n".join(lines)
print(report)
with open("evaluation_results.txt", "w", encoding="utf-8") as f:
    f.write(report + "\n")
print("\nResult evaluation_results.txt me save ho gaya.")