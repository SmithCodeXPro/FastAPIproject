import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATABASE = Path(__file__).parent / "sensors.db"
logger = logging.getLogger(__name__)


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
        logger.exception("Database initialization error")


def delete_older_than(days: int = 30) -> int:
    """Delete sensor records older than `days` days.

    Returns the number of rows deleted.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM sensors WHERE timestamp < ?", (cutoff_str,))
            deleted = cur.rowcount
            conn.commit()
        return deleted if deleted is not None else 0
    except sqlite3.Error as e:
        logger.exception("Error deleting old records")
        return 0
