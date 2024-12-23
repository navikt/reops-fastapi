import os
import logging
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from typing import List

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please check your environment variables.")

FORCE_SSL = os.getenv("FORCE_SSL", "false").lower() == "true"

connect_args = {}
if FORCE_SSL:
    connect_args = {
        "sslmode": "verify-ca",
        "sslrootcert": os.getenv("SSL_ROOT_CERT"),
        "sslcert": os.getenv("SSL_CERT"),
        "sslkey": os.getenv("SSL_KEY")
    }

# Configure connection engine with conditional SSL parameters
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # Configure connection pool for better performance
    pool_recycle=300,  # Connection pool recycle time
    connect_args=connect_args
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

    class Config:
        from_attributes = True

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        content={"message": "An internal server error occurred. Please try again later.", "details": str(exc)},
        status_code=500
    )

@app.on_event("startup")
async def startup():
    # No need for async task here, as engine creation handles connection
    engine.connect()
    logger.info("Database connection established.")

@app.on_event("shutdown")
def shutdown():
    if engine.pool:
        engine.pool.dispose()
        logger.info("Database connection pool disposed.")

@app.post("/api/send", response_model=AnalyticsModel)
async def add_stats(analytics: AnalyticsModel, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_analytics = Analytics(
        website_id=analytics.website_id,
        url=analytics.url,
        event_type=analytics.event_type,
        timestamp=datetime.utcnow().replace(second=0, microsecond=0)
    )
    try:
        db.add(new_analytics)
        db.commit()
        db.refresh(new_analytics)
        return new_analytics
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to insert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to add stats.")

@app.get("/api/data", response_model=List[AnalyticsModel])
async def get_events(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        results = db.query(Analytics).all()
        return [AnalyticsModel.from_orm(result) for result in results]
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events.")

@app.get("/api/isalive")
def read_isalive():
    return {"message": "Alive"}

@app.get("/api/isready")
def read_isready():
    return {"message": "Ready"}