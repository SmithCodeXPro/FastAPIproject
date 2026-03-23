from fastapi import FastAPI, HTTPException
from typing import List
from pathlib import Path
from contextlib import asynccontextmanager

from schemas import Sensor, SensorResponse, SensorUpdate, SensorCreateResponse, SensorMessageResponse
from db import get_connection, init_db
from service import create_sensor, get_sensors, get_sensor_stats, get_sensor, delete_sensor, update_sensor, simulate_sensors_from_file

"""
FastAPI Sensor API - Store and retrieve sensor temperature readings.
"""


SENSOR_DATA_FILE = Path(__file__).parent / "sensor_data.json" # Source for /simulate


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
    except Exception:  # sqlite3.Error might not be imported, but Exception is fine
        raise HTTPException(status_code=500, detail="Database not reachable")


# API Endpoints (HTTP Methods)

# ----------------------
# POST Sensor (add a new sensor)
# ----------------------
@app.post("/sensor", status_code=201, response_model=SensorCreateResponse)
def add_sensor(sensor: Sensor): 
    """Add one sensor reading. alert=True if temperature > 30°C."""
    return create_sensor(sensor)

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
    return get_sensors(name, min_temperature, max_temperature)

# ----------------------
# GET Sensor Statistics
# ----------------------
@app.get("/sensor/stats")
def get_sensor_statistics():
    """Return aggregated statistics for all sensor readings."""
    return get_sensor_stats()

# ----------------------
# GET Sensor by ID
# ----------------------
@app.get("/sensor/{sensor_id}", response_model=SensorResponse)
def get_sensor_by_id(sensor_id: int):
    """Return a single sensor by ID, or 404 if not found."""
    return get_sensor(sensor_id)

# -------------------------
# DELETE Sensor by ID
# -------------------------
@app.delete("/sensor/{sensor_id}", response_model=SensorMessageResponse)
def delete_sensor_by_id(sensor_id: int):
    """Delete the sensor with the given ID, or return 404 if not found.
    
    Returns a message and the deleted sensor data on success.
    """
    return delete_sensor(sensor_id)

# -------------------------
# UPDATE Sensor by ID
# -------------------------
@app.put("/sensor/{sensor_id}", response_model=SensorMessageResponse)
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
    return update_sensor(sensor_id, sensor_update)

# ----------------------
# POST Simulate: JSON file -> database
# ----------------------
@app.post("/simulate")
def simulate_sensors_from_file():
    """Load sensor_data.json and store all readings in the database."""
    return simulate_sensors_from_file(SENSOR_DATA_FILE)
