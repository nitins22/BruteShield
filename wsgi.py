"""
BruteShield - Production WSGI Entrypoint
------------------------------------------
Production-hardened WSGI entry point suitable for deployment with Waitress (Windows)
or Gunicorn / uWSGI (Linux).

Usage:
    Direct execution with Waitress:
        python wsgi.py

    Via Waitress CLI:
        waitress-serve --listen=127.0.0.1:5000 wsgi:app

    Via Gunicorn (Linux):
        gunicorn --bind 127.0.0.1:5000 --workers 4 wsgi:app
"""

import os
import sys
from bruteshield import create_app
from bruteshield.config import Config
from bruteshield.database import init_db

# Initialize application using configured environment
app = create_app(Config)

def run_production_server():
    """Launch production WSGI server using Waitress."""
    try:
        from waitress import serve
    except ImportError:
        print("[!] Warning: waitress is not installed. Falling back to development server.", file=sys.stderr)
        app.run(host="127.0.0.1", port=5000)
        return

    host = os.getenv("BRUTESHIELD_HOST", "127.0.0.1")
    port = int(os.getenv("BRUTESHIELD_PORT", "5000"))
    threads = int(os.getenv("WAITRESS_THREADS", "8"))
    
    print("=" * 70)
    print(" [BruteShield] Production WSGI Server (Waitress)")
    print(f" Environment : {Config.ENV.upper()}")
    print(f" Listening   : http://{host}:{port}")
    print(f" Workers     : {threads} worker threads")
    print(f" Database    : {Config.DB_PATH}")
    print(f" ML Model    : {Config.MODEL_PATH}")
    print("=" * 70)

    serve(app, host=host, port=port, threads=threads, channel_timeout=120)

if __name__ == "__main__":
    init_db(Config.DB_PATH)
    run_production_server()
