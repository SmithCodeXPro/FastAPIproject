# Project Rules

Use these rules to understand and work with this FastAPI sensor project.

## 1. Application startup

- The app must initialize the database on startup through `init_db()`.
- The `sensors` table must exist before any request writes data.
- The `/health` endpoint should only report success if SQLite is reachable.

## 2. Database behavior

- The project uses a local SQLite file called `sensors.db`.
- All database access goes through `get_connection()`.
- Connections return rows as dictionary-like objects so they can be converted into Pydantic models.

## 3. Timestamp rule

- You must use UTC for every timestamp.
- Write timestamps with `datetime.now(timezone.utc)`.
- Store timestamps in SQLite as `YYYY-MM-DD HH:MM:SS`.
- Read timestamps back as UTC-aware datetimes with `tzinfo=timezone.utc`.
- Do not use local time, because it makes the data inconsistent across machines and time zones.

## 4. Input validation

- A sensor name is required.
- A sensor name must be between 1 and 100 characters.
- Temperature must be between `-50` and `150`.
- The names `test` and `invalid` are blocked by business rule.
- Invalid input should fail with FastAPI validation errors.

## 5. Create sensor rule

- `POST /sensor` creates one reading.
- The API must return the created row id, name, temperature, timestamp, and alert flag.
- The alert flag is computed from temperature, not stored in the database.
- If temperature is greater than `30`, `alert` must be `true`.

## 6. Read sensor rules

- `GET /sensor` returns all readings.
- `GET /sensor` may filter by exact `name`.
- `GET /sensor` may filter by `min_temperature` and `max_temperature`.
- Results should be sorted by newest timestamp first.
- `GET /sensor/{sensor_id}` must return one row or `404` if it does not exist.

## 7. Update sensor rules

- `PUT /sensor/{sensor_id}` updates an existing row.
- Only the fields sent in the request body should change.
- Missing fields must keep their previous values.
- The timestamp must be refreshed on update using UTC.

## 8. Delete sensor rules

- `DELETE /sensor/{sensor_id}` removes the row.
- If the row does not exist, return `404`.
- The delete response should include the deleted sensor data.

## 9. Statistics rules

- `GET /sensor/stats` must compute aggregates from the database.
- Include total readings, unique sensors, average temperature, min temperature, max temperature, alert count, earliest timestamp, and latest timestamp.
- If there are no rows, return empty or zero values instead of failing.

## 10. Simulation rules

- `POST /simulate` loads `sensor_data.json`.
- The file must contain a JSON array.
- Each item must match the sensor schema.
- The endpoint should return how many rows were stored and how many alerts were triggered.

## 11. Error handling rules

- Return `400` for invalid JSON in the simulation file.
- Return `404` when a sensor or file is missing.
- Return `500` for database failures.
- Return `422` for invalid request bodies.

## 12. Testing rules

- Tests should use a temporary database, not the real `sensors.db` file.
- Tests must be able to import top-level modules from the project root.
- CRUD tests should cover create, read, update, delete, filtering, and validation.
