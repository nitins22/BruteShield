import os
import secrets
import time
from flask import Flask, request, session, jsonify, abort
from bruteshield.config import Config
from bruteshield.database import init_db, get_db, is_postgres_target
from bruteshield.ml.engine import get_ml_model


def create_app(config_class=Config):
    """Application Factory for BruteShield."""
    app = Flask(
        __name__,
        template_folder=os.path.join(Config.BASE_DIR, "templates"),
        static_folder=os.path.join(Config.BASE_DIR, "static")
    )
    app.config.from_object(config_class)

    # Secure cookie policies
    app.config["SESSION_COOKIE_HTTPONLY"] = getattr(config_class, "SESSION_COOKIE_HTTPONLY", True)
    app.config["SESSION_COOKIE_SAMESITE"] = getattr(config_class, "SESSION_COOKIE_SAMESITE", "Lax")
    app.config["SESSION_COOKIE_SECURE"] = getattr(config_class, "SESSION_COOKIE_SECURE", False)

    # Reverse proxy support (Render / Cloudflare / Nginx)
    if app.config.get("BEHIND_PROXY"):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Initialize database (PostgreSQL or SQLite) and schemas
    target_db = app.config.get("DATABASE_URL") or app.config.get("DB_PATH")
    init_db(target_db)

    # Health check endpoint for container orchestrators and Render
    @app.route("/health", methods=["GET"])
    def health_check():
        """Production health-check endpoint for load balancers and Render."""
        try:
            conn = get_db(target_db)
            conn.execute("SELECT 1").fetchone()
            conn.close()
            db_status = "connected"
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": time.time()
            }), 503

        model = get_ml_model()
        return jsonify({
            "status": "healthy",
            "database": db_status,
            "database_engine": "postgresql" if is_postgres_target(target_db) else "sqlite",
            "model_loaded": model is not None,
            "timestamp": time.time()
        }), 200

    # --- 1. CSRF Protection Middleware ---
    def generate_csrf_token():
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_hex(32)
        return session["_csrf_token"]

    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    @app.before_request
    def check_csrf_token():
        # Exempt safe HTTP methods
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return None

        # Exempt honeypot decoy (/admin-login) so attacker scripts can be trapped without CSRF tokens
        if request.path == "/admin-login":
            return None

        # In testing mode, enforce CSRF only when explicitly enabled (WTF_CSRF_ENABLED: True)
        if app.config.get("TESTING") and not app.config.get("WTF_CSRF_ENABLED", False):
            return None

        # Stateless public API password analysis
        if request.path == "/api/password-analyze":
            return None

        # Verify CSRF token from header or form body
        token = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
        if not token and request.form:
            token = request.form.get("csrf_token")
        if not token and request.is_json:
            token = (request.get_json(silent=True) or {}).get("csrf_token")

        expected = session.get("_csrf_token")
        if not expected or not token or not secrets.compare_digest(token, expected):
            if request.path.startswith("/api/") or request.path.startswith("/dashboard/api/"):
                return jsonify({"error": "CSRF verification failed", "message": "Missing or invalid CSRF token"}), 403
            abort(403, description="CSRF verification failed")

    # --- 2. Defense-in-Depth Security Response Headers ---
    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' https://api.pwnedpasswords.com; "
            "frame-ancestors 'self'; "
            "form-action 'self';"
        )
        if app.config.get("ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # --- 3. Safe Error Handlers (No Stack Traces Leaked) ---
    @app.errorhandler(403)
    def forbidden_error(e):
        if request.path.startswith("/api/") or request.path.startswith("/dashboard/api/"):
            return jsonify({"error": "Forbidden", "message": str(e.description if hasattr(e, 'description') else "Access Denied")}), 403
        return f"<div style='font-family:sans-serif; padding:40px; text-align:center;'><h2>403 Forbidden</h2><p>{e.description if hasattr(e, 'description') else 'Access denied.'}</p></div>", 403

    @app.errorhandler(413)
    def payload_too_large(e):
        return jsonify({"error": "Payload Too Large", "message": "Request entity exceeds maximum allowable size limit"}), 413

    # Register blueprints
    from bruteshield.routes.auth_routes import auth_bp
    from bruteshield.routes.vault_routes import vault_bp
    from bruteshield.routes.dashboard_routes import dashboard_bp
    from bruteshield.routes.honeypot_routes import honeypot_bp
    from bruteshield.routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(vault_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(honeypot_bp)
    app.register_blueprint(api_bp)

    return app
