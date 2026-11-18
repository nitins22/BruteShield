#!/usr/bin/env bash
# =========================================================================
#  BruteShield — Linux / Unix Production Launcher
# =========================================================================
#  Validates the environment and starts the production WSGI server in the
#  foreground.  Designed to run directly or under systemd supervision.
#
#  When managed by systemd, run Gunicorn in the FOREGROUND (no --daemon).
#  systemd handles process lifecycle, restart and logging.
#
#  Default binding: 127.0.0.1:5000  (localhost only)
# =========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# --- 1. Activate virtual environment ---
if [ -f "venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    source venv/Scripts/activate
else
    echo "[FATAL] Virtual environment not found.  Create with: python3 -m venv venv"
    exit 1
fi

# --- 2. Validate Python ---
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "[FATAL] Python interpreter not found."
    exit 1
fi
PYTHON="$(command -v python3 || command -v python)"

# --- 3. Check database directory ---
DB_DIR="$(dirname "${BRUTESHIELD_DB_PATH:-logs/bruteshield.db}")"
if [ ! -d "$DB_DIR" ]; then
    echo "[INFO] Creating database directory: $DB_DIR"
    mkdir -p "$DB_DIR"
fi
if [ ! -w "$DB_DIR" ]; then
    echo "[FATAL] Database directory $DB_DIR is not writable."
    exit 1
fi

# --- 4. Check ML model ---
MODEL_PATH="${BRUTESHIELD_MODEL_PATH:-trained_model.pkl}"
if [ ! -f "$MODEL_PATH" ]; then
    echo "[WARN] ML model $MODEL_PATH not found.  ML scoring unavailable."
fi

# --- 5. Production secret guard ---
if [ "${BRUTESHIELD_ENV:-development}" = "production" ]; then
    if [ -z "${BRUTESHIELD_SECRET_KEY:-}" ]; then
        echo "[FATAL] BRUTESHIELD_ENV=production but BRUTESHIELD_SECRET_KEY is not set."
        exit 1
    fi
    if [ -z "${BRUTESHIELD_VAULT_KEY:-}" ]; then
        echo "[FATAL] BRUTESHIELD_ENV=production but BRUTESHIELD_VAULT_KEY is not set."
        exit 1
    fi
fi

# --- 6. Start WSGI server ---
HOST="${BRUTESHIELD_HOST:-127.0.0.1}"
PORT="${BRUTESHIELD_PORT:-5000}"

if "$PYTHON" -c "import gunicorn" 2>/dev/null; then
    WORKERS="${GUNICORN_WORKERS:-2}"
    echo "==========================================================================="
    echo " BruteShield — Starting Gunicorn (${WORKERS} workers)"
    echo " Binding : http://${HOST}:${PORT}"
    echo "==========================================================================="
    # Foreground mode for systemd supervision; no --daemon.
    exec gunicorn \
        --bind "${HOST}:${PORT}" \
        --workers "${WORKERS}" \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        wsgi:app
elif "$PYTHON" -c "import waitress" 2>/dev/null; then
    echo "==========================================================================="
    echo " BruteShield — Starting Waitress"
    echo " Binding : http://${HOST}:${PORT}"
    echo "==========================================================================="
    exec "$PYTHON" wsgi.py
else
    echo "[FATAL] Neither gunicorn nor waitress is installed."
    echo "        Install with:  pip install gunicorn   (or)   pip install waitress"
    exit 1
fi
