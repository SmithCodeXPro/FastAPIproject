import sys
from pathlib import Path
from datetime import timezone

# Ensure the project root is importable when pytest runs from a different working directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db as db_module
from db import delete_older_than, get_connection, init_db, parse_timestamp


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


def test_delete_older_than_removes_only_expired_rows(tmp_path, monkeypatch):
    test_db = tmp_path / "test_sensors.db"
    monkeypatch.setattr(db_module, "DATABASE", test_db)

    init_db()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sensors (name, temperature, timestamp) VALUES (?, ?, ?)",
            ("old-sensor", 20.0, "2000-01-01 10:00:00"),
        )
        conn.execute(
            "INSERT INTO sensors (name, temperature, timestamp) VALUES (?, ?, ?)",
            ("new-sensor", 21.0, "2999-01-01 10:00:00"),
        )
        conn.commit()

    deleted = delete_older_than(30)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sensors ORDER BY name")
        remaining = [row[0] for row in cursor.fetchall()]

    assert deleted == 1
    assert remaining == ["new-sensor"]