import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databases import Database
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
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
                raise e

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
        "timestamp": datetime.datetime.utcnow()  # Use datetime object
    }
    await database.execute(query=query, values=values)
    return {"message": "Stats added successfully"}

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
def read_isready():
    return {"message": "Ready"}