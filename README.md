# BruteShield

An ML-based system that detects and responds to brute-force login attacks in real time.
Instead of the usual "5 wrong attempts = block" rule, it looks at the **behaviour** of each IP
(number of attempts, speed, number of usernames tried, failure ratio) using an Isolation Forest model.

Built as a BTech CSE mini project at ABES Engineering College, Ghaziabad.

## What it does

| Feature | How it works |
|---|---|
| ML detection | Isolation Forest scores every IP after each failed login |
| 3-level response | Normal -> nothing, borderline -> CAPTCHA, suspicious -> block |
| Adaptive cool-down | Repeat offenders are blocked for longer (1 min, 5 min, 15 min, 1 hour) |
| Password strength check | `/signup` uses `zxcvbn`; weak passwords are rejected |
| Honeypot | `/admin-login` is a decoy page; any IP that tries it is blocked everywhere |
| Admin alerts | Block / CAPTCHA / honeypot events are saved and shown on the dashboard |
| Dashboard | Stats, recent alerts, recent login and honeypot attempts (admin login required) |
| Admin login protection | The dashboard login is protected by the same engine |

## Setup (one time)

```
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python train_synthetic.py      # creates trained_model.pkl
```

## Run

```
python app.py
```

Open the pages below. **Only run this on your own computer (localhost).**

| Page | Purpose | Demo credentials |
|---|---|---|
| `/login` | Protected login page | `admin` / `Secure@123` |
| `/signup` | Password strength check | any password you want to test |
| `/admin-login` | Honeypot (decoy) | anything - it always says "Invalid" |
| `/dashboard-login` | Admin login for the dashboard | `dashadmin` / `Dash@Admin1` |
| `/dashboard` | Dashboard (needs admin login) | |

## Demo and test scripts

| Script | What it does |
|---|---|
| `attack_simulation.py` | Fires 15 common passwords at `/login` (use `python attack_simulation.py admin` for the admin login) |
| `check_honeypot.py` | Prints everything the honeypot has captured |
| `evaluate.py` | Accuracy / precision / recall / F1 of the ML model vs the old 5-attempt rule on a simulated test set; saves `evaluation_results.txt` |
| `debug_model.py` | Replays the stored login history through the model, attempt by attempt |
| `features.py`, `simulate_test.py`, `predict.py` | Smaller helper scripts used while building the model |
| `train_model.py` | Early version that trains on whatever is in the database. **Do not run it for the demo** - it overwrites `trained_model.pkl` with a model trained on very little data |

For a clean demo: stop the server, delete `logs/bruteshield.db`, start the server again.
After retraining the model with `train_synthetic.py`, always restart `app.py` (the model is loaded at startup).

## Typical demo attack

`python attack_simulation.py` - first attempts are rejected, then a CAPTCHA appears, and the IP is blocked at
roughly the 7th attempt. Check `/dashboard` for the alerts.

## Settings (top of `app.py`)

- `BLOCK_DURATIONS` - block times for repeat offenders
- `CAPTCHA_SCORE_LIMIT` - how close to "suspicious" the model score must be to show a CAPTCHA

## Results (simulated test set)

On a simulated test set the ML model reached roughly F1 0.95 and recall 0.96, compared with F1 0.73 and recall 0.58
for the old 5-attempt rule (it catches slow attacks the old rule misses completely). It also blocks more genuine users
who forget their password. Run `python evaluate.py` for the exact numbers.

## Limitations

- The model is trained and tested on **simulated** login behaviour, not real traffic (CICIDS2017 / real logs are future work).
- Detection is per IP, so a distributed attack (many IPs, few attempts each) is not caught.
- The CAPTCHA is a simple maths question; real bots can solve it.
- Admin credentials and the Flask secret key are hard-coded for the demo.
- Alerts are shown on the dashboard and printed in the console; there is no email yet.

## Project files

```
app.py                  Flask app (login, signup, honeypot, dashboard, ML logic)
train_synthetic.py      Trains the Isolation Forest on simulated normal behaviour
evaluate.py             Model evaluation
attack_simulation.py    Attack demo script
templates/              HTML pages
logs/                   SQLite database (created automatically, not committed)
```