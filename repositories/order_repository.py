from __future__ import annotations
from database.connection import Database
from models.order import Order, OrderItem


class OrderRepository:

    @staticmethod
    def create(customer_id: int, total_price: float, payment_method: str = 'cod') -> int:
        conn = Database.get_connection()
        cur = conn.execute(
            "INSERT INTO orders (customer_id, total_price, status, payment_method) "
            "VALUES (?, ?, 'pending', ?)",
            (customer_id, total_price, payment_method),
        )
        conn.commit()
        return cur.lastrowid

    @staticmethod
    def add_items(order_id: int, items: list[dict]) -> None:
        conn = Database.get_connection()
        conn.executemany(
            "INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price) "
            "VALUES (:order_id, :product_id, :product_name, :quantity, :unit_price)",
            [{**item, "order_id": order_id} for item in items],
        )
        conn.commit()

    @staticmethod
    def get_by_id(order_id: int) -> Order | None:
        conn = Database.get_connection()
        row = conn.execute(
            "SELECT id, customer_id, total_price, status, payment_method, created_at "
            "FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if not row:
            return None
        item_rows = conn.execute(
            "SELECT product_id, product_name, quantity, unit_price "
            "FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()
        return OrderRepository._to_model(row, item_rows)

    @staticmethod
    def get_by_customer(customer_id: int) -> list[Order]:
        conn = Database.get_connection()
        rows = conn.execute(
            "SELECT id, customer_id, total_price, status, payment_method, created_at "
            "FROM orders WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        ).fetchall()

        orders = []
        for r in rows:
            item_rows = conn.execute(
                "SELECT product_id, product_name, quantity, unit_price "
                "FROM order_items WHERE order_id = ?",
                (r["id"],),
            ).fetchall()
            orders.append(OrderRepository._to_model(r, item_rows))
        return orders

    @staticmethod
    def cancel(order_id: int) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE orders SET status = 'cancelled' WHERE id = ?",
            (order_id,),
        )
        conn.commit()

    @staticmethod
    def _to_model(row, item_rows) -> Order:
        return Order(
            id=row["id"],
            customer_id=row["customer_id"],
            total_price=row["total_price"],
            status=row["status"],
            payment_method=row["payment_method"],
            created_at=row["created_at"],
            items=[
                OrderItem(
                    product_id=i["product_id"],
                    product_name=i["product_name"],
                    quantity=i["quantity"],
                    unit_price=i["unit_price"],
                )
                for i in item_rows
            ],
        )
