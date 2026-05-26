from __future__ import annotations
from database.connection import Database
from models.inventory import Inventory, InventoryLine


class InventoryRepository:

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _row_to_line(r) -> InventoryLine:
        return InventoryLine(
            id=r["id"],
            inventory_id=r["inventory_id"],
            product_id=r["product_id"],
            product_name=r["product_name"],
            system_qty=r["system_qty"],
            actual_qty=r["actual_qty"],
            deviation=r["deviation"],
        )

    @staticmethod
    def _load_lines(conn, inv_id: int) -> list[InventoryLine]:
        rows = conn.execute(
            "SELECT * FROM inventory_lines WHERE inventory_id = ? ORDER BY product_name",
            (inv_id,),
        ).fetchall()
        return [InventoryRepository._row_to_line(r) for r in rows]

    @staticmethod
    def _row_to_inv(row, lines: list[InventoryLine]) -> Inventory:
        return Inventory(
            id=row["id"],
            status=row["status"],
            inv_type=row["inv_type"],
            filter_kw=row["filter_kw"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            lines=lines,
        )

    # ---------------------------------------------------------------- write
    @staticmethod
    def create(inv_type: str, filter_kw: str | None = None) -> int:
        conn = Database.get_connection()
        cur = conn.execute(
            "INSERT INTO inventories (status, inv_type, filter_kw) VALUES ('draft', ?, ?)",
            (inv_type, filter_kw),
        )
        conn.commit()
        return cur.lastrowid

    @staticmethod
    def add_lines(inv_id: int, products: list[dict]) -> list[InventoryLine]:
        """Εισάγει γραμμές για νέα απογραφή· επιστρέφει τα αντικείμενα με ids."""
        conn = Database.get_connection()
        lines: list[InventoryLine] = []
        for p in products:
            cur = conn.execute(
                "INSERT INTO inventory_lines "
                "(inventory_id, product_id, product_name, system_qty, actual_qty, deviation) "
                "VALUES (?, ?, ?, ?, 0, 0)",
                (inv_id, p["id"], p["name"], p["stock"]),
            )
            lines.append(InventoryLine(
                id=cur.lastrowid,
                inventory_id=inv_id,
                product_id=p["id"],
                product_name=p["name"],
                system_qty=p["stock"],
                actual_qty=0,
                deviation=0,
            ))
        conn.commit()
        return lines

    @staticmethod
    def update_lines(inv_id: int, actual_qtys: dict[int, int]) -> None:
        """Ενημερώνει actual_qty και deviation ανά line_id."""
        conn = Database.get_connection()
        for line_id, actual in actual_qtys.items():
            row = conn.execute(
                "SELECT system_qty FROM inventory_lines WHERE id = ? AND inventory_id = ?",
                (line_id, inv_id),
            ).fetchone()
            if row:
                deviation = actual - row["system_qty"]
                conn.execute(
                    "UPDATE inventory_lines SET actual_qty = ?, deviation = ? WHERE id = ?",
                    (actual, deviation, line_id),
                )
        conn.commit()

    @staticmethod
    def finalize(inv_id: int) -> None:
        """Ολοκλήρωση: ενημερώνει stocks προϊόντων + θέτει status='completed'."""
        conn = Database.get_connection()
        lines = InventoryRepository._load_lines(conn, inv_id)
        for line in lines:
            conn.execute(
                "UPDATE products SET stock = ? WHERE id = ?",
                (line.actual_qty, line.product_id),
            )
        conn.execute(
            "UPDATE inventories SET status = 'completed', "
            "completed_at = datetime('now', 'localtime') WHERE id = ?",
            (inv_id,),
        )
        conn.commit()

    @staticmethod
    def cancel(inv_id: int) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE inventories SET status = 'cancelled' WHERE id = ?", (inv_id,)
        )
        conn.commit()

    # ---------------------------------------------------------------- read
    @staticmethod
    def get_by_id(inv_id: int) -> Inventory | None:
        conn = Database.get_connection()
        row = conn.execute(
            "SELECT * FROM inventories WHERE id = ?", (inv_id,)
        ).fetchone()
        if not row:
            return None
        lines = InventoryRepository._load_lines(conn, inv_id)
        return InventoryRepository._row_to_inv(row, lines)

    @staticmethod
    def get_all() -> list[Inventory]:
        conn = Database.get_connection()
        rows = conn.execute(
            "SELECT * FROM inventories ORDER BY created_at DESC"
        ).fetchall()
        result = []
        for row in rows:
            lines = InventoryRepository._load_lines(conn, row["id"])
            result.append(InventoryRepository._row_to_inv(row, lines))
        return result

    @staticmethod
    def get_draft() -> Inventory | None:
        conn = Database.get_connection()
        row = conn.execute(
            "SELECT * FROM inventories WHERE status = 'draft' "
            "ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        lines = InventoryRepository._load_lines(conn, row["id"])
        return InventoryRepository._row_to_inv(row, lines)
