import os
import logging
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from databases import Database
from datetime import datetime
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Retrieve the DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Check if the DATABASE_URL environment variable is set
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please check your environment variables.")

# Initialize the database connection
database = Database(DATABASE_URL)
app = FastAPI()

class Analytics(BaseModel):
    website_id: int
    url: str


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return Response(
        content='{"message": "An internal server error occurred. Please try again later."}',
        media_type="application/json",
        status_code=500
    )

@app.on_event("startup")
async def startup():
    retries = 5
    for i in range(retries):
        try:
            await database.connect()
            logger.info("Database connection established.")
            break
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            if i < retries - 1:
                await asyncio.sleep(2 ** i)  # Exponential backoff
            else:
                logger.critical("Could not connect to the database after retries. Exiting application.")
                raise SystemExit("Database connection failed.")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    logger.info("Database connection closed.")

@app.post("/stats")
async def add_stats(analytics: Analytics):
    query = """
        INSERT INTO analytics (website_id, url, timestamp)
        VALUES (:website_id, :url, :timestamp)
    """
    values = {
        "website_id": analytics.website_id,
        "url": analytics.url,
        "timestamp": datetime.utcnow().replace(second=0, microsecond=0)  # Use datetime object
    }
    try:
        await database.execute(query=query, values=values)
        return {"message": "Stats added successfully"}
    except Exception as e:
        logger.error(f"Failed to insert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to add stats.")

@app.get("/events")
async def get_events():
    query = """
        SELECT * FROM analytics
    """
    results = await database.fetch_all(query=query)
    return {"events": [dict(result) for result in results]}

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/hello")
def read_hello():
    return {"message": "Hello world!"}

@app.get("/isalive")
def read_isalive():
    return {"message": "Alive"}

@app.get("/isready")
async def read_isready():
    try:
        await database.execute("SELECT 1")  # Simple query to check database readiness
        return {"message": "Ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"message": "Not ready", "details": str(e)}, 503