import sqlite3
import hashlib

DB_NAME = "database/users.db"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(full_name, email, password, college, branch, graduation_year):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO users
        (full_name, email, password, college, branch, graduation_year)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            full_name,
            email,
            hash_password(password),
            college,
            branch,
            graduation_year
        ))

        conn.commit()
        conn.close()

        return True, "Registration Successful!"

    except sqlite3.IntegrityError:
        conn.close()
        return False, "Email already exists."


def login_user(email, password):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users
    WHERE email=? AND password=?
    """, (
        email,
        hash_password(password)
    ))

    user = cursor.fetchone()

    conn.close()

    return user