from typing import Optional
from pydantic import BaseModel

class Member(BaseModel):

    sub: str
    name: str
    email: str
    sites: Optional[list[str]] = []
    admin: Optional[bool] = False