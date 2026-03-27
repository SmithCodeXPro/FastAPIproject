import asyncio
import logging
import sqlite3
import time
from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager

from db import get_connection, init_db, delete_older_than
from logging_config import configure_logging
from routers.sensor import router

"""
FastAPI Sensor API - Store and retrieve sensor temperature readings.
"""

CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60

configure_logging()
logger = logging.getLogger(__name__)


# ----------------------
# Lifespan Handler
# ----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup and release app control on shutdown."""

    # Create database tables before serving requests.
    init_db()
    logger.info("Application startup complete")

    async def cleanup_loop():
        while True:
            deleted = delete_older_than(30)
            if deleted:
                logger.info("Lifecycle cleanup deleted %s old sensor records", deleted)
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
        logger.info("Application shutdown complete")

# Register lifespan handler with the app
app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error during %s %s", request.method, request.url.path)
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s in %.2f ms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

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
        logger.debug("Health check succeeded")
        return {"status": "ok","database": "reachable"}
    except sqlite3.Error:
        logger.exception("Health check failed: database not reachable")
        raise HTTPException(status_code=500, detail="Database not reachable")
