from fastapi import Depends, APIRouter
import pytz
from auth import verify_token
from routers.calendar.data_structures import Event

router = APIRouter(prefix="/calendar")

@router.get("/", response_model=dict[str, list[Event]])
async def get_calendar(user = Depends(verify_token)):

    db_handler = user.db_handler
    sql = "select calendar.id, calendar.title, calendar.start, calendar.end from calendar"

    events = db_handler.fetchall(sql)
    tz_events = []
    for event in events:
        new_event = event
        new_event["start"] = new_event["start"].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
        new_event["end"] = new_event["end"].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
        tz_events.append(new_event)


    return {
        "events": tz_events,
    }