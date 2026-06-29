from flask import Flask, render_template, request, redirect
import sqlite3
app = Flask(__name__)

@app.route("/")
def home():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT amount FROM budget WHERE id=1")
    row = cursor.fetchone()

    if row:
        budget = row[0]
    else:
        budget = 0

    conn.close()

    if total is None:
        total = 0

    remaining = budget - total
    total = f"{total:,.0f}"
    budget = f"{budget:,.0f}"
    remaining = f"{remaining:,.0f}"
    return render_template("index.html", total=total, budget=budget, remaining = remaining)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        note = request.form["note"]

        conn = sqlite3.connect("expenses.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO expenses (amount, category, note, date) VALUES (?, ?, ?, date('now'))",
            (amount, category, note)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_expense.html")

@app.route("/history")
def history():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expenses ORDER BY id DESC")
    expenses = cursor.fetchall()

    conn.close()

    return render_template("history.html", expenses=expenses)
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/history")
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        note = request.form["note"]

        cursor.execute(
            "UPDATE expenses SET amount=?, category=?, note=? WHERE id=?",
            (amount, category, note, id)
        )

        conn.commit()
        conn.close()

        return redirect("/history")

    cursor.execute("SELECT * FROM expenses WHERE id=?", (id,))
    expense = cursor.fetchone()

    conn.close()

    return render_template("edit_expense.html", expense=expense)
@app.route("/budget", methods=["GET", "POST"])
def budget():

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    if request.method == "POST":

        amount = request.form["budget"]

        cursor.execute(
            "UPDATE budget SET amount=? WHERE id=1",
            (amount,)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    cursor.execute("SELECT amount FROM budget WHERE id=1")
    budget = cursor.fetchone()[0]

    conn.close()

    return render_template("budget.html", budget=budget)
if __name__ == "__main__":
    app.run(debug=True)