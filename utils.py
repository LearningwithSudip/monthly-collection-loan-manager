from datetime import date, datetime
from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

from extensions import db
from models import User, Transaction


def money(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Admin権限が必要です。")
            return redirect(url_for("dashboard.dashboard"))
        return function(*args, **kwargs)

    return wrapper


def create_transaction(transaction_type, amount, note):
    transaction = Transaction(
        tx_date=date.today(),
        tx_type=transaction_type,
        amount=int(amount),
        note=note
    )
    db.session.add(transaction)


def loan_repaid(loan):
    return sum(repayment.amount for repayment in loan.repayments)


def ensure_admin():
    admin_email = "lamsal@com"
    admin_password = "admin123"
    admin_name = "Sudip"

    existing_admin = User.query.filter_by(email=admin_email).first()

    if existing_admin:
        existing_admin.name = admin_name
        existing_admin.role = "admin"
        existing_admin.is_active_user = True

        if not existing_admin.check_password(admin_password):
            existing_admin.set_password(admin_password)

        db.session.commit()
        return

    admin = User(
        name=admin_name,
        email=admin_email,
        role="admin",
        is_active_user=True
    )

    admin.set_password(admin_password)

    db.session.add(admin)
    db.session.commit()
