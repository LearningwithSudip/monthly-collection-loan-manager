from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from models import (
    User,
    CollectionPlan,
    CollectionPayment,
    Loan,
    LoanRepayment,
    Expense,
    OtherIncome,
    Transaction,
)
from utils import money, loan_repaid

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.app_template_filter("money")
def money_filter(value):
    return money(value)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    try:
        selected_year = int(request.args.get("year", datetime.now().year))
    except (TypeError, ValueError):
        selected_year = datetime.now().year

    if current_user.role == "admin":
        users = User.query.filter_by(
            is_active_user=True
        ).order_by(User.name).all()
    else:
        users = [current_user]

    all_users = User.query.order_by(User.name).all()
    user_ids = [user.id for user in users]

    plans = CollectionPlan.query.filter(
        CollectionPlan.user_id.in_(user_ids),
        CollectionPlan.year == selected_year
    ).order_by(CollectionPlan.month).all()

    if current_user.role == "admin":
        loans = Loan.query.order_by(Loan.loan_date.desc()).all()
        transactions = Transaction.query.order_by(
            Transaction.id.desc()
        ).limit(50).all()
    else:
        loans = Loan.query.filter_by(
            borrower_id=current_user.id
        ).order_by(Loan.loan_date.desc()).all()
        transactions = []

    months = list(range(1, 13))
    collection_matrix = []

    for user in users:
        row = {
            "user": user,
            "months": {},
            "total_expected": 0,
            "total_paid": 0
        }

        for month in months:
            plan = CollectionPlan.query.filter_by(
                user_id=user.id,
                year=selected_year,
                month=month
            ).first()

            expected = plan.expected_amount if plan else 0
            paid = sum(payment.paid_amount for payment in plan.payments) if plan else 0

            if expected == 0:
                status = "none"
            elif paid == 0:
                status = "unpaid"
            elif paid < expected:
                status = "partial"
            elif paid == expected:
                status = "paid"
            else:
                status = "overpaid"

            row["months"][month] = {
                "plan": plan,
                "expected": expected,
                "paid": paid,
                "status": status
            }

            row["total_expected"] += expected
            row["total_paid"] += paid

        collection_matrix.append(row)

    total_collections = sum(
        payment.paid_amount for payment in CollectionPayment.query.all()
    )

    total_loan_disbursement = sum(
        loan.amount for loan in Loan.query.all()
    )

    total_loan_repayment = sum(
        repayment.amount for repayment in LoanRepayment.query.all()
    )

    total_expenses = sum(
        expense.amount for expense in Expense.query.all()
    )

    total_other_income = sum(
        income.amount for income in OtherIncome.query.all()
    )

    cash_in_hand = (
        total_collections
        + total_loan_repayment
        - total_loan_disbursement
        + total_other_income
        - total_expenses
    )

    outstanding_loans = sum(
        max(0, loan.amount - loan_repaid(loan))
        for loan in Loan.query.all()
    )

    unpaid_collections = sum(
        max(0, cell["expected"] - cell["paid"])
        for row in collection_matrix
        for cell in row["months"].values()
    )

    if current_user.role == "admin":
        loan_users = User.query.filter_by(
            is_active_user=True
        ).order_by(User.name).all()
    else:
        loan_users = [current_user]

    loan_summary = []

    for user in loan_users:
        user_loans = Loan.query.filter_by(borrower_id=user.id).all()

        total_loan = sum(loan.amount for loan in user_loans)
        total_repaid = sum(loan_repaid(loan) for loan in user_loans)
        total_remaining = total_loan - total_repaid

        if total_loan > 0:
            loan_summary.append({
                "user": user,
                "total_loan": total_loan,
                "total_repaid": total_repaid,
                "total_remaining": total_remaining,
                "loans": user_loans
            })

    return render_template(
        "dashboard.html",
        year=selected_year,
        users=users,
        all_users=all_users,
        plans=plans,
        loans=loans,
        loan_summary=loan_summary,
        transactions=transactions,
        months=months,
        collection_matrix=collection_matrix,
        cash_in_hand=cash_in_hand,
        total_collections=total_collections,
        outstanding_loans=outstanding_loans,
        unpaid_collections=unpaid_collections,
        loan_repaid=loan_repaid
    )
