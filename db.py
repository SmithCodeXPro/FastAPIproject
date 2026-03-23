import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DATABASE = Path(__file__).parent / "sensors.db"


def parse_timestamp(row):
    """Parse database row and convert timestamp string to UTC datetime object."""
    data = dict(row)
    if data.get("timestamp"):
        # SQLite stores timestamps as 'YYYY-MM-DD HH:MM:SS' strings
        # Parse and assume they're in UTC (since we store them that way)
        data["timestamp"] = datetime.strptime(data["timestamp"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    return data


def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=True)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create sensors table if it doesn't exist. Called on app startup."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sensors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
    except sqlite3.Error as e:
        print("Database initialization error:", e)
