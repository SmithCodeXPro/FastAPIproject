from fastapi import HTTPException
from typing import List
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from schemas import Sensor, SensorResponse, SensorUpdate, SensorCreateResponse, SensorMessageResponse
from db import get_connection, parse_timestamp


def create_sensor(sensor: Sensor) -> SensorCreateResponse:
    """Add one sensor reading. alert=True if temperature > 30°C."""
    
    alert = sensor.temperature > 30

    # Insert sensor into database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sensors (name, temperature, timestamp) VALUES (?, ?, ?)",
                (sensor.name, sensor.temperature, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
            ) 
            conn.commit()
            last_id = cursor.lastrowid

            # Fetch the inserted record to get the exact timestamp from database
            cursor.execute("SELECT timestamp FROM sensors WHERE id = ?", (last_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to retrieve timestamp")
            
            db_timestamp = parse_timestamp(row)["timestamp"]

    # Return error if database operation fails
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return success message and sensor details
    return SensorCreateResponse(
        message="sensor created",
        id=last_id,
        name=sensor.name,
        temperature=sensor.temperature,
        timestamp=db_timestamp,
        alert=alert
    )


def get_sensors(
    name: str | None = None,
    min_temperature: float | None = None,
    max_temperature: float | None = None,
) -> List[SensorResponse]:
    """Return filtered sensor readings.

    - name: filter by exact sensor name (case-sensitive). Use partial match with SQL `LIKE` by adjusting this code.
    - min_temperature: include sensors with temperature >= this value.
    - max_temperature: include sensors with temperature <= this value.

    Returns an empty list if no sensors are found.
    """

    # Build SQL query and params based on filters
    query = "SELECT id, name, temperature, timestamp FROM sensors"
    conditions = []
    params = []

    if name is not None:
        conditions.append("name = ?")
        params.append(name)

    if min_temperature is not None:
        conditions.append("temperature >= ?")
        params.append(min_temperature)

    if max_temperature is not None:
        conditions.append("temperature <= ?")
        params.append(max_temperature)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY timestamp DESC"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [SensorResponse(**parse_timestamp(row)) for row in rows]

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_sensor_stats() -> dict:
    """Return aggregated statistics for all sensor readings."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_readings,
                    COUNT(DISTINCT name) AS unique_sensors,
                    AVG(temperature) AS avg_temperature,
                    MIN(temperature) AS min_temperature,
                    MAX(temperature) AS max_temperature,
                    SUM(CASE WHEN temperature > 30 THEN 1 ELSE 0 END) AS alert_count,
                    MIN(timestamp) AS earliest_timestamp,
                    MAX(timestamp) AS latest_timestamp
                FROM sensors
                """
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "total_readings": 0,
                    "unique_sensors": 0,
                    "avg_temperature": None,
                    "min_temperature": None,
                    "max_temperature": None,
                    "alert_count": 0,
                    "earliest_timestamp": None,
                    "latest_timestamp": None,
                }

            return {
                "total_readings": row["total_readings"],
                "unique_sensors": row["unique_sensors"],
                "avg_temperature": row["avg_temperature"],
                "min_temperature": row["min_temperature"],
                "max_temperature": row["max_temperature"],
                "alert_count": row["alert_count"],
                "earliest_timestamp": datetime.strptime(row["earliest_timestamp"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc) if row["earliest_timestamp"] else None,
                "latest_timestamp": datetime.strptime(row["latest_timestamp"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc) if row["latest_timestamp"] else None,
            }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_sensor(sensor_id: int) -> SensorResponse:
    """Return a single sensor by ID, or 404 if not found."""

    # Get sensor from database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, name, temperature, timestamp FROM sensors where id = ?", (sensor_id,))

            row = cursor.fetchone() # Get the first row from the result set 
            if not row:
                raise HTTPException(status_code=404, detail="Sensor not found")
            return SensorResponse(**parse_timestamp(row)) # Convert sqlite3.Row to dict and then to SensorResponse object (using Pydantic's **kwargs)

    # Return error if database operation fails
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


def delete_sensor(sensor_id: int) -> SensorMessageResponse:
    """Delete the sensor with the given ID, or return 404 if not found.
    
    Returns a message and the deleted sensor data on success.
    """
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # First fetch the sensor to make sure it exists (and for response)
            cursor.execute("SELECT id, name, temperature, timestamp FROM sensors WHERE id = ?", (sensor_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Sensor not found")
            sensor_data = parse_timestamp(row)

            cursor.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))
            conn.commit()

            return SensorMessageResponse(
                message="Sensor deleted",
                sensor=SensorResponse(**sensor_data)
            )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_sensor(sensor_id: int, sensor_update: SensorUpdate) -> SensorMessageResponse:
    """
    Update the sensor with the given ID using the provided fields (name and/or temperature).
    Only fields provided in the request body will be updated; others remain unchanged.
    Returns a message and the updated sensor data on success.
    Raises 404 if the sensor is not found.
    """

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Fetch current sensor (to verify existence and for response)
            cursor.execute("SELECT id, name, temperature, timestamp FROM sensors WHERE id = ?", (sensor_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Sensor not found")

            # Get new values, fallback to old values if not provided
            current_data = parse_timestamp(row)
            new_name = sensor_update.name if sensor_update.name is not None else current_data["name"]
            new_temperature = sensor_update.temperature if sensor_update.temperature is not None else current_data["temperature"]

            # Update the sensor record
            cursor.execute(
                "UPDATE sensors SET name = ?, temperature = ?, timestamp = ? WHERE id = ?",
                (new_name, new_temperature, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'), sensor_id),
            )
            conn.commit()

            # Fetch the updated row to return fresh data (including updated timestamp, if any)
            cursor.execute("SELECT id, name, temperature, timestamp FROM sensors WHERE id = ?", (sensor_id,))
            updated_row = cursor.fetchone()
            updated_data = parse_timestamp(updated_row) if updated_row else current_data

            return SensorMessageResponse(
                message="Sensor updated",
                sensor=SensorResponse(**updated_data)
            )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


def simulate_sensors_from_file(file_path: Path) -> dict:
    """Load sensors from JSON and insert into DB. Returns count and alerts."""

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Sensor data file not found: {file_path}")

    # Load JSON data
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in file: {e}")

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="File must contain a JSON array of sensors")

    stored = 0
    alerts = 0

    # Insert data into database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            sensors = [Sensor(**item) for item in data]

            cursor.executemany(
                "INSERT INTO sensors (name, temperature, timestamp) VALUES (?, ?, ?)",
                [(s.name, s.temperature, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')) for s in sensors]
            )

            stored = len(sensors)
            alerts = sum(1 for s in sensors if s.temperature > 30)
            conn.commit()
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid sensor data: {e}")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return success message and counts
    return {
        "message": f"simulated {stored} sensor(s) from file",
        "stored": stored,
        "alerts": alerts,
    }