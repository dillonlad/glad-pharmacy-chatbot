import os
import base64

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from auth import verify_token
from config import get_config
from components import redis_client
from secrets_client import SecretsManagerClient
from wp_db_handler import DBHandler
from routers.staff.cash.data_structures import CashSheetsOut, CashUpAccess, CashUpAccessRequest, CashUpIn
from datetime import date

router = APIRouter(prefix="/cash")

@router.post("/access", response_model=CashUpAccess)
async def cash_up_access(params: CashUpAccessRequest, user=Depends(verify_token),):
    """
    Grants access to cash up
    """

    secrets_client = SecretsManagerClient()
    print(user.groups)
    if params.site not in user.groups:
        raise HTTPException(status_code=403, detail="User has no access to site")

    config = get_config()
    codes = secrets_client.get_secret_dict(config.cash_up_secret_arn)
    print(codes)
    if codes is None or (site_code := codes.get(params.site, None)) is None:
        raise HTTPException(status_code=403, detail="Cannot find code")

    if int(site_code) != (params.code):
        raise HTTPException(status_code=403, detail="Invalid code")

    access_token_bytes = os.urandom(32)
    access_token_str = base64.b64encode(access_token_bytes).decode()

    redis_client.set(access_token_str, params.site, ex=1800)

    return CashUpAccess(
        token=access_token_str,
    )

@router.get("/sheet", response_model=CashSheetsOut)
async def cash_sheets(
    token: str,
    start_date: date,
    end_date: date,
    user=Depends(verify_token),
):
    
    cached_site = redis_client.get(token)
    if cached_site is None:
        raise HTTPException(status_code=404, detail="No cashup request found")
    
    db_handler: DBHandler = user.db_handler
    current_date = date.today()
    if end_date > current_date or start_date > current_date or start_date > end_date:
        raise HTTPException(status_code=422, detail="Invalid input date")

    sql = """select cash_sheet_date, z_vat, five_vat, std_vat, total_sales, till_total, petty_cash,
            card_total, cash_total, cash_error from cash_sheets where site = %s and
            cash_sheet_date between %s and %s"""

    cash_sheet_data = db_handler.fetchall_params(sql, (cached_site, start_date, end_date,),)
    cash_sheet_response = CashSheetsOut(
        cash_sheets=cash_sheet_data, 
        total_z_vat=0.0,
        total_card_total=0.0,
        total_cash_error=0.0,
        total_cash_total=0.0,
        total_five_vat=0.0,
        total_petty_cash=0.0,
        total_std_vat=0.0,
        total_till_total=0.0,
        total_total_sales=0.0,
    )
    for cash_sheet in cash_sheet_data:
        cash_sheet_response.total_z_vat += cash_sheet["z_vat"]
        cash_sheet_response.total_card_total += cash_sheet["card_total"]
        cash_sheet_response.total_cash_error += cash_sheet["cash_error"]
        cash_sheet_response.total_cash_total += cash_sheet["cash_total"]
        cash_sheet_response.total_five_vat += cash_sheet["five_vat"]
        cash_sheet_response.total_petty_cash += cash_sheet["petty_cash"]
        cash_sheet_response.total_std_vat += cash_sheet["std_vat"]

    return cash_sheet_response

@router.post("/up", response_model=dict)
async def cash_up(
    params: CashUpIn,
    background_tasks: BackgroundTasks,
    user=Depends(verify_token),
):

    cached_site = redis_client.get(params.token)
    if cached_site is None:
        raise HTTPException(status_code=404, detail="No cashup request found")

    db_handler: DBHandler = user.db_handler
    current_date = date.today()

    # 1. Check if a cash sheet already exists for today using parameterized fetchone
    check_sql = "SELECT id FROM cash_sheets WHERE cash_sheet_date = %s LIMIT 1"
    existing_sheet = db_handler.fetchone_params(check_sql, (current_date,))

    if existing_sheet:
        # 2. Overwrite (Update) existing record for today
        cash_sql = """
                    UPDATE cash_sheets 
                    SET z_vat = %s, five_vat = %s, std_vat = %s,
                        total_sales = %s, till_total = %s, 
                        petty_cash = %s, card_total = %s, cash_total = %s, 
                        cash_error = %s
                    WHERE cash_sheet_date = %s AND site = %s
                   """
        sql_params = (
            params.z_vat,
            params.five_vat,
            params.std_vat,
            params.total_sales,
            params.till_total,
            params.petty_cash,
            params.card_total,
            params.cash_total,
            params.cash_error,
            current_date,
            cached_site,
        )
    else:
        # 3. Insert new record for today
        cash_sql = """
                    INSERT INTO cash_sheets (site, cash_sheet_date, z_vat, five_vat, std_vat,
                                            total_sales, till_total, 
                                            petty_cash, card_total, cash_total, 
                                            cash_error)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   """
        sql_params = (
            cached_site,
            current_date,
            params.z_vat,
            params.five_vat,
            params.std_vat,
            params.total_sales,
            params.till_total,
            params.petty_cash,
            params.card_total,
            params.cash_total,
            params.cash_error,
        )

    db_handler.execute_params(cash_sql, sql_params, commit=True)
    
    return {
        "success": True,
    }