import os
import logging
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import uuid as uuid_lib
from pydantic import UUID4

load_dotenv()
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=False,
    allow_methods=["GET", "POST"],  # Allows all methods
    allow_headers=["Content-Type"],  # Allows all headers
)

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

# Model definition for database table
Base = declarative_base()

class Analytics(Base):
    __tablename__ = "analytics"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    website_id = Column(String)
    url_host = Column(String)
    url_path = Column(String)
    url_search = Column(String)
    event_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AnalyticsModel(BaseModel):
    website_id: UUID4
    url_host: str
    url_path: str
    url_search: str
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
        website_id=uuid_lib.UUID(str(analytics.website_id)),
        event_type=analytics.event_type,
        url_host=analytics.url_host,
        url_path=analytics.url_path,
        url_search=analytics.url_search,
        created_at=datetime.utcnow().replace(microsecond=0)
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