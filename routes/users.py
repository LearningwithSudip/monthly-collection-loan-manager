from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models import User
from utils import admin_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/users/add", methods=["POST"])
@login_required
@admin_required
def add_user():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    role = request.form.get("role", "user")

    if not name or not email or not password:
        flash("Name、Email、Passwordは必須です。")
        return redirect(url_for("dashboard.dashboard"))

    if role not in ("admin", "user"):
        role = "user"

    if User.query.filter_by(email=email).first():
        flash("このEmailは既に登録されています。")
        return redirect(url_for("dashboard.dashboard"))

    user = User(
        name=name,
        email=email,
        role=role,
        is_active_user=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash("ユーザーを追加しました。")
    return redirect(url_for("dashboard.dashboard"))
