# FastAPI Sensor API

A REST API to store and retrieve sensor temperature readings using FastAPI and SQLite.

## Features

- **Add sensors** – POST sensor readings with name and temperature
- **List all sensors** – GET all stored readings
- **Get sensor by ID** – GET a single sensor by its ID
- **Temperature alerts** – Automatic alert when temperature exceeds 30°C
- **File sensor simulator** – Load batch sensor data from a JSON file

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- SQLite (built-in)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/SmithCodeXPro/FastAPIproject.git
cd FastAPIproject
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
# venv\Scripts\activate   # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
fastapi dev main.py
```

- **API:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

## API Endpoints

### POST `/sensor`

Add a new sensor reading.

**Request:**
```json
{
  "name": "sensor-1",
  "temperature": 25.5
}
```

**Response (201):**
```json
{
  "message": "sensor stored",
  "id": 1,
  "name": "sensor-1",
  "temperature": 25.5,
  "timestamp": "2024-03-12T10:30:00",
  "alert": false
}
```

- `alert` is `true` when temperature > 30°C

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/sensor \
  -H "Content-Type: application/json" \
  -d '{"name": "sensor-1", "temperature": 25.5}'
```

### GET `/sensor`

Retrieve all sensors.

**Response:**
```json
[
  {
    "id": 1,
    "name": "sensor-1",
    "temperature": 25.5,
    "timestamp": "2024-03-12T10:30:00"
  }
]
```

**Example:**
```bash
curl http://127.0.0.1:8000/sensor
```

### GET `/sensor/{sensor_id}`

Retrieve a single sensor by ID. Returns 404 if not found.

**Example:**
```bash
curl http://127.0.0.1:8000/sensor/1
```

### POST `/simulate`

Load sensor data from `sensor_data.json` and insert all readings into the database.

**sensor_data.json format:**
```json
[
  {"name": "sim-sensor-1", "temperature": 22.5},
  {"name": "sim-sensor-2", "temperature": 31.2}
]
```

**Response:**
```json
{
  "message": "simulated 5 sensor(s) from file",
  "stored": 5,
  "alerts": 2
}
```

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/simulate
```

## Project Structure

```
FastAPIproject/
├── main.py           # FastAPI application
├── sensor_data.json  # Sample data for /simulate
├── sensors.db        # SQLite database (created on first run)
├── requirements.txt  # Python dependencies
└── README.md         # Documentation
```

## Notes

- SQLite requires no separate database setup.
- The database file `sensors.db` is created automatically on first run.
- The API is lightweight and suitable for local use or small deployments.
