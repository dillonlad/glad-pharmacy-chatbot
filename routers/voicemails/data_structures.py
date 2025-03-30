from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VoicemailOut(BaseModel):

    site_name: str
    inbox_name: str
    number: str
    filename: str
    presigned_url: Optional[str]
    expiry: Optional[int]
    created: datetime
    voicemail_id: int
    