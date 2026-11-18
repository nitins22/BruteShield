"""
BruteShield — Production WSGI Entry Point
--------------------------------------------
Provides the importable WSGI application object ``app`` for use by external
WSGI servers (Waitress, Gunicorn, uWSGI) and a convenience ``__main__`` block
that starts the Waitress server on Windows.

Usage:

    # Import by Waitress CLI:
    waitress-serve --listen=127.0.0.1:5000 --threads=4 wsgi:app

    # Import by Gunicorn:
    gunicorn --bind 127.0.0.1:5000 --workers 2 wsgi:app

    # Direct execution (Waitress on Windows):
    python wsgi.py
"""

import os
import sys

# ---------------------------------------------------------------------------
# Application creation
# ---------------------------------------------------------------------------
# create_app() is the Flask application factory.  It reads Config (which
# itself reads environment variables), initialises the database if needed,
# registers blueprints and middleware.  Importing Config also enforces the
# production-secret guard: if BRUTESHIELD_ENV is "production" and the secret
# key / vault key are still at their demo defaults, Config.__init_subclass__
# raises RuntimeError *before* any request is served.
# ---------------------------------------------------------------------------
from bruteshield import create_app          # noqa: E402
from bruteshield.config import Config       # noqa: E402

try:
    app = create_app(Config)
except RuntimeError as exc:
    # Config raises RuntimeError when mandatory production secrets are missing.
    # Print a sanitised message (no secrets) and exit.
    print(f"[FATAL] Application startup failed: {exc}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Convenience runner — Waitress (Windows)
# ---------------------------------------------------------------------------
def _run_waitress():
    """Start Waitress in the foreground.  Never used when Gunicorn imports
    ``wsgi:app`` — only when this file is executed directly."""
    try:
        from waitress import serve          # noqa: F811
    except ImportError:
        print(
            "[FATAL] The 'waitress' package is not installed.\n"
            "        Install it with:  pip install waitress\n"
            "        Do NOT fall back to the Flask development server in production.",
            file=sys.stderr,
        )
        sys.exit(1)

    host = os.getenv("BRUTESHIELD_HOST", "127.0.0.1")
    port = int(os.getenv("BRUTESHIELD_PORT", "5000"))
    threads = int(os.getenv("WAITRESS_THREADS", "4"))

    print("=" * 70)
    print(" BruteShield — Production WSGI Server (Waitress)")
    print(f" Environment  : {Config.ENV}")
    print(f" Listening    : http://{host}:{port}")
    print(f" Threads      : {threads}")
    print(f" Database     : {Config.DB_PATH}")
    print(f" ML Model     : {Config.MODEL_PATH}")
    # Intentionally do NOT print SECRET_KEY or VAULT_KEY.
    print("=" * 70)

    serve(app, host=host, port=port, threads=threads, channel_timeout=120)


if __name__ == "__main__":
    _run_waitress()
