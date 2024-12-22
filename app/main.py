import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databases import Database
import datetime
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")

database = Database(DATABASE_URL)
app = FastAPI()

class Analytics(BaseModel):
    website_id: int
    url: str

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

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