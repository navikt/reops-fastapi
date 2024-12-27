from typing import Optional
from pydantic import BaseModel, UUID4, Field
from sqlalchemy import Boolean
from datetime import datetime

class EventsModel(BaseModel):
    app_id: UUID4
    url_host: str
    url_path: str
    url_query: str
    event_name: str

    class Config:
        from_attributes = True

class EventsResponseModel(BaseModel):
    event_id: UUID4
    app_id: UUID4
    url_host: str
    url_path: str
    url_query: str
    event_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class AppsModel(BaseModel):
    app_name: str

class AppsUpdateModel(BaseModel):
    app_name: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
         from_attributes = True

class AppsResponseModel(BaseModel):
    app_id: UUID4
    app_name: str
    is_active: bool = Field(default=True)
    created_at: datetime

    class Config:
        from_attributes = True