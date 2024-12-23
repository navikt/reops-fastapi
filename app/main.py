import os
import logging
import asyncio
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import ssl
from typing import List

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
SKIP_DB_CHECK = os.getenv("SKIP_DB_CHECK", "false").lower() == "true"

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please check your environment variables.")

# Configure connection engine with SSL parameters
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # Configure connection pool for better performance
    pool_recycle=300,  # Connection pool recycle time
    connect_args={
        "sslmode": "verify-ca",
        "sslrootcert": "/var/run/secrets/nais.io/sqlcertificate/root-cert.pem",
        "sslcert": "/var/run/secrets/nais.io/sqlcertificate/cert.pem",
        "sslkey": "/var/run/secrets/nais.io/sqlcertificate/key.pem"
    }
)

# Create a database session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

# Model definition for database table
Base = declarative_base()

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True)
    website_id = Column(Integer)
    url = Column(String)
    event_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class AnalyticsModel(BaseModel):
    website_id: int
    url: str
    event_type: str
    timestamp: datetime

    class Config:
        orm_mode = True


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
    check_ssl_files()
    if not SKIP_DB_CHECK:
        # No need for async task here, as engine creation handles connection
        engine.connect()
        logger.info("Database connection established.")


@app.on_event("shutdown")
def shutdown():
    if engine.pool:
        engine.pool.dispose()
        logger.info("Database connection pool disposed.")


async def ensure_connection():
    # No need for connection logic as engine manages it
    pass


@app.post("/api/send", response_model=AnalyticsModel)
async def add_stats(analytics: AnalyticsModel, background_tasks: BackgroundTasks):
    background_tasks.add_task(ensure_connection)
    query = """
        INSERT INTO analytics (website_id, url, event_type, timestamp)
        VALUES (:website_id, :url, :event_type, :timestamp)
    """
    values = {
        "website_id": analytics.website_id,
        "url": analytics.url,
        "event_type": analytics.event_type,
        "timestamp": datetime.utcnow().replace(second=0, microsecond=0)
    }
    try:
        await database.execute(query=query, values=values)
        return analytics
    except Exception as e:
        logger.error(f"Failed to insert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to add stats.")


@app.get("/api/data", response_model=List[AnalyticsModel])
async def get_events(background_tasks: BackgroundTasks):
    background_tasks.add_task(ensure_connection)
    query = "SELECT * FROM analytics"
    results = await database.fetch_all(query=query)
    return [AnalyticsModel.from_orm(result) for result in results]


@app.get("/api/isalive")
def read_isalive():
    return {"message": "Alive"}


@app.get("/api/isready")
def read_isready():
    return {"message": "Ready"}