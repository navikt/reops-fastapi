from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
from ..database import get_db
from ..models import Apps
from ..schemas import AppsModel, AppsResponseModel

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/apps", response_model=AppsModel, tags=["Apps"])
async def add_app(apps: AppsModel, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
        logger.error(f"Failed to insert app: {e}")
        raise HTTPException(status_code=500, detail="Failed to add app.")

@router.get("/api/apps", response_model=List[AppsResponseModel], tags=["Apps"])
async def get_apps(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        results = db.query(Apps).all()
        return [AppsResponseModel.from_orm(result) for result in results]
    except Exception as e:
        logger.error(f"Failed to fetch apps: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch apps.")