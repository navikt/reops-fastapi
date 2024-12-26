import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

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

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    pool_recycle=300,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()