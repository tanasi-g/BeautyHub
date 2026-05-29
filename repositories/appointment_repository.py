from __future__ import annotations
from database.connection import Database
from models.appointment import AppointmentDetail, EmployeeAppointmentDetail


class AppointmentRepository:

    @staticmethod
    def create(
        customer_id: int,
        employee_id: int,
        service_id: int,
        scheduled_at: str,
        notes: str | None = None,
        salon_id: int | None = None,
    ) -> int:
        conn = Database.get_connection()
        cur = conn.execute(
            "INSERT INTO appointments "
            "(customer_id, employee_id, service_id, scheduled_at, status, notes, salon_id) "
            "VALUES (?, ?, ?, ?, 'pending', ?, ?)",
            (customer_id, employee_id, service_id, scheduled_at, notes, salon_id),
        )
        conn.commit()
        return cur.lastrowid

    @staticmethod
    def get_by_customer(customer_id: int) -> list[AppointmentDetail]:
        rows = Database.get_connection().execute(
            """
            SELECT a.id, a.service_id, a.employee_id, a.scheduled_at, a.status, a.notes,
                   a.salon_id,
                   s.name  AS service_name, s.duration_min, s.price,
                   u.first_name || ' ' || u.last_name AS employee_name,
                   sl.name AS salon_name
              FROM appointments a
              JOIN services s  ON s.id  = a.service_id
              JOIN users    u  ON u.id  = a.employee_id
              LEFT JOIN salons sl ON sl.id = a.salon_id
             WHERE a.customer_id = ?
             ORDER BY a.scheduled_at DESC
            """,
            (customer_id,),
        ).fetchall()
        return [AppointmentDetail(
            id=r["id"],
            service_id=r["service_id"],
            service_name=r["service_name"],
            duration_min=r["duration_min"],
            price=r["price"],
            employee_name=r["employee_name"],
            employee_id=r["employee_id"],
            scheduled_at=r["scheduled_at"],
            status=r["status"],
            notes=r["notes"],
            salon_id=r["salon_id"],
            salon_name=r["salon_name"],
        ) for r in rows]

    @staticmethod
    def has_overlap(employee_id: int, start_iso: str, end_iso: str) -> bool:
        """True if any non-cancelled appointment of the employee overlaps [start, end)."""
        count = Database.get_connection().execute(
            """
            SELECT COUNT(*) FROM appointments a
              JOIN services s ON s.id = a.service_id
             WHERE a.employee_id = ?
               AND a.status NOT IN ('cancelled')
               AND a.scheduled_at < ?
               AND datetime(a.scheduled_at, '+' || s.duration_min || ' minutes') > ?
            """,
            (employee_id, end_iso, start_iso),
        ).fetchone()[0]
        return count > 0

    @staticmethod
    def count(salon_id: int | None = None) -> int:
        if salon_id is not None:
            return Database.get_connection().execute(
                "SELECT COUNT(*) FROM appointments WHERE salon_id = ?",
                (salon_id,),
            ).fetchone()[0]
        return Database.get_connection().execute(
            "SELECT COUNT(*) FROM appointments"
        ).fetchone()[0]

    @staticmethod
    def get_all(salon_id: int | None = None) -> list[dict]:
        sql = """
            SELECT a.id, a.scheduled_at, a.status, a.notes, a.salon_id,
                   s.name  AS service_name, s.duration_min, s.price,
                   c.first_name || ' ' || c.last_name AS customer_name,
                   e.first_name || ' ' || e.last_name AS employee_name
              FROM appointments a
              JOIN services s ON s.id = a.service_id
              JOIN users    c ON c.id = a.customer_id
              JOIN users    e ON e.id = a.employee_id
            """
        params: tuple = ()
        if salon_id is not None:
            sql += " WHERE a.salon_id = ?"
            params = (salon_id,)
        sql += " ORDER BY a.scheduled_at DESC"
        rows = Database.get_connection().execute(sql, params).fetchall()
        return [
            {
                "id":            r["id"],
                "scheduled_at":  r["scheduled_at"],
                "status":        r["status"],
                "service_name":  r["service_name"],
                "duration_min":  r["duration_min"],
                "price":         r["price"],
                "customer_name": r["customer_name"],
                "employee_name": r["employee_name"],
                "notes":         r["notes"],
                "salon_id":      r["salon_id"],
            }
            for r in rows
        ]

    @staticmethod
    def get_by_employee(employee_id: int) -> list[EmployeeAppointmentDetail]:
        rows = Database.get_connection().execute(
            """
            SELECT a.id, a.customer_id, a.scheduled_at, a.status, a.notes,
                   s.name  AS service_name, s.duration_min, s.price,
                   u.first_name || ' ' || u.last_name AS customer_name
              FROM appointments a
              JOIN services s ON s.id = a.service_id
              JOIN users    u ON u.id = a.customer_id
             WHERE a.employee_id = ?
             ORDER BY a.scheduled_at ASC
            """,
            (employee_id,),
        ).fetchall()
        return [EmployeeAppointmentDetail(
            id=r["id"],
            service_name=r["service_name"],
            duration_min=r["duration_min"],
            price=r["price"],
            customer_name=r["customer_name"],
            customer_id=r["customer_id"],
            scheduled_at=r["scheduled_at"],
            status=r["status"],
            notes=r["notes"],
        ) for r in rows]

    @staticmethod
    def set_status(appt_id: int, status: str) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (status, appt_id),
        )
        conn.commit()

    @staticmethod
    def reschedule(appt_id: int, new_scheduled_at: str) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE appointments SET scheduled_at = ?, status = 'pending' WHERE id = ?",
            (new_scheduled_at, appt_id),
        )
        conn.commit()

    @staticmethod
    def has_overlap_excluding(
        employee_id: int, start_iso: str, end_iso: str, exclude_appt_id: int
    ) -> bool:
        """Like has_overlap but ignores a specific appointment (used when rescheduling)."""
        count = Database.get_connection().execute(
            """
            SELECT COUNT(*) FROM appointments a
              JOIN services s ON s.id = a.service_id
             WHERE a.employee_id = ?
               AND a.id != ?
               AND a.status NOT IN ('cancelled')
               AND a.scheduled_at < ?
               AND datetime(a.scheduled_at, '+' || s.duration_min || ' minutes') > ?
            """,
            (employee_id, exclude_appt_id, end_iso, start_iso),
        ).fetchone()[0]
        return count > 0

    @staticmethod
    def get_all_employees(salon_id: int | None = None) -> list[dict]:
        if salon_id is not None:
            rows = Database.get_connection().execute(
                """
                SELECT u.id, u.first_name || ' ' || u.last_name AS full_name
                  FROM users u
                  JOIN roles r ON r.id = u.role_id
                 WHERE r.name = 'employee'
                   AND u.is_active = 1
                   AND u.salon_id = ?
                 ORDER BY u.first_name, u.last_name
                """,
                (salon_id,),
            ).fetchall()
        else:
            rows = Database.get_connection().execute(
                """
                SELECT u.id, u.first_name || ' ' || u.last_name AS full_name
                  FROM users u
                  JOIN roles r ON r.id = u.role_id
                 WHERE r.name = 'employee' AND u.is_active = 1
                 ORDER BY u.first_name, u.last_name
                """,
            ).fetchall()
        return [{"id": r["id"], "name": r["full_name"]} for r in rows]
