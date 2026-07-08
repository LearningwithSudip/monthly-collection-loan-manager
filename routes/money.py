from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models import Expense, OtherIncome
from utils import admin_required, parse_date, create_transaction

money_bp = Blueprint("money", __name__)


@money_bp.route("/expense/add", methods=["POST"])
@login_required
@admin_required
def add_expense():
    amount = int(request.form.get("amount"))

    expense = Expense(
        expense_date=parse_date(request.form.get("expense_date")),
        amount=amount,
        note=request.form.get("note")
    )

    db.session.add(expense)
    create_transaction("expense", -expense.amount, expense.note or "Expense")
    db.session.commit()

    flash("支出を登録しました。")
    return redirect(url_for("dashboard.dashboard"))


@money_bp.route("/income/add", methods=["POST"])
@login_required
@admin_required
def add_income():
    amount = int(request.form.get("amount"))

    income = OtherIncome(
        income_date=parse_date(request.form.get("income_date")),
        amount=amount,
        note=request.form.get("note")
    )

    db.session.add(income)
    create_transaction("other_income", income.amount, income.note or "Other Income")
    db.session.commit()

    flash("その他収入を登録しました。")
    return redirect(url_for("dashboard.dashboard"))
