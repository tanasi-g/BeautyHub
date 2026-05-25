from __future__ import annotations
from database.connection import Database
from models.product import Product


class ProductRepository:

    @staticmethod
    def get_all() -> list[Product]:
        rows = Database.get_connection().execute(
            "SELECT id, name, description, price, stock, image_path, is_active "
            "FROM products ORDER BY name"
        ).fetchall()
        return [ProductRepository._to_model(r) for r in rows]

    @staticmethod
    def count() -> int:
        return Database.get_connection().execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

    @staticmethod
    def exists_by_name(name: str) -> bool:
        return Database.get_connection().execute(
            "SELECT 1 FROM products WHERE LOWER(name) = LOWER(?)", (name,)
        ).fetchone() is not None

    @staticmethod
    def create(
        name: str,
        description: str | None,
        price: float,
        stock: int,
        image_path: str | None,
    ) -> int:
        conn = Database.get_connection()
        cursor = conn.execute(
            "INSERT INTO products (name, description, price, stock, image_path) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, description, price, stock, image_path),
        )
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def search(keyword: str) -> list[Product]:
        kw = f"%{keyword.strip().lower()}%" if keyword.strip() else "%"
        rows = Database.get_connection().execute(
            "SELECT id, name, description, price, stock, image_path, is_active "
            "FROM products "
            "WHERE is_active = 1 AND (LOWER(name) LIKE ? OR LOWER(COALESCE(description,'')) LIKE ?) "
            "ORDER BY name",
            (kw, kw),
        ).fetchall()
        return [ProductRepository._to_model(r) for r in rows]

    @staticmethod
    def get_stock(product_id: int) -> int:
        row = Database.get_connection().execute(
            "SELECT stock FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        return row["stock"] if row else 0

    @staticmethod
    def reduce_stock(product_id: int, qty: int) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (qty, product_id),
        )
        conn.commit()

    @staticmethod
    def restore_stock(product_id: int, qty: int) -> None:
        conn = Database.get_connection()
        conn.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (qty, product_id),
        )
        conn.commit()

    @staticmethod
    def _to_model(row) -> Product:
        return Product(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            stock=row["stock"],
            image_path=row["image_path"],
            is_active=bool(row["is_active"]),
        )
