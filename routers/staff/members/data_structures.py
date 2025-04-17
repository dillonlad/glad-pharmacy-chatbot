from typing import Optional
from pydantic import BaseModel

class Member(BaseModel):

    sub: str
    name: str
    email: str
    sites: Optional[list[str]] = []
    admin: Optional[bool] = False
    al_entitlement: int = 25
    al_used: int = 0
    al_remaining: int = 25
    sickness_used: int = 0
    username: str

class MembersOut(BaseModel):

    is_admin: bool
    members: list[Member]