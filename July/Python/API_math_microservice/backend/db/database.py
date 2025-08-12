# database.py
import sqlite3
from typing import Optional, Any, Dict
from config.settings import Settings
import uuid
import bcrypt

class Database:
    def __init__(self, db_path: Optional[str] = None):
        settings = Settings()
        self.db_path = db_path or settings.db_path
        self._ensure_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        with self._get_connection() as conn:
            # Requests table
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
            # Users table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
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

    def clear_requests(self, table_name: str) -> None:
        with self._get_connection() as conn:
            conn.execute(f"DELETE FROM {table_name}")
            conn.commit()

    # --- User Management ---

    def register_user(self, username: str, email: str, password: str) -> Optional[Dict]:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user_id = str(uuid.uuid4())
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (id, username, email, password) VALUES (?, ?, ?, ?)",
                    (user_id, username, email, hashed_pw)
                )
                conn.commit()
            return {"id": user_id, "username": username, "email": email}
        except sqlite3.IntegrityError:
            return None

    def get_user_by_email_or_username(self, identifier: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE email = ? OR username = ?",
                (identifier, identifier)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def delete_user_by_id(self, user_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def verify_user_password(self, identifier: str, password: str) -> Optional[Dict]:
        user = self.get_user_by_email_or_username(identifier)
        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            return user
        return None
