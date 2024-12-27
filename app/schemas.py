from pydantic import BaseModel, UUID4
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


class AppsResponseModel(BaseModel):
    app_id: UUID4
    app_name: str
    created_at: datetime

    class Config:
        from_attributes = True