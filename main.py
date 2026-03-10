from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from contextlib import asynccontextmanager

app = FastAPI()



DATABASE = "sensors.db"


# ----------------------
# Pydantic Model (Input)
# ----------------------
class Sensor(BaseModel):
    name: str
    temperature: float

# ----------------------
# Pydantic Response Model (Output)
# ----------------------
class SensorResponse(Sensor):
    id: int


# ----------------------
# Database Connection
# ----------------------
def get_connection():
    return sqlite3.connect(DATABASE)


# ----------------------
# Initialize Database
# ----------------------
def init_db():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    temperature REAL NOT NULL
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
    init_db()
    yield


# ----------------------
# POST Sensor
# ----------------------
@app.post("/sensor", status_code=201)
def add_sensor(sensor: Sensor):

    alert = sensor.temperature > 30

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO sensors (name, temperature) VALUES (?, ?)",
                (sensor.name, sensor.temperature)
            )

            conn.commit()

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "sensor stored",
        "alert": alert
    }


# ----------------------
# GET Sensors
# ----------------------
@app.get("/sensor", response_model=List[SensorResponse])
def get_sensors():

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, name, temperature FROM sensors")

            rows = cursor.fetchall()

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    sensors = [
        {
            "id": row[0],
            "name": row[1],
            "temperature": row[2]
        }
        for row in rows
    ]

    return sensors