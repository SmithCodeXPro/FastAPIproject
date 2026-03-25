import sys
from pathlib import Path
from datetime import timezone

# Ensure the project root is importable when pytest runs from a different working directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db as db_module
from db import get_connection, init_db, parse_timestamp


def test_init_db_creates_table(tmp_path, monkeypatch):
    test_db = tmp_path / "test_sensors.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    init_db()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sensors'"
        )
        assert cursor.fetchone() is not None


def test_get_connection_uses_database_file(tmp_path, monkeypatch):
    test_db = tmp_path / "test_sensors.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    with get_connection() as conn:
        conn.execute("SELECT 1")
        assert conn is not None


def test_parse_timestamp_returns_utc_datetime():
    row = {
        "id": 1,
        "name": "sensor-1",
        "temperature": 25.5,
        "timestamp": "2026-03-25 12:00:00",
    }

    data = parse_timestamp(row)

    assert data["timestamp"].tzinfo == timezone.utc
    assert data["timestamp"].hour == 12