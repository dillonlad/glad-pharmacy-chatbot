from pydantic import BaseModel

class ItemTotal(BaseModel):

    order_item_name: str
    item_total: int

class MetricsOut(BaseModel):

    total: int
    popular: list[ItemTotal]


class CancelOrderIn(BaseModel):

    reason: str | None = None
    out_of_stock_item_skus: list[int] = []