from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from db import get_connection, init_db
from routers.sensor import router

"""
FastAPI Sensor API - Store and retrieve sensor temperature readings.
"""


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

# Include routers
app.include_router(router)

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
