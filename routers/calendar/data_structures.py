from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from data_structures import EventBase

class AddEvent(BaseModel):

    start: datetime
    end: datetime
    title: Optional[str]
    event_type: str
    notes: str
    metadata: Optional[dict]
    days: int = 0

class Event(EventBase):
    
    class Config:
        pass

class NotesIn(BaseModel):

    notes: str
