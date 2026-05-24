from __future__ import annotations
from database.connection import Database
from models.service import Service
from repositories.service_repository import ServiceRepository


class SalonServiceRepository:

    @staticmethod
    def get_assigned(salon_id: int) -> list[Service]:
        rows = Database.get_connection().execute(
            """
            SELECT s.id, s.name, s.description, s.duration_min, s.price, s.is_active
              FROM services s
              JOIN salon_services ss ON ss.service_id = s.id
             WHERE ss.salon_id = ?
             ORDER BY s.name
            """,
            (salon_id,),
        ).fetchall()
        return [ServiceRepository._to_model(r) for r in rows]

    @staticmethod
    def get_available(salon_id: int) -> list[Service]:
        rows = Database.get_connection().execute(
            """
            SELECT s.id, s.name, s.description, s.duration_min, s.price, s.is_active
              FROM services s
             WHERE s.is_active = 1
               AND s.id NOT IN (
                   SELECT service_id FROM salon_services WHERE salon_id = ?
               )
             ORDER BY s.name
            """,
            (salon_id,),
        ).fetchall()
        return [ServiceRepository._to_model(r) for r in rows]

    @staticmethod
    def add(salon_id: int, service_id: int) -> None:
        conn = Database.get_connection()
        conn.execute(
            "INSERT OR IGNORE INTO salon_services (salon_id, service_id) VALUES (?, ?)",
            (salon_id, service_id),
        )
        conn.commit()

    @staticmethod
    def remove(salon_id: int, service_id: int) -> None:
        conn = Database.get_connection()
        conn.execute(
            "DELETE FROM salon_services WHERE salon_id = ? AND service_id = ?",
            (salon_id, service_id),
        )
        conn.commit()
