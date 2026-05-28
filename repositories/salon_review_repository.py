from __future__ import annotations
from database.connection import Database
from models.salon_review import SalonReview


class SalonReviewRepository:

    @staticmethod
    def create(
        appointment_id: int,
        customer_id: int,
        salon_id: int,
        rating: int,
        comment: str | None,
    ) -> int:
        conn = Database.get_connection()
        cur = conn.execute(
            """
            INSERT INTO salon_reviews
                (appointment_id, customer_id, salon_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
            """,
            (appointment_id, customer_id, salon_id, rating, comment),
        )
        conn.commit()
        return cur.lastrowid

    @staticmethod
    def exists_for_appointment(appointment_id: int) -> bool:
        row = Database.get_connection().execute(
            "SELECT COUNT(*) FROM salon_reviews WHERE appointment_id = ?",
            (appointment_id,),
        ).fetchone()
        return (row[0] if row else 0) > 0

    @staticmethod
    def get_by_salon(salon_id: int) -> list[SalonReview]:
        rows = Database.get_connection().execute(
            "SELECT * FROM salon_reviews WHERE salon_id = ? ORDER BY created_at DESC",
            (salon_id,),
        ).fetchall()
        return [
            SalonReview(
                id=r["id"],
                appointment_id=r["appointment_id"],
                customer_id=r["customer_id"],
                salon_id=r["salon_id"],
                rating=r["rating"],
                comment=r["comment"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
