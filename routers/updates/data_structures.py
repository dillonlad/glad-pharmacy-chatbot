from pydantic import BaseModel
from typing import List
from data_structures import OrderUpdateOut

class UpdatesOut(BaseModel):

    orders: List[OrderUpdateOut]
    unread_whatsapps: int = 0
    repeats: int = 0
    contact_forms: int = 0
    unread_voicemails: int = 0

