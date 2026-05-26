from __future__ import annotations
from database.connection import Database
from models.salon import Salon


class SalonRepository:

    @staticmethod
    def get_all() -> list[Salon]:
        rows = Database.get_connection().execute(
            "SELECT id, name, address, city, phone, email, is_active FROM salons ORDER BY name"
        ).fetchall()
        return [SalonRepository._to_model(r) for r in rows]

    @staticmethod
    def count() -> int:
        return Database.get_connection().execute(
            "SELECT COUNT(*) FROM salons"
        ).fetchone()[0]

    @staticmethod
    def get_by_id(salon_id: int) -> Salon | None:
        row = Database.get_connection().execute(
            "SELECT id, name, address, city, phone, email, is_active FROM salons WHERE id = ?",
            (salon_id,),
        ).fetchone()
        return SalonRepository._to_model(row) if row else None

    @staticmethod
    def search(
        name_kw: str = "",
        city_kw: str = "",
        service_id: int | None = None,
    ) -> list[Salon]:
        conn = Database.get_connection()
        nkw = f"%{name_kw.strip().casefold()}%" if name_kw.strip() else "%"
        ckw = f"%{city_kw.strip().casefold()}%" if city_kw.strip() else "%"

        if service_id is not None:
            rows = conn.execute(
                """
                SELECT DISTINCT s.id, s.name, s.address, s.city, s.phone, s.email, s.is_active
                  FROM salons s
                  JOIN salon_services ss ON ss.salon_id = s.id
                 WHERE s.is_active = 1
                   AND ss.service_id = ?
                   AND casefold(s.name) LIKE ?
                   AND casefold(s.city) LIKE ?
                 ORDER BY s.name
                """,
                (service_id, nkw, ckw),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, name, address, city, phone, email, is_active
                  FROM salons
                 WHERE is_active = 1
                   AND casefold(name) LIKE ?
                   AND casefold(city) LIKE ?
                 ORDER BY name
                """,
                (nkw, ckw),
            ).fetchall()

        return [SalonRepository._to_model(r) for r in rows]

    @staticmethod
    def create(name: str, address: str, city: str, phone: str | None, email: str | None) -> int:
        conn = Database.get_connection()
        cursor = conn.execute(
            "INSERT INTO salons (name, address, city, phone, email) VALUES (?, ?, ?, ?, ?)",
            (name, address, city, phone, email),
        )
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def set_active(salon_id: int, active: bool) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE salons SET is_active = ? WHERE id = ?",
            (1 if active else 0, salon_id),
        )
        conn.commit()

    @staticmethod
    def _to_model(row) -> Salon:
        return Salon(
            id=row["id"],
            name=row["name"],
            address=row["address"],
            city=row["city"],
            phone=row["phone"],
            email=row["email"],
            is_active=bool(row["is_active"]),
        )