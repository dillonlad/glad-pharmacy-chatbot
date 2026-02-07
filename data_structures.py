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
    