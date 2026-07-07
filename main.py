import os
from datetime import date, datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///monthly_manager.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# =========================
# Models
# =========================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CollectionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    expected_amount = db.Column(db.Integer, nullable=False)
    user = db.relationship("User")


class CollectionPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("collection_plan.id"), nullable=False)
    paid_amount = db.Column(db.Integer, nullable=False)
    paid_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    plan = db.relationship("CollectionPlan")


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    loan_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255))
    borrower = db.relationship("User")


class LoanRepayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loan.id"), nullable=False)
    repayment_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255))
    loan = db.relationship("Loan")


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_date = db.Column(db.Date, nullable=False)
    tx_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================
# Helpers
# =========================

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Admin権限が必要です。")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)
    return wrapper


def money(value):
    return f"{value:,}"


app.jinja_env.filters["money"] = money


def create_transaction(tx_type, amount, note):
    tx = Transaction(
        tx_date=date.today(),
        tx_type=tx_type,
        amount=amount,
        note=note
    )
    db.session.add(tx)


# =========================
# Routes
# =========================

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/init-admin")
def init_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@test.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin_name = os.environ.get("ADMIN_NAME", "Admin")

    if User.query.filter_by(email=admin_email).first():
        return "Admin already exists."

    user = User(
        name=admin_name,
        email=admin_email,
        role="admin"
    )
    user.set_password(admin_password)
    db.session.add(user)
    db.session.commit()

    return f"Admin created: {admin_email}"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, is_active_user=True).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("メールまたはパスワードが違います。")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    users = User.query.filter_by(is_active_user=True).all()

    if current_user.role == "admin":
        plans = CollectionPlan.query.all()
        loans = Loan.query.all()
        transactions = Transaction.query.order_by(Transaction.id.desc()).limit(20).all()
    else:
        plans = CollectionPlan.query.filter_by(user_id=current_user.id).all()
        loans = Loan.query.filter_by(borrower_id=current_user.id).all()
        transactions = []

    total_collections = sum(
        p.paid_amount for p in CollectionPayment.query.all()
    )

    total_loan_disbursement = sum(l.amount for l in Loan.query.all())
    total_loan_repayment = sum(r.amount for r in LoanRepayment.query.all())

    cash_in_hand = total_collections + total_loan_repayment - total_loan_disbursement

    return render_template(
        "dashboard.html",
        users=users,
        plans=plans,
        loans=loans,
        transactions=transactions,
        cash_in_hand=cash_in_hand,
        total_collections=total_collections,
        total_loan_disbursement=total_loan_disbursement,
        total_loan_repayment=total_loan_repayment,
    )


@app.route("/users/add", methods=["POST"])
@login_required
@admin_required
def add_user():
    user = User(
        name=request.form["name"],
        email=request.form["email"],
        role=request.form["role"]
    )
    user.set_password(request.form["password"])
    db.session.add(user)
    db.session.commit()
    flash("ユーザーを追加しました。")
    return redirect(url_for("dashboard"))


@app.route("/collection-plan/add", methods=["POST"])
@login_required
@admin_required
def add_collection_plan():
    plan = CollectionPlan(
        user_id=request.form["user_id"],
        year=int(request.form["year"]),
        month=int(request.form["month"]),
        expected_amount=int(request.form["expected_amount"])
    )
    db.session.add(plan)
    db.session.commit()
    flash("集金予定を追加しました。")
    return redirect(url_for("dashboard"))


@app.route("/collection-payment/add", methods=["POST"])
@login_required
@admin_required
def add_collection_payment():
    plan = CollectionPlan.query.get_or_404(int(request.form["plan_id"]))

    payment = CollectionPayment(
        plan_id=plan.id,
        paid_amount=int(request.form["paid_amount"]),
        paid_date=datetime.strptime(request.form["paid_date"], "%Y-%m-%d").date(),
        note=request.form.get("note")
    )

    db.session.add(payment)
    create_transaction(
        "collection_payment",
        payment.paid_amount,
        f"{plan.user.name} collection payment"
    )
    db.session.commit()

    flash("支払いを登録しました。")
    return redirect(url_for("dashboard"))


@app.route("/loan/add", methods=["POST"])
@login_required
@admin_required
def add_loan():
    loan = Loan(
        borrower_id=request.form["borrower_id"],
        loan_date=datetime.strptime(request.form["loan_date"], "%Y-%m-%d").date(),
        amount=int(request.form["amount"]),
        note=request.form.get("note")
    )

    db.session.add(loan)
    create_transaction(
        "loan_disbursement",
        -loan.amount,
        "Loan disbursement"
    )
    db.session.commit()

    flash("Loanを登録しました。")
    return redirect(url_for("dashboard"))


@app.route("/loan-repayment/add", methods=["POST"])
@login_required
@admin_required
def add_loan_repayment():
    loan = Loan.query.get_or_404(int(request.form["loan_id"]))

    repayment = LoanRepayment(
        loan_id=loan.id,
        repayment_date=datetime.strptime(request.form["repayment_date"], "%Y-%m-%d").date(),
        amount=int(request.form["amount"]),
        note=request.form.get("note")
    )

    db.session.add(repayment)
    create_transaction(
        "loan_repayment",
        repayment.amount,
        f"Loan repayment from {loan.borrower.name}"
    )
    db.session.commit()

    flash("Loan返済を登録しました。")
    return redirect(url_for("dashboard"))


@app.route("/setup-db")
def setup_db():
    db.create_all()
    return "Database created."


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
