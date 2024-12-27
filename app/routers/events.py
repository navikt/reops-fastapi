from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import UUID4
import uuid as uuid_lib
from datetime import datetime
import logging
from ..database import get_db
from ..models import Events
from ..schemas import EventsModel, EventsResponseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Send events
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

# Get all events or filter by app_id, url_host, url_path, url_query, event_name (partial match)
@router.get("/api/events", response_model=List[EventsResponseModel], tags=["Events"])
async def get_events(
    app_id: Optional[UUID4] = Query(None),
    url_host: Optional[str] = Query(None),
    url_path: Optional[str] = Query(None),
    url_query: Optional[str] = Query(None),
    event_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Events)
        if app_id:
            query = query.filter(Events.app_id == app_id)
        if url_host:
            query = query.filter(Events.url_host.like(f"%{url_host}%"))
        if url_path:
            query = query.filter(Events.url_path.like(f"%{url_path}%"))
        if url_query:
            query = query.filter(Events.url_query.like(f"%{url_query}%"))
        if event_name:
            query = query.filter(Events.event_name.like(f"%{event_name}%"))
        results = query.all()
        if not results:
            raise HTTPException(status_code=404, detail="Events not found")
        return [EventsResponseModel.from_orm(result) for result in results]
    except Exception as e:
        logger.error(f"Failed to fetch events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events.")