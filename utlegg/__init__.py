import logging
import os

from flask import Flask, redirect, url_for

from . import db
from .config import Config


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    db.init_app(app)

    from .auth import bp as auth_bp
    from .expenses import bp as expenses_bp
    from .profile import bp as profile_bp
    from .admin import bp as admin_bp
    from .internal import bp as internal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(internal_bp)

    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config["APP_NAME"],
            "company_name": app.config["COMPANY_NAME"],
        }

    @app.route("/")
    def index():
        return redirect(url_for("expenses.list_expenses"))

    return app
