from fastapi import APIRouter, Depends, HTTPException
import json
from auth import verify_token
from calendar_manager import CalendarManager
from routers.staff.clock.data_structures import Leave, LeaveOut, LeaveDecision, NotesIn
from wp_db_handler import DBHandler


router = APIRouter(prefix="/clock")


@router.post("/leave", response_model=dict)
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

    existing_calendar_sql = "SELECT id from calendar where user_sub='%s' and ('%s' between start and end or '%s' between start and end) and status != 'Rejected'" % (user_sub, start, end,)
    existing_calendar = db_handler.fetchone(existing_calendar_sql)
    if existing_calendar is not None:
        raise HTTPException(status_code=400, detail="Overlaps existing schedule.")
    
    if user.sub != user_sub:
        response = user.cognito_client.list_users()
        cognito_users = response.get("Users", None)
        if cognito_users is None:
            raise HTTPException(status_code=403, detail="No users")
        matching_user = next(
                _user for _user in cognito_users
                if any(attr["Name"] == "sub" and attr["Value"] == user_sub for attr in _user["Attributes"])
            )

        user_attr = matching_user.get("Attributes", [])
        user_name = next((_attr["Value"] for _attr in user_attr if _attr["Name"] == "name"), None)
    else:
        user_name = user.name

    title = f"{event_type['description']} - {user_name}"
    _site = user.groups[0] if len(user.groups) == 1 else "all"
    calendar_sql = "INSERT INTO calendar (event_type_id, user_sub, title, start, end, status, added_by, site, notes) VALUES (%s, '%s', '%s', '%s', '%s', 'Pending', '%s', '%s', '%s')" % (event_type["id"], user_sub, title, start, end, user.sub, _site, params.notes,)
    db_handler.execute(calendar_sql, True)

    calendar_manager = CalendarManager(db_handler)
    
    return {
        "events": calendar_manager.get_all_events(user),
    }


@router.delete("/leave", response_model=dict)
async def cancel_leave():
    pass

@router.put("/leave", response_model=dict)
async def confirm_leave(
    event_id: int,
    decision: LeaveDecision,
    notes: NotesIn,
    user=Depends(verify_token),
):
    
    db_handler = user.db_handler
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to do this")
    
    calendar_sql = "SELECT id, user_sub, added_by from calendar where status='Pending' and id=%s" % (event_id,)
    event = db_handler.fetchone(calendar_sql)

    if event is None:
        raise HTTPException(status_code=404, detail="Event does not exist.")
    
    if user.is_colleague(event["user_sub"]) is False and event["user_sub"] != user.sub and event["added_by"] != user.sub:
        raise HTTPException(status_code=403, detail="Not colleagues.")
    
    metadata_new = {"reason": notes.notes} if notes.notes is not None else {"reason": ""}
    update_sql = "update calendar set status='%s', metadata='%s' where id = %s" % (decision.value, json.dumps(metadata_new), event_id,)
    db_handler.execute(update_sql, True)

    calendar_manager = CalendarManager(db_handler)
    return {
        "events": calendar_manager.get_all_events(user),
        }