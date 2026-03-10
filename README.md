</> Markdown
# FastAPI Sensor API

A simple API to manage sensors using FastAPI and SQLite.

This API allows you to:

- Add a sensor (POST `/sensor`)
- Retrieve all sensors (GET `/sensor`)
- Detect alerts when temperature exceeds 30°C

---

## Installation

1. **Clone the repository**

git clone https://github.com/SmithCodeXPro/FastAPIproject.git
cd FastAPIproject

2. **Create a virtual environment (recommended)**

python3 -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows

3. **Install dependencies**

pip install -r requirements.txt

- requirements.txt contains:

    fastapi[standard]==0.135.1
    pydantic==2.12.5


4. **Run the server** 

Use the FastAPI dev command: 

   fastapi dev main.py


- API will be available at: http://127.0.0.1:8000

- Swagger UI documentation: http://127.0.0.1:8000/docs

- ReDoc documentation: http://127.0.0.1:8000/redoc


## Endpoints

**POST /sensor**

- Add a new sensor.

    Request JSON body:

        {
        "name": "sensor 1",
        "temperature": 25.5
        }

    Response:

        {
        "message": "sensor stored",
        "alert": false
        }

- alert = true if temperature > 30°C.

**GET /sensor**

- Retrieve all sensors.

    Response:

    [
    {
        "id": 1,
        "name": "sensor 1",
        "temperature": 25.5
    },
    {
        "id": 2,
        "name": "sensor 2",
        "temperature": 32.0
    }
    ]

- id: unique sensor identifier

- temperature: measured temperature



## Project Structure

fastapi-sensor-api/
├── main.py          # FastAPI application
├── requirements.txt # Python dependencies
└── README.md        # Documentation


## Notes

- This project uses SQLite, which is built into Python. No extra database setup is needed.

- The API is ready to run locally and is lightweight for testing or small deployments.
