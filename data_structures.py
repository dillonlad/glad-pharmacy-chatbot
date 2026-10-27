from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItemOut(BaseModel):
    item_name: str
    item_sku: int
    quantity: int
    item_product_id: int

class OrderUpdateOut(BaseModel):
    id: int
    amount_paid: float
    transaction_id: str
    address: Optional[str]
    name: str
    email: Optional[str]
    items: list[ItemOut]
    created: datetime

class EventBase(BaseModel):
    
    start: datetime
    end: datetime
    title: str
    id: int
    background_colour: str
    status: str
    can_delete: bool = False
    site: str
    notes: str
    type: str

class CachedEvents(BaseModel):
    events: list[EventBase]