from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class LeaveDecision(Enum):

    APPROVED = "Approved"
    REJECTED = "Rejected"


class Leave(BaseModel):

    start: datetime
    end: datetime
    type: str = "annual_leave"
    notes: str = ""


class EditLeave(Leave):

    start: Optional[datetime]
    end: Optional[datetime]
    type: Optional[str]

class LeaveOut(Leave):

    id: int
    metadata: Optional[dict]
    status: str

class NotesIn(BaseModel):

    notes: Optional[str]
