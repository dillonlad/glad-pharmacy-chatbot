from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from routers.staff.clock.data_structures import Leave, LeaveOut
from wp_db_handler import DBHandler


router = APIRouter(prefix="/clock")


@router.post("/leave", response_model=LeaveOut)
async def book_leave(
    params: Leave,
    user_sub: str = None,
    user=Depends(verify_token),
):
    
    db_handler: DBHandler = user.db_handler
    if user_sub is None:
        user_sub = user.sub

    users_sql = "SELECT id, site_id from dashboard_users where active=1 and `sub`='%s'" % (user_sub,)
    dashboard_user = db_handler.fetchone(users_sql)

    if dashboard_user is None:
        raise HTTPException(status_code=404, detail="No user found.")
    
    event_type_sql = "SELECT id, description from event_types where name = '%s'" % (params.type,)
    event_type = db_handler.fetchone(event_type_sql)
    if event_type is None:
        raise HTTPException(status_code=404, detail="No event type found.")
    
    start = params.start.strftime("%y-%m-%d %H:%M")
    end = params.end.strftime("%y-%m-%d %H:%M")

    existing_calendar_sql = "SELECT id from calendar where user_sub='%s' and ('%s' between start and end or '%s' between start and end)" % (user_sub, start, end,)
    existing_calendar = db_handler.fetchone(existing_calendar_sql)
    if existing_calendar is not None:
        raise HTTPException(status_code=400, detail="Overlaps existing schedule.")
    
    title = f"{event_type['description']} - {user.name}"
    calendar_sql = "INSERT INTO calendar (event_type_id, user_sub, title, start, end, status) VALUES (%s, '%s', '%s', '%s', '%s', 'Pending')" % (event_type["id"], user_sub, title, start, end,)
    db_handler.execute(calendar_sql, True)
    
    return LeaveOut(
        id=db_handler._cursor.lastrowid, 
        metadata=None, 
        status="Pending",
        start=params.start,
        end=params.end,
        type=params.type,
    )


@router.delete("/leave", response_model=dict)
async def cancel_leave():
    pass

@router.put("/leave", response_model=dict)
async def edit_leave():
    pass