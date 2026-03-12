from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
    name: str
    temperature: float

# ----------------------
# Pydantic Response Model (response body)
# ----------------------
class SensorResponse(Sensor):
    id: int
    timestamp: datetime | None = None


# ----------------------
# Database (SQLite) Connection
# ----------------------
def get_connection():
    return sqlite3.connect(DATABASE)


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



# API Endpoints (HTTP Methods)

# ----------------------
# POST Sensor
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

    # Return error if database operation fails
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return success message and alert
    return {
        "message": "sensor stored",
        "alert": alert
    }

# ----------------------
# GET All Sensors
# ----------------------
@app.get("/sensor", response_model=List[SensorResponse])
def get_all_sensors(): 
    """Return all stored sensors. Returns empty list if no sensors are found."""

    # Get all sensors from database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, temperature, timestamp FROM sensors ORDER BY id")
            rows = cursor.fetchall()
    # Return error if database operation fails
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return all sensors
    return [
        {"id": row[0], "name": row[1], "temperature": row[2], "timestamp": row[3]}
        for row in rows
    ]


# ----------------------
# GET Sensor by ID
# ----------------------
@app.get("/sensor/{sensor_id}", response_model=SensorResponse)
def get_sensors(sensor_id: int):
    """Return a single sensor by ID, or 404 if not found."""

    # Get sensor from database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, name, temperature, timestamp FROM sensors where id = ?", (sensor_id,))

            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Sensor not found")

    # Return error if database operation fails
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return sensor
    return {
        "id": row[0],
        "name": row[1],
        "temperature": row[2],
        "timestamp": row[3],
    }

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
