from pydantic import BaseModel
from typing import Optional, List
from data_structures import OrderUpdateOut

class UpdatesOut(BaseModel):

    orders: List[OrderUpdateOut]
    unread_whatsapps: int = 0
    repeats: int = 0