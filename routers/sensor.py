from fastapi import APIRouter
from typing import List
from pathlib import Path

from schemas import Sensor, SensorResponse, SensorUpdate, SensorCreateResponse, SensorMessageResponse
from service import create_sensor, get_sensors, get_sensor_stats, get_sensor, delete_sensor, update_sensor
from service import simulate_sensors_from_file as _simulate_sensors_from_file

router = APIRouter()

SENSOR_DATA_FILE = Path(__file__).parent.parent / "sensor_data.json"

# ----------------------
# POST Sensor (add a new sensor)
# ----------------------
@router.post("/sensor", status_code=201, response_model=SensorCreateResponse)
def add_sensor(sensor: Sensor):
    """Add one sensor reading. alert=True if temperature > 30°C."""
    return create_sensor(sensor)

# ----------------------
# GET All Sensors
# ----------------------
@router.get("/sensor", response_model=List[SensorResponse])
def get_all_sensors(
    name: str | None = None,
    min_temperature: float | None = None,
    max_temperature: float | None = None,
    limit: int = 10,
    offset: int = 0,
):
    """Return filtered sensor readings.

    - name: filter by exact sensor name (case-sensitive). Use partial match with SQL `LIKE` by adjusting this code.
    - min_temperature: include sensors with temperature >= this value.
    - max_temperature: include sensors with temperature <= this value.
    - limit: maximum number of results to return.
    - offset: number of results to skip (for pagination).

    Returns an empty list if no sensors are found.
    """
    return get_sensors(name, min_temperature, max_temperature, limit, offset)


# ----------------------
# GET Sensor Statistics
# ----------------------
@router.get("/sensor/stats")
def get_sensor_statistics(name: str | None = None):
    """Return aggregated statistics for all sensor readings."""
    return get_sensor_stats(name)

# ----------------------
# GET Sensor by ID
# ----------------------
@router.get("/sensor/{sensor_id}", response_model=SensorResponse)
def get_sensor_by_id(sensor_id: int):
    """Return a single sensor by ID, or 404 if not found."""
    return get_sensor(sensor_id)

# -------------------------
# DELETE Sensor by ID
# -------------------------
@router.delete("/sensor/{sensor_id}", response_model=SensorMessageResponse)
def delete_sensor_by_id(sensor_id: int):
    """Delete the sensor with the given ID, or return 404 if not found.

    Returns a message and the deleted sensor data on success.
    """
    return delete_sensor(sensor_id)

# -------------------------
# UPDATE Sensor by ID
# -------------------------
@router.put("/sensor/{sensor_id}", response_model=SensorMessageResponse)
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
@router.post("/simulate")
def simulate_sensors():
    """Load sensor_data.json and store all readings in the database."""
    return _simulate_sensors_from_file(SENSOR_DATA_FILE)