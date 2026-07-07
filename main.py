from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

DB = "database.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        month TEXT NOT NULL,
        amount INTEGER NOT NULL,
        type TEXT NOT NULL,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        loan_amount INTEGER NOT NULL,
        paid_amount INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    admin = cur.execute(
        "SELECT * FROM users WHERE email=?",
        ("admin@test.com",)
    ).fetchone()

    if not admin:
        cur.execute("""
        INSERT INTO users (name, email, password, role)
        VALUES (?, ?, ?, ?)
        """, (
            "Admin",
            "admin@test.com",
            generate_password_hash("admin123"),
            "admin"
        ))

    conn.commit()
    conn.close()


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    if session["role"] == "admin":
        return redirect("/admin")

    return redirect("/user")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect("/")

        return "メールまたはパスワードが違います"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()

    users = conn.execute("SELECT * FROM users").fetchall()

    payments = conn.execute("""
        SELECT payments.*, users.name
        FROM payments
        JOIN users ON payments.user_id = users.id
        ORDER BY payments.year DESC, payments.month DESC
    """).fetchall()

    loans = conn.execute("""
        SELECT loans.*, users.name,
        loan_amount - paid_amount AS remaining
        FROM loans
        JOIN users ON loans.user_id = users.id
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        payments=payments,
        loans=loans
    )


@app.route("/user")
def user_page():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    payments = conn.execute("""
        SELECT * FROM payments
        WHERE user_id=?
        ORDER BY year DESC, month DESC
    """, (session["user_id"],)).fetchall()

    loans = conn.execute("""
        SELECT *, loan_amount - paid_amount AS remaining
        FROM loans
        WHERE user_id=?
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "user.html",
        payments=payments,
        loans=loans
    )


@app.route("/add_user", methods=["POST"])
def add_user():
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    conn.execute("""
    INSERT INTO users (name, email, password, role)
    VALUES (?, ?, ?, ?)
    """, (
        request.form["name"],
        request.form["email"],
        generate_password_hash(request.form["password"]),
        request.form["role"]
    ))

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/add_payment", methods=["POST"])
def add_payment():
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    conn.execute("""
    INSERT INTO payments (user_id, year, month, amount, type, note)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        request.form["user_id"],
        request.form["year"],
        request.form["month"],
        request.form["amount"],
        request.form["type"],
        request.form["note"]
    ))

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/add_loan", methods=["POST"])
def add_loan():
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    conn.execute("""
    INSERT INTO loans (user_id, loan_amount, paid_amount)
    VALUES (?, ?, ?)
    """, (
        request.form["user_id"],
        request.form["loan_amount"],
        request.form["paid_amount"]
    ))

    conn.commit()
    conn.close()

    return redirect("/admin")


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
