from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class Leave(BaseModel):

    start: datetime
    end: datetime
    type: str = "annual_leave"


class EditLeave(Leave):

    start: Optional[datetime]
    end: Optional[datetime]
    type: Optional[str]

class LeaveOut(Leave):

    id: int
    metadata: Optional[dict]
    status: str
