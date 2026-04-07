"""
SQLite cache (opsiyonel).
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta

from config import DATABASE

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_file = DATABASE["file"]
        self.cache_hours = DATABASE["cache_hours"]
        self.init_db()

    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    symbol TEXT PRIMARY KEY,
                    data BLOB,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Database init hatası: %s", e)

    def save(self, symbol: str, data: dict):
        try:
            import pickle

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache (symbol, data, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                (symbol, pickle.dumps(data)),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Cache save hatası: %s", e)

    def get(self, symbol: str):
        try:
            import pickle

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT data, timestamp FROM cache WHERE symbol = ?", (symbol,))
            result = cursor.fetchone()
            conn.close()
            if not result:
                return None
            data, timestamp = result
            timestamp = datetime.fromisoformat(timestamp)
            if datetime.now() - timestamp < timedelta(hours=self.cache_hours):
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error("Cache get hatası: %s", e)
            return None

    def clear(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Cache clear hatası: %s", e)

