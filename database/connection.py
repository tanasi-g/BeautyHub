import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "data" / "salon.db"
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Database:
    _conn: sqlite3.Connection | None = None

    @classmethod
    def initialize(cls) -> None:
        _DB_PATH.parent.mkdir(exist_ok=True)
        cls._apply_schema()
        cls._apply_migrations()

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        if cls._conn is None:
            cls._conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
            cls._conn.row_factory = sqlite3.Row
            cls._conn.execute("PRAGMA foreign_keys = ON")
        return cls._conn

    @classmethod
    def _apply_schema(cls) -> None:
        conn = cls.get_connection()
        sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.commit()

    @classmethod
    def _apply_migrations(cls) -> None:
        """Idempotent migrations for columns added after initial release."""
        conn = cls.get_connection()
        for ddl in [
            "ALTER TABLE orders ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'cod'",
        ]:
            try:
                conn.execute(ddl)
                conn.commit()
            except Exception:
                pass  # column already exists

    @classmethod
    def close(cls) -> None:
        if cls._conn:
            cls._conn.close()
            cls._conn = None
