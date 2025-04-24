from typing import Optional
from pydantic import BaseModel

class Member(BaseModel):

    sub: str
    name: str
    email: str
    sites: Optional[list[str]] = []
    admin: Optional[bool] = False
    al_entitlement: float = 25.0
    al_used: float = 0.0
    al_remaining: float = 25.0
    sickness_used: int = 0
    username: str

class MembersOut(BaseModel):

    is_admin: bool
    members: list[Member]