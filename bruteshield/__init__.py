import os
from flask import Flask
from bruteshield.config import Config
from bruteshield.database import init_db

def create_app(config_class=Config):
    """Application Factory for BruteShield."""
    app = Flask(
        __name__,
        template_folder=os.path.join(Config.BASE_DIR, "templates"),
        static_folder=os.path.join(Config.BASE_DIR, "static")
    )
    app.config.from_object(config_class)

    # Secure cookie policies
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Initialize SQLite database and default seeds
    init_db(app.config["DB_PATH"])

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
