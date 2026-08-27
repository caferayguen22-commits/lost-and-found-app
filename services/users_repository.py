from services.db import get_connection
from models.user import User


def insert_user(user: User) -> User:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (user.email, user.password_hash)
        )
        connection.commit()
        new_id = cursor.lastrowid
        row = connection.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()
        return User.from_row(row)
    finally:
        connection.close()


def get_user_by_email(email: str) -> User | None:
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return User.from_row(row) if row else None
    finally:
        connection.close()


def get_user_by_id(user_id: int) -> User | None:
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return User.from_row(row) if row else None
    finally:
        connection.close()
