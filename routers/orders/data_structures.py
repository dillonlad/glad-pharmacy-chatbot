from pydantic import BaseModel

class ItemTotal(BaseModel):

    order_item_name: str
    item_total: int

class MetricsOut(BaseModel):

    total: int
    popular: list[ItemTotal]