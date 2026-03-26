import sqlite3
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
    """Initialize the database on startup and release app control on shutdown."""

    # Create database tables before serving requests.
    init_db()

    # Hand control back to FastAPI for the app lifetime.
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
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database not reachable")
