from typing import Optional

from pydantic import BaseModel
from datetime import date

class CashUpAccessRequest(BaseModel):
    site: str
    code: int

class CashSheetOut(BaseModel):
    cash_sheet_date: date
    z_vat: float
    five_vat: float
    std_vat: float
    till_total: float
    petty_cash: float
    card_total: float
    total_sales: float
    cash_total: float
    cash_error: float

class CashSheetsOut(BaseModel):
    cash_sheets: list[CashSheetOut]
    total_z_vat: float
    total_five_vat: float
    total_std_vat: float
    total_till_total: float
    total_petty_cash: float
    total_card_total: float
    total_total_sales: float
    total_cash_total: float
    total_cash_error: float


class CashUpAccess(BaseModel):

    token: Optional[str]

class CashUpIn(BaseModel):

    token: str
    z_vat: float
    five_vat: float
    std_vat: float
    till_total: float
    petty_cash: float
    card_total: float

    @property
    def total_sales(self):
        return self.z_vat + self.five_vat + self.std_vat

    @property
    def cash_total(self):
        return self.total_sales - self.card_total

    @property
    def cash_error(self):
        expected_till_total = self.cash_total - self.petty_cash
        return self.till_total - expected_till_total