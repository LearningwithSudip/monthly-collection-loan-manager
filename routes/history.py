from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import User, CollectionPlan, Loan
from utils import loan_repaid

history_bp = Blueprint("history", __name__)


@history_bp.route("/user-history/<int:user_id>")
@login_required
def user_history(user_id):
    if current_user.role != "admin" and current_user.id != user_id:
        flash("他のユーザーの履歴は確認できません。")
        return redirect(url_for("dashboard.dashboard"))

    user = db.session.get(User, user_id)

    if not user:
        flash("ユーザーが見つかりません。")
        return redirect(url_for("dashboard.dashboard"))

    collection_plans = CollectionPlan.query.filter_by(
        user_id=user.id
    ).order_by(
        CollectionPlan.year.desc(),
        CollectionPlan.month.desc()
    ).all()

    loans = Loan.query.filter_by(
        borrower_id=user.id
    ).order_by(
        Loan.loan_date.desc()
    ).all()

    return render_template(
        "user_history.html",
        user=user,
        collection_plans=collection_plans,
        loans=loans,
        loan_repaid=loan_repaid
    )
