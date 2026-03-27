# FastAPI Sensor API

A REST API to store and retrieve sensor temperature readings using FastAPI and SQLite.

## Features

- **Add sensor reading** – POST `/sensor` with name and temperature
- **List sensors** – GET `/sensor` with optional filters
- **Get sensor by ID** – GET `/sensor/{sensor_id}`
- **Update sensor by ID** – PUT `/sensor/{sensor_id}`
- **Delete sensor by ID** – DELETE `/sensor/{sensor_id}`
- **Query stats** – GET `/sensor/stats` (aggregate metrics)
- **Batch load simulator** – POST `/simulate` from `sensor_data.json`
- **Alerts** – temperature above 30°C sets `alert: true` on insert
- **Auto cleanup** – records older than 30 days are removed automatically on app startup

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- SQLite (built-in)

## Quickstart

```bash
git clone https://github.com/SmithCodeXPro/FastAPIproject.git
cd FastAPIproject
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

- API base URL: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API Endpoints

### POST `/sensor`

Create one sensor reading.

Request body:

```json
{
  "name": "sensor-1",
  "temperature": 25.5
}
```

Response (201):

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

### GET `/sensor`

List all sensor readings. Optional query params:
- `name` (exact)
- `min_temperature`
- `max_temperature`

Example:

```bash
curl "http://127.0.0.1:8000/sensor?min_temperature=20&max_temperature=35"
```

### GET `/sensor/{sensor_id}`

Get a reading by ID; 404 if missing.

```bash
curl http://127.0.0.1:8000/sensor/1
```

### PUT `/sensor/{sensor_id}`

Update sensor name and/or temperature.

Request body (partial updates allowed):

```json
{
  "temperature": 26.5
}
```

### DELETE `/sensor/{sensor_id}`

Delete a sensor reading by ID.

```bash
curl -X DELETE http://127.0.0.1:8000/sensor/1
```

### GET `/sensor/stats`

Aggregate statistics over all readings:

```json
{
  "total_readings": 25,
  "unique_sensors": 3,
  "avg_temperature": 28.6,
  "min_temperature": 15.1,
  "max_temperature": 42.8,
  "alert_count": 8,
  "earliest_timestamp": "2026-03-19 10:00:02",
  "latest_timestamp": "2026-03-19 12:08:33"
}
```

Example:

```bash
curl http://127.0.0.1:8000/sensor/stats
```

### POST `/simulate`

Load batch sensor data from `sensor_data.json` and store in DB.

`sample sensor_data.json`:

```json
[
  {"name": "sim-sensor-1", "temperature": 22.5},
  {"name": "sim-sensor-2", "temperature": 31.2}
]
```

```bash
curl -X POST http://127.0.0.1:8000/simulate
```

Response:

```json
{
  "message": "simulated 5 sensor(s) from file",
  "stored": 5,
  "alerts": 2
}
```

## Project Structure

```
FastAPIproject/
├── main.py           # FastAPI application
├── sensor_data.json  # Simulator input data
├── sensors.db        # SQLite database (auto-created)
├── requirements.txt  # Python dependencies
└── README.md         # Documentation
```

## Notes

- SQLite DB is created automatically in project directory.
- Old sensor rows older than 30 days are cleaned up automatically when the app starts.
- No additional DB server required.
- `name` cannot be `test` or `invalid` by business rule.
- Temperatures are validated in range [-50, 150].

## Troubleshooting

- If `sensors.db` is locked, stop all app instances and remove stale `.db-journal` file.
- For JSON parse errors in `/simulate`, verify `sensor_data.json` is valid JSON array.

