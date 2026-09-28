import json
import os
import sqlite3
import time
from pathlib import Path

from app.config import settings


class CacheStore:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.cache_db_path
        self._ensure_parent_directory()
        self._initialize_db()

    def _ensure_parent_directory(self) -> None:
        parent = Path(self.db_path).parent
        if parent:
            parent.mkdir(parents=True, exist_ok=True)

    def _initialize_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def get(self, key: str):
        now = time.time()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM cache WHERE key = ? AND expires_at > ?",
                (key, now),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def set(self, key: str, value, ttl_seconds: int = 300) -> None:
        payload = json.dumps(value)
        expires_at = time.time() + ttl_seconds
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO cache(key, value, expires_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at",
                (key, payload, expires_at),
            )
            conn.commit()

    def delete(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()
