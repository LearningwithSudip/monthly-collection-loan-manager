import os
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


# ============================================================
# Flask Configuration
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key-change-me"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///monthly_manager.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


database_url = app.config["SQLALCHEMY_DATABASE_URI"]

if database_url.startswith("postgres://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )


db = SQLAlchemy(app)


# ============================================================
# Login Manager
# ============================================================

login_manager = LoginManager(app)

login_manager.login_view = "login"
login_manager.login_message = "ログインしてください。"


# ============================================================
# User Model
# ============================================================

class User(db.Model, UserMixin):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="user",
        nullable=False
    )

    is_active_user = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

    @property
    def is_active(self):
        return self.is_active_user


# ============================================================
# Collection Plan
# ============================================================

class CollectionPlan(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    year = db.Column(
        db.Integer,
        nullable=False
    )

    month = db.Column(
        db.Integer,
        nullable=False
    )

    expected_amount = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="collection_plans"
    )

    payments = db.relationship(
        "CollectionPayment",
        backref="plan",
        lazy=True
    )


# ============================================================
# Collection Payment
# ============================================================

class CollectionPayment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("collection_plan.id"),
        nullable=False
    )

    paid_amount = db.Column(
        db.Integer,
        nullable=False
    )

    paid_date = db.Column(
        db.Date,
        nullable=False
    )

    note = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# Loan
# ============================================================

