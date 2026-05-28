import sqlite3
import unicodedata
from pathlib import Path

# normalize string for case sensitive
def _normalize(s: object) -> str:
    if not isinstance(s, str):
        return s or ""
    nfkd = unicodedata.normalize("NFKD", s.casefold())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

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

            cls._conn.create_function("casefold", 1, _normalize)
        return cls._conn

    @classmethod
    def _apply_schema(cls) -> None:
        conn = cls.get_connection()
        sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.commit()

    @classmethod
    def _apply_migrations(cls) -> None:
        conn = cls.get_connection()
        for ddl in [
            "ALTER TABLE orders ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'cod'",
            "ALTER TABLE appointments ADD COLUMN salon_id INTEGER REFERENCES salons(id)",
            "ALTER TABLE users ADD COLUMN salon_id INTEGER REFERENCES salons(id)",
            "ALTER TABLE salons ADD COLUMN owner_id INTEGER REFERENCES users(id)",
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