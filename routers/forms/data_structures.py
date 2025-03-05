from pydantic import BaseModel
from typing import Optional
from enum import Enum

class FormType(Enum):

    REPEATS="repeat-prescription-sign-up"

class FormEntryOut(BaseModel):

    id: int
    form_name: str
    file_path: str
    metadata: Optional[dict]
    presigned_url: str