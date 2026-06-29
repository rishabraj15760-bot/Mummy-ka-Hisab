import sqlite3

conn = sqlite3.connect("expenses.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    note TEXT,
    date TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS budget(
    id INTEGER PRIMARY KEY,
    amount REAL
)
""")

cursor.execute("SELECT * FROM budget")

if cursor.fetchone() is None:
    cursor.execute(
        "INSERT INTO budget (id, amount) VALUES (1, 0)"
    )

conn.commit()
conn.close()

print("Database created successfully!")