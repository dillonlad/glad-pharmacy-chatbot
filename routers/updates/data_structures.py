from pydantic import BaseModel
from typing import Optional, List

class ItemOut(BaseModel):
    item_name: str
    item_sku: int
    quantity: int

class OrderUpdateOut(BaseModel):
    id: int
    amount_paid: float
    address: str
    name: str
    email: Optional[str]
    items: list[ItemOut]

class UpdatesOut(BaseModel):
    orders: List[OrderUpdateOut]