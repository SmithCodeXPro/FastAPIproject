from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List
import sqlite3 
import json
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

"""
FastAPI Sensor API - Store and retrieve sensor temperature readings.
"""


# Paths relative to this file's directory
DATABASE = Path(__file__).parent / "sensors.db"
SENSOR_DATA_FILE = Path(__file__).parent / "sensor_data.json" # Source for /simulate


# ----------------------
# Pydantic Model (request body)
# ----------------------
class Sensor(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    temperature: float = Field(..., ge=-50, le=150)

    # Sensor request model for incoming data
    @field_validator("name")
    @classmethod
    def no_forbidden_names(cls, v: str) -> str:
        if v.lower() in {"test", "invalid"}:
            raise ValueError("This sensor name is not allowed")
        return v

# ----------------------
# Pydantic Response Model (response body)
# ----------------------
class SensorResponse(Sensor):
    id: int
    timestamp: datetime | None = None

# ------------------------
# Pydantic Update Model (update body)
# ------------------------
class SensorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    temperature: float | None = Field(default=None, ge=-50, le=150)

# ----------------------
# Database (SQLite) Connection  - rows become dict-like
# ----------------------
def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # rows become dict-like objects (for easier access)
    return conn


# ----------------------
# Initialize Database
# ----------------------
def init_db():
    """Create sensors table if it doesn't exist. Called on app startup."""

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    except sqlite3.Error as e:
        print("Database initialization error:", e)


# ----------------------
# Lifespan Handler
# ----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run init_db on startup, cleanup on shutdown."""

    # Create database tables
    init_db()

    # Yield control to the FastAPI app
    yield

# Register lifespan handler with the app
app = FastAPI(lifespan=lifespan) 

# ----------------------
# Health check
# ----------------------
@app.get("/health")
def health_check():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok","database": "reachable"}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database not reachable")


# API Endpoints (HTTP Methods)

# ----------------------
# POST Sensor (add a new sensor)
# ----------------------
@app.post("/sensor", status_code=201)
def add_sensor(sensor: Sensor): 
    """Add one sensor reading. alert=True if temperature > 30°C."""

    alert = sensor.temperature > 30

    # Insert sensor into database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sensors (name, temperature) VALUES (?, ?)",
                (sensor.name, sensor.temperature)
            ) 
            conn.commit()
            last_id = cursor.lastrowid

    # Return error if database operation fails
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return success message and sensor details
    return {
        "message": "sensor stored",
        "id": last_id, # Get the last inserted row id (auto-incremented)
        "name": sensor.name, # Get the sensor name
        "temperature": sensor.temperature,
        "timestamp": datetime.now(), # Get the current timestamp
        "alert": alert, # Get the alert status (True if temperature > 30°C)  
    }

# ----------------------
# GET All Sensors
# ----------------------
@app.get("/sensor", response_model=List[SensorResponse])
def get_all_sensors(
    name: str | None = None,
    min_temperature: float | None = None,
    max_temperature: float | None = None,
):
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

    query += " ORDER BY id"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [SensorResponse(**dict(row)) for row in rows]

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------
# GET Sensor Statistics
# ----------------------
@app.get("/sensor/stats")
def get_sensor_statistics():
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
                "earliest_timestamp": row["earliest_timestamp"],
                "latest_timestamp": row["latest_timestamp"],
            }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------
# GET Sensor by ID
# ----------------------
@app.get("/sensor/{sensor_id}", response_model=SensorResponse)
def get_sensor_by_id(sensor_id: int):
    """Return a single sensor by ID, or 404 if not found."""

    # Get sensor from database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, name, temperature, timestamp FROM sensors where id = ?", (sensor_id,))

            row = cursor.fetchone() # Get the first row from the result set 
            if not row:
                raise HTTPException(status_code=404, detail="Sensor not found")
            return SensorResponse(**dict(row)) # Convert sqlite3.Row to dict and then to SensorResponse object (using Pydantic's **kwargs)

    # Return error if database operation fails
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# -------------------------
# DELETE Sensor by ID
# -------------------------
@app.delete("/sensor/{sensor_id}", response_model=dict)

def delete_sensor_by_id(sensor_id: int):
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
            sensor_data = dict(row)

            cursor.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))
            conn.commit()

            return {
                "message": "Sensor deleted",
                "sensor": SensorResponse(**sensor_data)
            }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# -------------------------
# UPDATE Sensor by ID
# -------------------------
@app.put("/sensor/{sensor_id}", response_model=dict)
def update_sensor_by_id(
    sensor_id: int,
    sensor_update: SensorUpdate
):
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
            current_data = dict(row)
            new_name = sensor_update.name if sensor_update.name is not None else current_data["name"]
            new_temperature = sensor_update.temperature if sensor_update.temperature is not None else current_data["temperature"]

            # Update the sensor record
            cursor.execute(
                "UPDATE sensors SET name = ?, temperature = ? WHERE id = ?",
                (new_name, new_temperature, sensor_id),
            )
            conn.commit()

            # Fetch the updated row to return fresh data (including updated timestamp, if any)
            cursor.execute("SELECT id, name, temperature, timestamp FROM sensors WHERE id = ?", (sensor_id,))
            updated_row = cursor.fetchone()
            updated_data = dict(updated_row) if updated_row else current_data

            return {
                "message": "Sensor updated",
                "sensor": SensorResponse(**updated_data)
            }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ----------------------
# File sensor simulator: JSON file -> database
# ----------------------
def run_file_sensor_simulator(file_path: Path = SENSOR_DATA_FILE) -> dict:
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
            for item in data: # Convert JSON to Sensor object
                sensor = Sensor(**item) # Validate sensor data
                cursor.execute(
                    "INSERT INTO sensors (name, temperature) VALUES (?, ?)",
                    (sensor.name, sensor.temperature),
                )
                stored += 1
                if float(sensor.temperature) > 30:
                    alerts += 1
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


# ----------------------
# POST Simulate: JSON file -> database
# ----------------------
@app.post("/simulate")
def simulate_sensors_from_file():
    """Load sensor_data.json and store all readings in the database."""

    return run_file_sensor_simulator()
