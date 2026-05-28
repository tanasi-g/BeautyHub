from __future__ import annotations
import sqlite3
from database.connection import Database
from models.user import User


class UserRepository:

    @staticmethod
    def find_by_username(username: str) -> sqlite3.Row | None:
        return Database.get_connection().execute(
            """
            SELECT u.id, u.username, u.email, u.password_hash,
                   u.first_name, u.last_name, u.phone, u.is_active, u.salon_id,
                   r.name AS role_name, r.display_name AS role_display
              FROM users u
              JOIN roles r ON r.id = u.role_id
             WHERE u.username = ?
            """,
            (username,),
        ).fetchone()

    @staticmethod
    def exists_username(username: str) -> bool:
        return bool(
            Database.get_connection()
            .execute("SELECT 1 FROM users WHERE username = ?", (username,))
            .fetchone()
        )

    @staticmethod
    def exists_email(email: str) -> bool:
        return bool(
            Database.get_connection()
            .execute("SELECT 1 FROM users WHERE email = ?", (email,))
            .fetchone()
        )

    @staticmethod
    def get_role_id(role_name: str) -> int:
        row = Database.get_connection().execute(
            "SELECT id FROM roles WHERE name = ?", (role_name,)
        ).fetchone()
        return row["id"]

    @staticmethod
    def create(
        username: str,
        email: str,
        pw_hash: str,
        first_name: str,
        last_name: str,
        phone: str | None,
        role_id: int,
    ) -> int:
        conn = Database.get_connection()
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, first_name, last_name, phone, role_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (username, email, pw_hash, first_name, last_name, phone, role_id),
        )
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def count() -> int:
        return Database.get_connection().execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

    @staticmethod
    def get_all() -> list[sqlite3.Row]:
        return Database.get_connection().execute(
            """
            SELECT u.id, u.username, u.email, r.display_name, u.is_active
              FROM users u
              JOIN roles r ON r.id = u.role_id
             ORDER BY u.id
            """
        ).fetchall()


    @staticmethod
    def row_to_user(row: sqlite3.Row) -> User:
        keys = row.keys() if hasattr(row, "keys") else []
        salon_id = row["salon_id"] if "salon_id" in keys else None
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            phone=row["phone"],
            role_name=row["role_name"],
            role_display=row["role_display"],
            is_active=bool(row["is_active"]),
            salon_id=salon_id,
        )
