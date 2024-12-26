from pydantic import BaseModel, UUID4

class EventsModel(BaseModel):
    app_id: UUID4
    url_host: str
    url_path: str
    url_search: str
    event_name: str

    class Config:
        from_attributes = True

class AppsModel(BaseModel):
    app_name: str