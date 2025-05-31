from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class AddEvent(BaseModel):

    start: datetime
    end: datetime
    title: Optional[str]
    event_type: str
    notes: str
    metadata: Optional[dict]
    days: int = 0

class Event(BaseModel):
    
    start: datetime
    end: datetime
    title: str
    id: int
    background_colour: str
    status: str
    can_delete: bool = False
    site: str
    notes: str
    type: str

class NotesIn(BaseModel):

    notes: str
