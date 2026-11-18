#!/usr/bin/env bash
# ==============================================================================
#  BruteShield - Linux/Unix Production Startup Script
# ==============================================================================
set -e

echo "[BruteShield] Initializing production launcher..."

if [ -f "venv/bin/activate" ]; then
    echo "[BruteShield] Activating virtual environment..."
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# Ensure requirements are satisfied
if ! python3 -c "import waitress" 2>/dev/null && ! python3 -c "import gunicorn" 2>/dev/null; then
    echo "[!] Neither waitress nor gunicorn installed. Installing requirements..."
    pip install -r requirements.txt
fi

if python3 -c "import gunicorn" 2>/dev/null; then
    echo "[*] Launching via Gunicorn..."
    exec gunicorn --bind "${BRUTESHIELD_HOST:-127.0.0.1}:${BRUTESHIELD_PORT:-5000}" \
        --workers "${GUNICORN_WORKERS:-4}" \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        wsgi:app
else
    echo "[*] Launching via Waitress..."
    exec python3 wsgi.py
fi
