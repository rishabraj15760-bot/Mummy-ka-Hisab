from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2
from db import get_db_connection
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-this")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                (name, email, password_hash)
            )
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            cursor.close()
            conn.close()
            return render_template("signup.html", error="Email already registered")

        cursor.close()
        conn.close()
        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password_hash FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def home():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id=%s", (user_id,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT amount FROM budget WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()
    budget = row[0] if row else 0

    cursor.close()
    conn.close()

    if total is None:
        total = 0

    remaining = budget - total
    total = f"{total:,.0f}"
    budget = f"{budget:,.0f}"
    remaining = f"{remaining:,.0f}"

    return render_template("index.html", total=total, budget=budget, remaining=remaining)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        user_id = session["user_id"]
        amount = request.form["amount"]
        category = request.form["category"]
        note = request.form["note"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO expenses (amount, category, note, date, user_id) VALUES (%s, %s, %s, CURRENT_DATE, %s)",
            (amount, category, note, user_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/")

    return render_template("add_expense.html")


@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expenses WHERE user_id=%s ORDER BY id DESC;", (user_id,))
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("history.html", expenses=expenses)


@app.route("/delete/<int:id>")
@login_required
def delete(id):
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s", (id, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/history")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        note = request.form["note"]

        cursor.execute(
            "UPDATE expenses SET amount=%s, category=%s, note=%s WHERE id=%s AND user_id=%s",
            (amount, category, note, id, user_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/history")

    cursor.execute("SELECT * FROM expenses WHERE id=%s AND user_id=%s", (id, user_id))
    expense = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("edit_expense.html", expense=expense)


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        amount = request.form["budget"]

        cursor.execute(
            """
            INSERT INTO budget (amount, user_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET amount = EXCLUDED.amount
            """,
            (amount, user_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/")

    cursor.execute("SELECT amount FROM budget WHERE user_id=%s;", (user_id,))
    row = cursor.fetchone()
    budget_val = row[0] if row else 0
    cursor.close()
    conn.close()

    return render_template("budget.html", budget=budget_val)


if __name__ == "__main__":
    app.run(debug=True)
