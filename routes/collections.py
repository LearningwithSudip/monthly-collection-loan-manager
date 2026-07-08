from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models import CollectionPlan, CollectionPayment
from utils import admin_required, parse_date, create_transaction

collections_bp = Blueprint("collections", __name__)


@collections_bp.route("/collection-plan/add", methods=["POST"])
@login_required
@admin_required
def add_collection_plan():
    user_id = int(request.form.get("user_id"))
    year = int(request.form.get("year"))
    month = int(request.form.get("month"))
    expected_amount = int(request.form.get("expected_amount"))

    if month < 1 or month > 12:
        flash("Monthは1～12で入力してください。")
        return redirect(url_for("dashboard.dashboard", year=year))

    existing_plan = CollectionPlan.query.filter_by(
        user_id=user_id,
        year=year,
        month=month
    ).first()

    if existing_plan:
        flash("このユーザーの同じ年月の集金予定は既に存在します。")
        return redirect(url_for("dashboard.dashboard", year=year))

    plan = CollectionPlan(
        user_id=user_id,
        year=year,
        month=month,
        expected_amount=expected_amount
    )

    db.session.add(plan)
    db.session.commit()

    flash("集金予定を追加しました。")
    return redirect(url_for("dashboard.dashboard", year=year))


@collections_bp.route("/collection-payment/add", methods=["POST"])
@login_required
@admin_required
def add_collection_payment():
    plan = db.session.get(CollectionPlan, int(request.form.get("plan_id")))

    if not plan:
        flash("集金予定が見つかりません。")
        return redirect(url_for("dashboard.dashboard"))

    paid_amount = int(request.form.get("paid_amount"))

    payment = CollectionPayment(
        plan_id=plan.id,
        paid_amount=paid_amount,
        paid_date=parse_date(request.form.get("paid_date")),
        note=request.form.get("note")
    )

    db.session.add(payment)

    create_transaction(
        "collection_payment",
        payment.paid_amount,
        f"{plan.user.name} {plan.year}/{plan.month} Collection"
    )

    db.session.commit()

    flash("支払いを登録しました。")
    return redirect(url_for("dashboard.dashboard", year=plan.year))
