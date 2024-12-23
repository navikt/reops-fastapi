import os
import logging
import asyncio
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from databases import Database
from datetime import datetime
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import ssl

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve the DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
SKIP_DB_CHECK = os.getenv("SKIP_DB_CHECK", "false").lower() == "true"

if DATABASE_URL:
    logger.info(f"DATABASE_URL is set to: {DATABASE_URL}")

# Check if the DATABASE_URL environment variable is set
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please check your environment variables.")

# Initialize the database connection
database = Database(DATABASE_URL)
app = FastAPI()

class Analytics(BaseModel):
    website_id: int
    url: str
    event_type: str

def check_ssl_files():
    ssl_files = [
        "/var/run/secrets/nais.io/sqlcertificate/cert.pem",
        "/var/run/secrets/nais.io/sqlcertificate/key.pem",
        "/var/run/secrets/nais.io/sqlcertificate/root-cert.pem"
    ]
    for file in ssl_files:
        if os.path.exists(file):
            if os.access(file, os.R_OK):
                logger.info(f"SSL file found and readable: {file}")
            else:
                logger.error(f"SSL file found but not readable: {file}")
        else:
            logger.error(f"SSL file not found: {file}")


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        content={"message": "An internal server error occurred. Please try again later.", "details": str(exc)},
        status_code=500
    )

@app.on_event("startup")
async def startup():
    if SKIP_DB_CHECK:
        logger.info("Skipping database connection check during startup.")
        return

    check_ssl_files()
    retries = 5
    for i in range(retries):
        try:
            await database.connect()
            logger.info("Database connection established.")
            break
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            if isinstance(e, ssl.SSLError):
                logger.error(f"SSL Error details: {e.__class__.__name__}: {e}")
            if i < retries - 1:
                await asyncio.sleep(2 ** i)
            else:
                logger.critical("Could not connect to the database after retries. Exiting application.")
                raise SystemExit("Database connection failed.")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    logger.info("Database connection closed.")

@app.post("/api/send")
async def add_stats(analytics: Analytics):
    query = """
        INSERT INTO analytics (website_id, url, event_type, timestamp)
        VALUES (:website_id, :url, :event_type, :timestamp)
    """
    values = {
        "website_id": analytics.website_id,
        "url": analytics.url,
        "event_type": analytics.event_type,
        "timestamp": datetime.utcnow().replace(second=0, microsecond=0)  # Use datetime object
    }
    try:
        await database.execute(query=query, values=values)
        return {"message": "Stats added successfully"}
    except Exception as e:
        logger.error(f"Failed to insert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to add stats.")

@app.get("/api/data")
async def get_events():
    query = """
        SELECT * FROM analytics
    """
    results = await database.fetch_all(query=query)
    return {"events": [dict(result) for result in results]}

@app.get("/api/isalive")
def read_isalive():
    return {"message": "Alive"}

@app.get("/api/isready")
async def read_isready():
    try:
        await database.execute("SELECT 1")  # Simple query to check database readiness
        return {"message": "Ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"message": "Not ready", "details": str(e)}, 503