class Loan(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    borrower_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    loan_date = db.Column(
        db.Date,
        nullable=False
    )

    amount = db.Column(
        db.Integer,
        nullable=False
    )

    note = db.Column(
        db.String(255)
    )

    is_closed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    borrower = db.relationship(
        "User",
        backref="loans"
    )

    repayments = db.relationship(
        "LoanRepayment",
        backref="loan",
        lazy=True
    )


# ============================================================
# Loan Repayment
# ============================================================

class LoanRepayment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    loan_id = db.Column(
        db.Integer,
        db.ForeignKey("loan.id"),
        nullable=False
    )

    repayment_date = db.Column(
        db.Date,
        nullable=False
    )

    amount = db.Column(
        db.Integer,
        nullable=False
    )

    note = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# Installment Balance
# ============================================================

class InstallmentBalance(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    year = db.Column(
        db.Integer,
        nullable=False
    )

    opening_balance = db.Column(
        db.Integer,
        default=0
    )

    jan = db.Column(db.Integer, default=0)
    feb = db.Column(db.Integer, default=0)
    mar = db.Column(db.Integer, default=0)
    apr = db.Column(db.Integer, default=0)
    may = db.Column(db.Integer, default=0)
    jun = db.Column(db.Integer, default=0)
    jul = db.Column(db.Integer, default=0)
    aug = db.Column(db.Integer, default=0)
    sep = db.Column(db.Integer, default=0)
    oct = db.Column(db.Integer, default=0)
    nov = db.Column(db.Integer, default=0)
    dec = db.Column(db.Integer, default=0)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="installments"
    )


# ============================================================
# Expense
# ============================================================

class Expense(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    expense_date = db.Column(
        db.Date,
        nullable=False
    )

    amount = db.Column(
        db.Integer,
        nullable=False
    )

    note = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# Other Income
# ============================================================

class OtherIncome(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    income_date = db.Column(
        db.Date,
        nullable=False
    )

    amount = db.Column(
        db.Integer,
        nullable=False
    )

    note = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# Transaction Ledger
# ============================================================

class Transaction(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tx_date = db.Column(
        db.Date,
        nullable=False
    )

    tx_type = db.Column(
        db.String(50),
        nullable=False
    )

    amount = db.Column(
        db.Integer,
        nullable=False
    )

    note = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# Login Loader
# ============================================================

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# ============================================================
# Helpers
# ============================================================

def money(value):

    try:
        return f"{int(value):,}"

    except (TypeError, ValueError):
        return "0"


app.jinja_env.filters["money"] = money


def parse_date(value):

    return datetime.strptime(
        value,
        "%Y-%m-%d"
    ).date()


def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if (
            not current_user.is_authenticated
            or current_user.role != "admin"
        ):

            flash("Admin権限が必要です。")

            return redirect(
                url_for("dashboard")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


def create_transaction(
    transaction_type,
    amount,
    note
):

    transaction = Transaction(

        tx_date=date.today(),

        tx_type=transaction_type,

        amount=int(amount),

        note=note

    )

    db.session.add(transaction)


def loan_repaid(loan):

    return sum(
        repayment.amount
        for repayment in loan.repayments
    )


def installment_total(item):

    return (
        item.opening_balance
        + item.jan
        + item.feb
        + item.mar
        + item.apr
        + item.may
        + item.jun
        + item.jul
        + item.aug
        + item.sep
        + item.oct
        + item.nov
        + item.dec
    )


# ============================================================
# Fixed Initial Admin
# ============================================================

def ensure_admin():

    admin_email = "admin@test.com"
    admin_password = "admin123"
    admin_name = "Sudip"

    existing_admin = User.query.filter_by(
        email=admin_email
    ).first()

    if existing_admin:

        existing_admin.name = admin_name
        existing_admin.role = "admin"
        existing_admin.is_active_user = True

        if not existing_admin.check_password(
            admin_password
        ):

            existing_admin.set_password(
                admin_password
            )

        db.session.commit()

        return

    admin = User(

        name=admin_name,

        email=admin_email,

        role="admin",

        is_active_user=True

    )

    admin.set_password(
        admin_password
    )

    db.session.add(admin)

    db.session.commit()


# ============================================================
# Before Request
# ============================================================

@app.before_request
def before_request():

    db.create_all()

    ensure_admin()


# ============================================================
# Index
# ============================================================

@app.route("/")
def index():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# ============================================================
# Setup DB
# ============================================================

@app.route("/setup-db")
def setup_db():

    db.create_all()

    ensure_admin()

    return "Database and Admin created successfully."


# ============================================================
# Init Admin
# ============================================================

@app.route("/init-admin")
def init_admin():

    ensure_admin()

    return "Admin initialized successfully."


# ============================================================
# Login
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = (
            request.form.get("email")
            or ""
        ).strip().lower()

        password = (
            request.form.get("password")
            or ""
        )

        user = User.query.filter_by(
            email=email,
            is_active_user=True
        ).first()

        if (
            user
            and user.check_password(password)
        ):

            login_user(user)

            return redirect(
                url_for("dashboard")
            )

        flash(
            "メールアドレスまたはパスワードが違います。"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# Logout
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# ============================================================
# Dashboard
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    try:

        selected_year = int(
            request.args.get(
                "year",
                datetime.now().year
            )
        )

    except (TypeError, ValueError):

        selected_year = datetime.now().year


    if current_user.role == "admin":

        users = User.query.filter_by(
            is_active_user=True
        ).order_by(
            User.name
        ).all()

    else:

        users = [current_user]


    all_users = User.query.order_by(
        User.name
    ).all()


    user_ids = [
        user.id
        for user in users
    ]


    plans = CollectionPlan.query.filter(

        CollectionPlan.user_id.in_(
            user_ids
        ),

        CollectionPlan.year == selected_year

    ).order_by(

        CollectionPlan.month

    ).all()


    if current_user.role == "admin":

        loans = Loan.query.order_by(
            Loan.loan_date.desc()
        ).all()

    else:

        loans = Loan.query.filter_by(
            borrower_id=current_user.id
        ).order_by(
            Loan.loan_date.desc()
        ).all()


    installments = InstallmentBalance.query.filter(

        InstallmentBalance.user_id.in_(
            user_ids
        ),

        InstallmentBalance.year == selected_year

    ).all()


    if current_user.role == "admin":

        transactions = Transaction.query.order_by(
            Transaction.id.desc()
        ).limit(50).all()

    else:

        transactions = []


    months = list(
        range(1, 13)
    )


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


            expected = (
                plan.expected_amount
                if plan
                else 0
            )


            paid = (
                sum(
                    payment.paid_amount
                    for payment in plan.payments
                )
                if plan
                else 0
            )


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
        payment.paid_amount
        for payment in CollectionPayment.query.all()
    )


    total_loan_disbursement = sum(
        loan.amount
        for loan in Loan.query.all()
    )


    total_loan_repayment = sum(
        repayment.amount
        for repayment in LoanRepayment.query.all()
    )


    total_expenses = sum(
        expense.amount
        for expense in Expense.query.all()
    )


    total_other_income = sum(
        income.amount
        for income in OtherIncome.query.all()
    )


    cash_in_hand = (
        total_collections
        + total_loan_repayment
        - total_loan_disbursement
        + total_other_income
        - total_expenses
    )


    outstanding_loans = sum(

        max(
            0,
            loan.amount - loan_repaid(loan)
        )

        for loan in Loan.query.all()

    )


    unpaid_collections = sum(

        max(
            0,
            cell["expected"] - cell["paid"]
        )

        for row in collection_matrix

        for cell in row["months"].values()

    )


    return render_template(

        "dashboard.html",

        year=selected_year,

        users=users,

        all_users=all_users,

        plans=plans,

        loans=loans,

        installments=installments,

        transactions=transactions,

        months=months,

        collection_matrix=collection_matrix,

        cash_in_hand=cash_in_hand,

        total_collections=total_collections,

        total_loan_disbursement=total_loan_disbursement,

        total_loan_repayment=total_loan_repayment,

        total_expenses=total_expenses,

        total_other_income=total_other_income,

        outstanding_loans=outstanding_loans,

        unpaid_collections=unpaid_collections,

        loan_repaid=loan_repaid,

        installment_total=installment_total

    )


# ============================================================
# Add User
# ============================================================

@app.route(
    "/users/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_user():

    name = (
        request.form.get("name")
        or ""
    ).strip()

    email = (
        request.form.get("email")
        or ""
    ).strip().lower()

    password = (
        request.form.get("password")
        or ""
    )

    role = request.form.get(
        "role",
        "user"
    )


    if not name or not email or not password:

        flash(
            "Name、Email、Passwordは必須です。"
        )

        return redirect(
            url_for("dashboard")
        )


    if role not in ("admin", "user"):

        role = "user"


    existing_user = User.query.filter_by(
        email=email
    ).first()


    if existing_user:

        flash(
            "このEmailは既に登録されています。"
        )

        return redirect(
            url_for("dashboard")
        )


    user = User(

        name=name,

        email=email,

        role=role,

        is_active_user=True

    )


    user.set_password(
        password
    )


    db.session.add(user)

    db.session.commit()


    flash(
        "ユーザーを追加しました。"
    )


    return redirect(
        url_for("dashboard")
    )


# ============================================================
# Deactivate User
# ============================================================

@app.route(
    "/users/deactivate/<int:user_id>",
    methods=["POST"]
)
@login_required
@admin_required
def deactivate_user(user_id):

    user = db.session.get(
        User,
        user_id
    )


    if not user:

        flash(
            "ユーザーが見つかりません。"
        )

        return redirect(
            url_for("dashboard")
        )


    if user.id == current_user.id:

        flash(
            "自分自身は無効化できません。"
        )

        return redirect(
            url_for("dashboard")
        )


    user.is_active_user = False

    db.session.commit()


    flash(
        "ユーザーを無効化しました。"
    )


    return redirect(
        url_for("dashboard")
    )


# ============================================================
# Add Collection Plan
# ============================================================

@app.route(
    "/collection-plan/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_collection_plan():

    user_id = int(
        request.form.get("user_id")
    )

    year = int(
        request.form.get("year")
    )

    month = int(
        request.form.get("month")
    )

    expected_amount = int(
        request.form.get("expected_amount")
    )


    if month < 1 or month > 12:

        flash(
            "Monthは1～12で入力してください。"
        )

        return redirect(
            url_for(
                "dashboard",
                year=year
            )
        )


    if expected_amount < 0:

        flash(
            "Expected Amountは0以上で入力してください。"
        )

        return redirect(
            url_for(
                "dashboard",
                year=year
            )
        )


    existing_plan = CollectionPlan.query.filter_by(

        user_id=user_id,

        year=year,

        month=month

    ).first()


    if existing_plan:

        flash(
            "このユーザーの同じ年月の集金予定は既に存在します。"
        )

        return redirect(
            url_for(
                "dashboard",
                year=year
            )
        )


    plan = CollectionPlan(

        user_id=user_id,

        year=year,

        month=month,

        expected_amount=expected_amount

    )


    db.session.add(plan)

    db.session.commit()


    flash(
        "集金予定を追加しました。"
    )


    return redirect(
        url_for(
            "dashboard",
            year=year
        )
    )


# ============================================================
# Add Collection Payment
# ============================================================

@app.route(
    "/collection-payment/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_collection_payment():

    plan_id = int(
        request.form.get("plan_id")
    )

    plan = db.session.get(
        CollectionPlan,
        plan_id
    )


    if not plan:

        flash(
            "集金予定が見つかりません。"
        )

        return redirect(
            url_for("dashboard")
        )


    paid_amount = int(
        request.form.get("paid_amount")
    )


    if paid_amount <= 0:

        flash(
            "支払額は1以上で入力してください。"
        )

        return redirect(
            url_for(
                "dashboard",
                year=plan.year
            )
        )


    payment = CollectionPayment(

        plan_id=plan.id,

        paid_amount=paid_amount,

        paid_date=parse_date(
            request.form.get(
                "paid_date"
            )
        ),

        note=request.form.get(
            "note"
        )

    )


    db.session.add(payment)


    create_transaction(

        "collection_payment",

        payment.paid_amount,

        (
            f"{plan.user.name} "
            f"{plan.year}/{plan.month} "
            f"Collection"
        )

    )


    db.session.commit()


    flash(
        "支払いを登録しました。"
    )


    return redirect(
        url_for(
            "dashboard",
            year=plan.year
        )
    )


# ============================================================
# Add Loan
# ============================================================

@app.route(
    "/loan/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_loan():

    loan_amount = int(
        request.form.get("amount")
    )


    if loan_amount <= 0:

        flash(
            "Loan Amountは1以上で入力してください。"
        )

        return redirect(
            url_for("dashboard")
        )


    loan = Loan(

        borrower_id=int(
            request.form.get(
                "borrower_id"
            )
        ),

        loan_date=parse_date(
            request.form.get(
                "loan_date"
            )
        ),

        amount=loan_amount,

        note=request.form.get(
            "note"
        ),

        is_closed=False

    )


    db.session.add(loan)


    create_transaction(

        "loan_disbursement",

        -loan.amount,

        "Loan disbursement"

    )


    db.session.commit()


    flash(
        "Loanを登録しました。"
    )


    return redirect(
        url_for("dashboard")
    )


# ============================================================
# Add Loan Repayment
# ============================================================

@app.route(
    "/loan-repayment/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_loan_repayment():

    loan_id = int(
        request.form.get("loan_id")
    )

    loan = db.session.get(
        Loan,
        loan_id
    )


    if not loan:

        flash(
            "Loanが見つかりません。"
        )

        return redirect(
            url_for("dashboard")
        )


    repayment_amount = int(
        request.form.get("amount")
    )


    remaining = (
        loan.amount
        - loan_repaid(loan)
    )


    if repayment_amount <= 0:

        flash(
            "返済額は1以上で入力してください。"
        )

        return redirect(
            url_for("dashboard")
        )


    if repayment_amount > remaining:

        flash(
            "返済額がLoan Remainingを超えています。"
        )

        return redirect(
            url_for("dashboard")
        )


    repayment = LoanRepayment(

        loan_id=loan.id,

        repayment_date=parse_date(
            request.form.get(
                "repayment_date"
            )
        ),

        amount=repayment_amount,

        note=request.form.get(
            "note"
        )

    )


    db.session.add(repayment)


    create_transaction(

        "loan_repayment",

        repayment.amount,

        (
            "Loan repayment from "
            f"{loan.borrower.name}"
        )

    )


    if repayment_amount == remaining:

        loan.is_closed = True


    db.session.commit()


    flash(
        "Loan返済を登録しました。"
    )


    return redirect(
        url_for("dashboard")
    )


# ============================================================
# Add / Update Installment
# ============================================================

@app.route(
    "/installment/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_installment():

    user_id = int(
        request.form.get("user_id")
    )

    year = int(
        request.form.get("year")
    )


    month_names = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec"
    ]


    values = {

        month: int(
            request.form.get(
                month,
                0
            )
            or 0
        )

        for month in month_names

    }


    opening_balance = int(
        request.form.get(
            "opening_balance",
            0
        )
        or 0
    )


    existing = InstallmentBalance.query.filter_by(

        user_id=user_id,

        year=year

    ).first()


    if existing:

        existing.opening_balance = opening_balance


        for month in month_names:

            setattr(
                existing,
                month,
                values[month]
            )

    else:

        installment = InstallmentBalance(

            user_id=user_id,

            year=year,

            opening_balance=opening_balance,

            **values

        )


        db.session.add(
            installment
        )


    db.session.commit()


    flash(
        "Installmentを保存しました。"
    )


    return redirect(
        url_for(
            "dashboard",
            year=year
        )
    )


# ============================================================
# Add Expense
# ============================================================

@app.route(
    "/expense/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_expense():

    amount = int(
        request.form.get("amount")
    )


    if amount <= 0:

        flash(
            "Expense Amountは1以上で入力してください。"
        )

        return redirect(
            url_for("dashboard")
        )


    expense = Expense(

        expense_date=parse_date(
            request.form.get(
                "expense_date"
            )
        ),

        amount=amount,

        note=request.form.get(
            "note"
        )

    )


    db.session.add(expense)


    create_transaction(

        "expense",

        -expense.amount,

        expense.note
        or "Expense"

    )


    db.session.commit()


    flash(
        "支出を登録しました。"
    )


    return redirect(
        url_for("dashboard")
    )


# ============================================================
# Add Other Income
# ============================================================

@app.route(
    "/income/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_income():

    amount = int(
        request.form.get("amount")
    )


    if amount <= 0:

        flash(
            "Income Amountは1以上で入力してください。"
        )

        return redirect(
            url_for("dashboard")
        )


    income = OtherIncome(

        income_date=parse_date(
            request.form.get(
                "income_date"
            )
        ),

        amount=amount,

        note=request.form.get(
            "note"
        )

    )


    db.session.add(income)


    create_transaction(

        "other_income",

        income.amount,

        income.note
        or "Other Income"

    )


    db.session.commit()


    flash(
        "その他収入を登録しました。"
    )


    return redirect(
        url_for("dashboard")
    )


# ============================================================
# Application Start
# ============================================================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        ensure_admin()

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )
