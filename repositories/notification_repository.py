from __future__ import annotations
from database.connection import Database
from models.notification import Notification


class NotificationRepository:

    @staticmethod
    def create(
        user_id: int,
        message: str,
        type: str = "info",
        appointment_id: int | None = None,
    ) -> int:
        conn = Database.get_connection()
        cur = conn.execute(
            "INSERT INTO notifications (user_id, message, type, appointment_id) "
            "VALUES (?, ?, ?, ?)",
            (user_id, message, type, appointment_id),
        )
        conn.commit()
        return cur.lastrowid

    @staticmethod
    def get_by_user(user_id: int) -> list[Notification]:
        rows = Database.get_connection().execute(
            """
            SELECT id, user_id, message, is_read, type, appointment_id, created_at
              FROM notifications
             WHERE user_id = ?
             ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [
            Notification(
                id=r["id"],
                user_id=r["user_id"],
                message=r["message"],
                is_read=bool(r["is_read"]),
                created_at=r["created_at"],
                type=r["type"] or "info",
                appointment_id=r["appointment_id"],
            )
            for r in rows
        ]

    @staticmethod
    def mark_read(notification_id: int) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,),
        )
        conn.commit()

    @staticmethod
    def mark_all_read(user_id: int) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()

    @staticmethod
    def count_unread(user_id: int) -> int:
        row = Database.get_connection().execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,),
        ).fetchone()
        return row[0] if row else 0

    @staticmethod
    def clear_type_for_appointment(appointment_id: int, type: str) -> None:
        """Διαγραφή τυχόν προηγούμενων ειδοποιήσεων ίδιου τύπου για το ραντεβού."""
        conn = Database.get_connection()
        conn.execute(
            "DELETE FROM notifications WHERE appointment_id = ? AND type = ?",
            (appointment_id, type),
        )
        conn.commit()
