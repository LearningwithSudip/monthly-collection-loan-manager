from flask import Flask, redirect, url_for
from flask_login import current_user

from config import Config
from extensions import db, login_manager
from models import User
from utils import ensure_admin

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.users import users_bp
from routes.collections import collections_bp
from routes.loans import loans_bp
from routes.money import money_bp
from routes.history import history_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "ログインしてください。"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.before_request
    def before_request():
        db.create_all()
        ensure_admin()

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("auth.login"))

    @app.route("/setup-db")
    def setup_db():
        db.create_all()
        ensure_admin()
        return "Database and Admin created successfully."

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(money_bp)
    app.register_blueprint(history_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=False)
