from __future__ import annotations
from database.connection import Database
from models.service import Service


class ServiceRepository:

    @staticmethod
    def get_all() -> list[Service]:
        rows = Database.get_connection().execute(
            "SELECT id, name, description, duration_min, price, is_active FROM services ORDER BY name"
        ).fetchall()
        return [ServiceRepository._to_model(r) for r in rows]

    @staticmethod
    def count() -> int:
        return Database.get_connection().execute(
            "SELECT COUNT(*) FROM services"
        ).fetchone()[0]

    @staticmethod
    def get_by_id(service_id: int) -> Service | None:
        row = Database.get_connection().execute(
            "SELECT id, name, description, duration_min, price, is_active FROM services WHERE id = ?",
            (service_id,),
        ).fetchone()
        return ServiceRepository._to_model(row) if row else None

    @staticmethod
    def create(name: str, description: str | None, duration_min: int, price: float) -> int:
        conn = Database.get_connection()
        cursor = conn.execute(
            "INSERT INTO services (name, description, duration_min, price) VALUES (?, ?, ?, ?)",
            (name, description, duration_min, price),
        )
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def _to_model(row) -> Service:
        return Service(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            duration_min=row["duration_min"],
            price=row["price"],
            is_active=bool(row["is_active"]),
        )
