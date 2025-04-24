from pydantic import BaseModel
from datetime import datetime

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
