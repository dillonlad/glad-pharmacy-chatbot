from pydantic import BaseModel
from typing import List, Optional
from data_structures import OrderUpdateOut

class UpdatesOut(BaseModel):

    orders: List[OrderUpdateOut]
    unread_whatsapps: int = 0
    repeats: int = 0
    contact_forms: int = 0
    unread_voicemails: int = 0
    is_admin: bool = False
    sites: list[str]

