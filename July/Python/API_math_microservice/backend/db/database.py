# database.py
import sqlite3
from typing import Optional, Any
from config.settings import Settings

class Database:
    def __init__(self, db_path: Optional[str] = None):
        settings = Settings()
        self.db_path = db_path or settings.db_path
        self._ensure_table()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    input TEXT NOT NULL,
                    result TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_request(self, operation: str, inp: dict, result: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO requests (operation, input, result) VALUES (?, ?, ?)",
                (operation, str(inp), str(result))
            )
            conn.commit()

    def get_existing_request(self, operation: str, inp: dict) -> Optional[Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT result FROM requests WHERE operation = ? AND input = ?",
                (operation, str(inp))
            )
            row = cursor.fetchone()
            if row:
                return row["result"]
            return None

    def clear_requests(self) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM requests")
            conn.commit()
