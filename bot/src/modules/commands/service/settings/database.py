import sqlite3
from pathlib import Path


class SettingsDatabase:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self.init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    PRIMARY KEY (user_id, key)
                )
            """)

    def get(self, user_id: int, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT value
                FROM user_settings
                WHERE user_id = ? AND key = ?
                """,
                (user_id, key),
            ).fetchone()

        return row["value"] if row else None

    def get_all(self, user_id: int) -> dict[str, str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT key, value
                FROM user_settings
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchall()

        return {row["key"]: row["value"] for row in rows}

    def set(self, user_id: int, key: str, value: str):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_settings(user_id, key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, key)
                DO UPDATE SET value = excluded.value
                """,
                (user_id, key, value),
            )
            conn.commit()

    def delete(self, user_id: int, key: str):
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM user_settings
                WHERE user_id = ? AND key = ?
                """,
                (user_id, key),
            )
            conn.commit()

    def delete_user(self, user_id: int):
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM user_settings
                WHERE user_id = ?
                """,
                (user_id,),
            )
            conn.commit()