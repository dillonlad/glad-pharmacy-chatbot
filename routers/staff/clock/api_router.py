from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import json
from auth import verify_token
from calendar_manager import CalendarManager
from routers.staff.clock.data_structures import Leave, LeaveOut, LeaveDecision, NotesIn
from ses_client import SESClient, SESTemplates
from wp_db_handler import DBHandler
import math
import pytz

router = APIRouter(prefix="/clock")


@router.post("/leave", response_model=dict)
async def book_leave(
    params: Leave,
    background_tasks: BackgroundTasks,
    user_sub: str = None,
    user=Depends(verify_token),
):
    
    db_handler: DBHandler = user.db_handler
    if user_sub is None:
        user_sub = user.sub
    
    event_type_sql = "SELECT id, description from event_types where name = '%s'" % (params.type,)
    event_type = db_handler.fetchone(event_type_sql)
    if event_type is None:
        raise HTTPException(status_code=404, detail="No event type found.")
    
    date_diff = params.end - params.start

    number_seconds = date_diff.seconds
    number_of_days = number_seconds / 86400
    days_taken = math.ceil(number_of_days * 2) / 2
    days_taken = float(date_diff.days) + days_taken
    
    start = params.start.strftime("%y-%m-%d %H:%M")
    end = params.end.strftime("%y-%m-%d %H:%M")

    existing_calendar_sql = "SELECT id from calendar where user_sub='%s' and ('%s' between start and end or '%s' between start and end) and status != 'Rejected'" % (user_sub, start, end,)
    existing_calendar = db_handler.fetchone(existing_calendar_sql)
    if existing_calendar is not None:
        raise HTTPException(status_code=400, detail="Overlaps existing schedule.")
    
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

    if user.is_admin is False:
        # Users must be colleagues for them to book for one another. Can just call get admin user
        # for current site

        leave_status = "Pending"

        _tz = pytz.timezone("Europe/London")

        start_local = params.start.astimezone(_tz)
        end_local = params.end.astimezone(_tz)

        ses_client = SESClient()
        email_data = {
            "admin_name": "",
            "staff_name": user_name,
            "start_date": start_local.strftime("%d/%m/%Y"),
            "end_date": end_local.strftime("%d/%m/%Y"),
            "notes": params.notes if params.notes is not None else ""
        }
        background_tasks.add_task(
            ses_client.send_managers_email,
            user,
            SESTemplates.ANNUAL_LEAVE_REQUEST,
            email_data,
        )

    else:

        leave_status = "Approved"

    title = f"{event_type['description']} - {user_name}"
    calendar_sql = "INSERT INTO calendar (event_type_id, user_sub, title, start, end, status, added_by, site, notes, days) VALUES (%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s)" % (event_type["id"], user_sub, title, start, end, leave_status, user.sub, _site, params.notes, days_taken,)
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
    background_tasks: BackgroundTasks,
    user=Depends(verify_token),
):
    
    db_handler = user.db_handler
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to do this")
        
    calendar_sql = "SELECT id, user_sub, start, end, added_by from calendar where status='Pending' and id=%s" % (event_id,)
    event = db_handler.fetchone(calendar_sql)

    if event is None:
        raise HTTPException(status_code=404, detail="Event does not exist.")
    
    if user.is_colleague(event["user_sub"]) is False and event["user_sub"] != user.sub and event["added_by"] != user.sub:
        raise HTTPException(status_code=403, detail="Not colleagues.")
    
    metadata_new = {"reason": notes.notes} if notes.notes is not None else {"reason": ""}
    update_sql = "update calendar set status='%s', metadata='%s' where id = %s" % (decision.value, json.dumps(metadata_new), event_id,)
    db_handler.execute(update_sql, True)

    email_template = SESTemplates.ANNUAL_LEAVE_APPROVED if decision == LeaveDecision.APPROVED else SESTemplates.ANNUAL_LEAVE_REJECTED
    _tz = pytz.timezone("Europe/London")

    start_local = event["start"].astimezone(_tz)
    end_local = event["end"].astimezone(_tz)
    template_data = {
        "start_date": start_local.strftime("%d/%m/%Y"),
        "end_date": end_local.strftime("%d/%m/%Y"),
        "notes": metadata_new["reason"]
    }

    calendar_manager = CalendarManager(db_handler)
    ses_client = SESClient()
    background_tasks.add_task(
        ses_client.send_user_email,
        user.cognito_client,
        event["user_sub"],
        email_template,
        template_data,
    )

    return {
        "events": calendar_manager.get_all_events(user),
        }