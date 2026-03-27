import asyncio
import sqlite3
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from db import get_connection, init_db, delete_older_than
from routers.sensor import router

"""
FastAPI Sensor API - Store and retrieve sensor temperature readings.
"""

CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60


# ----------------------
# Lifespan Handler
# ----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup and release app control on shutdown."""

    # Create database tables before serving requests.
    init_db()

    async def cleanup_loop():
        while True:
            deleted = delete_older_than(30)
            if deleted:
                print(f"Lifecycle cleanup: deleted {deleted} old sensor records")
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)

    # Run one cleanup immediately, then keep cleaning up once per day.
    cleanup_task = asyncio.create_task(cleanup_loop())

    # Hand control back to FastAPI for the app lifetime.
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

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
