# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 Intiphlora LLC
"""
IntimaGuard — Flask App Factory
"""

import os
from flask import Flask
from config import config


def create_app(env: str | None = None) -> Flask:
    env = env or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config.get(env, config["default"]))

    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.api import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app
