from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models import Loan, LoanRepayment
from utils import admin_required, parse_date, create_transaction, loan_repaid

loans_bp = Blueprint("loans", __name__)


@loans_bp.route("/loan/add", methods=["POST"])
@login_required
@admin_required
def add_loan():
    loan_amount = int(request.form.get("amount"))

    loan = Loan(
        borrower_id=int(request.form.get("borrower_id")),
        loan_date=parse_date(request.form.get("loan_date")),
        amount=loan_amount,
        note=request.form.get("note"),
        is_closed=False
    )

    db.session.add(loan)
    create_transaction("loan_disbursement", -loan.amount, "Loan disbursement")
    db.session.commit()

    flash("Loanを登録しました。")
    return redirect(url_for("dashboard.dashboard"))


@loans_bp.route("/loan-repayment/add", methods=["POST"])
@login_required
@admin_required
def add_loan_repayment():
    loan = db.session.get(Loan, int(request.form.get("loan_id")))

    if not loan:
        flash("Loanが見つかりません。")
        return redirect(url_for("dashboard.dashboard"))

    repayment_amount = int(request.form.get("amount"))
    remaining = loan.amount - loan_repaid(loan)

    if repayment_amount > remaining:
        flash("返済額がLoan Remainingを超えています。")
        return redirect(url_for("dashboard.dashboard"))

    repayment = LoanRepayment(
        loan_id=loan.id,
        repayment_date=parse_date(request.form.get("repayment_date")),
        amount=repayment_amount,
        note=request.form.get("note")
    )

    db.session.add(repayment)

    create_transaction(
        "loan_repayment",
        repayment.amount,
        f"Loan repayment from {loan.borrower.name}"
    )

    if repayment_amount == remaining:
        loan.is_closed = True

    db.session.commit()

    flash("Loan返済を登録しました。")
    return redirect(url_for("dashboard.dashboard"))
