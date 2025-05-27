import sqlite3
from datetime import datetime

DB_FILE = "usage_tracking.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            payload TEXT,
            timestamp TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


def log_usage(endpoint: str, payload: str):
    conn = sqlite3.connect("usage_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            endpoint TEXT,
            payload TEXT
        )
    """
    )
    cursor.execute(
        "INSERT INTO usage_log (timestamp, endpoint, payload) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), endpoint, payload),
    )
    conn.commit()
    conn.close()
