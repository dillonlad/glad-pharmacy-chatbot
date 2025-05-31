from fastapi import Depends, APIRouter, HTTPException
from auth import verify_token
from calendar_manager import CalendarManager
from routers.calendar.data_structures import Event, NotesIn, AddEvent

router = APIRouter(prefix="/calendar")

@router.get("/", response_model=dict[str, list[Event]])
async def get_calendar(user = Depends(verify_token)):

    db_handler = user.db_handler
    
    calendar_manager = CalendarManager(db_handler)

    return {
        "events": calendar_manager.get_all_events(user),
    }

@router.post("/event", response_model=dict[str, list[Event]])
async def add_event(
    user_sub: str,
    params: AddEvent,
    user = Depends(verify_token),
):
    
    db_handler = user.db_handler
    
    event_type_sql = "select id, description from event_types where name = '%s'" % (params.event_type)
    event_type = db_handler.fetchone(event_type_sql)
    if event_type is None:
        raise HTTPException(status_code=404, detail="No matching event type.")
    
    event_type_id = event_type["id"]

    if user.sub != user_sub:

        matching_user = user.cognito_client.get_user_from_sub(user_sub)
        
        if matching_user: 
            user_attr = matching_user.get("Attributes", [])
            user_name = next((_attr["Value"] for _attr in user_attr if _attr["Name"] == "name"), None)
            user_username = matching_user.get("Username", "")
        else:
            user_name = user.name
            user_username = user.email

        user_groups_response = user.cognito_client.admin_list_groups_for_user(user_username)
        groups = user_groups_response.get("Groups", [])
        user_group_names = [_group["GroupName"] for _group in groups if _group["GroupName"] not in ["glad_admin", "sites"]]
        _site = user_group_names[0] if len(user_group_names) == 1 else "all"
    else:
        user_name = user.name
        _site = user.groups[0] if len(user.groups) == 1 else "all"

    title = params.title
    if params.title is None:
        title = f"{event_type["description"]} - {user_name}"
    
    calendar_sql = """insert into calendar (event_type_id, user_sub, site,
     title, notes, metadata, start, end, days, status, added_by) values (
     %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s')""" % (
         event_type_id, user_sub, _site, title, params.notes, 
         params.metadata if params.metadata else '{}', params.start, params.end, params.days, 'Approved', user.sub
     )
    
    db_handler.execute(calendar_sql, commit=True)
    
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