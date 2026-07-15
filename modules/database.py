import sqlite3
import os

# Create database folder if it doesn't exist
os.makedirs("database", exist_ok=True)

conn = sqlite3.connect("database/users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    college TEXT,
    branch TEXT,
    graduation_year TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database created successfully!")