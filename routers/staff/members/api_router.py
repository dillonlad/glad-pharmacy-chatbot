from datetime import datetime
from typing import Union
from fastapi import APIRouter, Depends, HTTPException
import pytz
from calendar_manager import CalendarManager
from cognito_user import EditableAttribute
from routers.staff.members.data_structures import MembersOut
from auth import verify_token

router = APIRouter()

@router.get("/", response_model=MembersOut)
async def get_staff_members(
    add_calendar: bool = False,
    user=Depends(verify_token)
):
    
    db_handler = user.db_handler
    calendar_manager = CalendarManager(db_handler)

    current_dt = datetime.now(tz=pytz.utc)

    from_year = current_dt.year
    if current_dt.month < 4:
        from_year -= 1
        to_year = current_dt.year
    else:
        to_year = current_dt.year + 1

    tz = pytz.timezone('Europe/London')

    month_start_dt = datetime(from_year, 4, 1, 0, 0, tzinfo=tz)
    month_end_dt = datetime(to_year, 4, 1, 0, 0, tzinfo=tz)

    print(month_start_dt)
    print(month_end_dt)

    # repeat sql query for month
    month_utc = month_start_dt.astimezone(pytz.UTC)
    end_utc = month_end_dt.astimezone(pytz.UTC)

    members = user.get_colleagues(add_calendar)
    for member in members:
        al_used = calendar_manager.get_time_remaining(month_utc, end_utc, member["sub"])
        member["al_used"] = al_used
        member["al_remaining"] = round(member["al_entitlement"] - al_used, 2)

    return {
        "is_admin": user.is_admin,
        "members": members
    }

@router.put("/", response_model=MembersOut)
async def edit_staff_member(
    username: str,
    params: dict[EditableAttribute, Union[int, float, str]],
    user=Depends(verify_token)
):
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorised.")
    
    updated_attributes = {
        attr.value: attr_value
        for attr, attr_value in params.items()
        if attr_value not in [None, ""]
    }
    formatted_attrs = [{"Name": f"custom:{k}" if k not in ["name", "sub", "email"] else k, "Value": v} for k, v in updated_attributes.items()]

    user.cognito_client.update_user_attributes(
        username=username,
        new_attrs=formatted_attrs
    )

    return {
        "is_admin": user.is_admin,
        "members": user.get_colleagues(True)
    }

@router.get("/al-remaining", response_model=dict[str, float])
async def get_al_remaining(
    user_sub: str,
    user=Depends(verify_token)
):
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorised.")
    
    db_handler = user.db_handler
    calendar_manager = CalendarManager(db_handler)

    current_dt = datetime.now(tz=pytz.utc)

    from_year = current_dt.year
    if current_dt.month <= 4:
        from_year -= 1
        to_year = current_dt.year
    else:
        to_year = current_dt.year + 1

    tz = pytz.timezone('Europe/London')

    month_start_dt = datetime(from_year, 4, 1, 0, 0, tzinfo=tz)
    month_end_dt = datetime(to_year, 4, 1, 0, 0, tzinfo=tz)

    print(month_start_dt)
    print(month_end_dt)

    # repeat sql query for month
    month_utc = month_start_dt.astimezone(pytz.UTC)
    end_utc = month_end_dt.astimezone(pytz.UTC)

    return {
        "al_remaining": calendar_manager.get_time_remaining(month_utc, end_utc, user_sub),
    }