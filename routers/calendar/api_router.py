from fastapi import Depends, APIRouter, HTTPException
from auth import verify_token
from calendar_manager import CalendarManager
from routers.calendar.data_structures import Event, NotesIn

router = APIRouter(prefix="/calendar")

@router.get("/", response_model=dict[str, list[Event]])
async def get_calendar(user = Depends(verify_token)):

    db_handler = user.db_handler
    
    calendar_manager = CalendarManager(db_handler)

    return {
        "events": calendar_manager.get_all_events(user),
    }

@router.put("/event-notes", response_model=dict[str, list[Event]])
async def save_notes(event_id: int, params: NotesIn, user = Depends(verify_token)):

    db_handler = user.db_handler
    
    calendar_manager = CalendarManager(db_handler)

    calendar_sql = "SELECT id, user_sub, added_by from calendar where id=%s" % (event_id,)
    event = db_handler.fetchone(calendar_sql)

    if event is None:
        raise HTTPException(status_code=404, detail="Event does not exist.")
    
    update_sql = "update calendar set notes = '%s' where id=%s" % (params.notes, event_id,)
    db_handler.execute(update_sql, True)

    return {
        "events": calendar_manager.get_all_events(user),
    }

@router.delete("/event", response_model=dict[str, list[Event]])
async def delete_event(event_id: int, user = Depends(verify_token)):

    db_handler = user.db_handler
    
    calendar_sql = "SELECT id, user_sub, added_by from calendar where id=%s" % (event_id,)
    event = db_handler.fetchone(calendar_sql)

    if event is None:
        raise HTTPException(status_code=404, detail="Event does not exist.")
    
    authorised = False
    if user.is_admin is True:
        authorised = True
    elif event["user_sub"] == user.sub:
        authorised = True
    elif event["added_by"] == user.sub:
        authorised = True

    if authorised is False:
        raise HTTPException(status_code=403, detail="Not authorized.")
    
    delete_sql = "delete from calendar where id = %s" % (event_id)
    db_handler.execute(delete_sql, True)
    
    calendar_manager = CalendarManager(db_handler)

    return {
        "events": calendar_manager.get_all_events(user),
    }