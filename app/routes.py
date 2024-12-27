from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid as uuid_lib
from datetime import datetime
import logging
from .database import get_db
from .models import Events, Apps
from .schemas import EventsModel, AppsModel

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/send", response_model=EventsModel)
async def add_stats(events: EventsModel, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_events = Events(
        app_id=uuid_lib.UUID(str(events.app_id)),
        event_name=events.event_name,
        url_host=events.url_host,
        url_path=events.url_path,
        url_query=events.url_query,
        created_at=datetime.utcnow().replace(microsecond=0)
    )
    try:
        db.add(new_events)
        db.commit()
        db.refresh(new_events)
        return new_events
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to insert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to add stats.")

@router.post("/api/apps", response_model=AppsModel)
async def add_stats(apps: AppsModel, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_app = Apps(
        app_name=apps.app_name,
        created_at=datetime.utcnow().replace(microsecond=0)
    )
    try:
        db.add(new_app)
        db.commit()
        db.refresh(new_app)
        return new_app
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to insert stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to add stats.")

@router.get("/api/data", response_model=List[EventsModel])
async def get_events(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        results = db.query(Events).all()
        return [EventsModel.from_orm(result) for result in results]
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events.")

@router.get("/api/isalive")
def read_isalive():
    return {"message": "Alive"}

@router.get("/api/isready")
def read_isready():
    return {"message": "Ready"}