from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import UUID4
import uuid as uuid_lib
from datetime import datetime
import logging
from .database import get_db
from .models import Events, Apps
from .schemas import EventsModel, AppsModel, EventsResponseModel, AppsResponseModel

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/send", response_model=EventsModel, tags=["Events"])
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

# Create a new app
@router.post("/api/apps", response_model=AppsModel, tags=["Apps"])
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

# Gets all apps
@router.get("/api/apps", response_model=List[AppsResponseModel], tags=["Apps"])
async def get_apps(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        results = db.query(Apps).all()
        return [AppsResponseModel.from_orm(result) for result in results]
    except Exception as e:
        logger.error(f"Failed to fetch apps: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch apps.")


# Gets all events
@router.get("/api/events", response_model=List[EventsResponseModel], tags=["Events"])
async def get_events(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        results = db.query(Events).all()
        return [EventsResponseModel.from_orm(result) for result in results]
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events.")

# Gets all events for a specific app
@router.get("/api/{app_id}/events", response_model=List[EventsResponseModel], tags=["Events"])
async def get_events_for_app(app_id: UUID4, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        results = db.query(Events).filter(Events.app_id == app_id).all()
        return [EventsResponseModel.from_orm(result) for result in results]
    except Exception as e:
        logger.error(f"Failed to fetch events for app {app_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events for app.")

@router.get("/api/isalive", tags=["Health Check"])
def read_isalive():
    return {"message": "Alive"}

@router.get("/api/isready", tags=["Health Check"])
def read_isready():
    return {"message": "Ready"}