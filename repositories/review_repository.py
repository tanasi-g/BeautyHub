from __future__ import annotations
from database.connection import Database
from models.review import Review


class ReviewRepository:

    @staticmethod
    def create(
        appointment_id: int,
        customer_id: int,
        employee_id: int,
        service_id: int,
        rating: int,
        comment: str | None,
    ) -> int:
        conn = Database.get_connection()
        cur = conn.execute(
            """
            INSERT INTO reviews
                (appointment_id, customer_id, employee_id, service_id, rating, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (appointment_id, customer_id, employee_id, service_id, rating, comment),
        )
        conn.commit()
        return cur.lastrowid

    @staticmethod
    def exists_for_appointment(appointment_id: int) -> bool:
        row = Database.get_connection().execute(
            "SELECT COUNT(*) FROM reviews WHERE appointment_id = ?",
            (appointment_id,),
        ).fetchone()
        return (row[0] if row else 0) > 0

    @staticmethod
    def get_by_appointment(appointment_id: int) -> Review | None:
        row = Database.get_connection().execute(
            "SELECT * FROM reviews WHERE appointment_id = ?",
            (appointment_id,),
        ).fetchone()
        if not row:
            return None
        return Review(
            id=row["id"],
            appointment_id=row["appointment_id"],
            customer_id=row["customer_id"],
            employee_id=row["employee_id"],
            service_id=row["service_id"],
            rating=row["rating"],
            comment=row["comment"],
            created_at=row["created_at"],
        )

    @staticmethod
    def get_by_employee(employee_id: int) -> list[Review]:
        rows = Database.get_connection().execute(
            "SELECT * FROM reviews WHERE employee_id = ? ORDER BY created_at DESC",
            (employee_id,),
        ).fetchall()
        return [
            Review(
                id=r["id"],
                appointment_id=r["appointment_id"],
                customer_id=r["customer_id"],
                employee_id=r["employee_id"],
                service_id=r["service_id"],
                rating=r["rating"],
                comment=r["comment"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
