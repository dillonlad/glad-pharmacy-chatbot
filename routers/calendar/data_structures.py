from pydantic import BaseModel
from datetime import datetime

class Event(BaseModel):
    
    start: datetime
    end: datetime
    title: str
    id: int
