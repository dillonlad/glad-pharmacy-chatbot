import pytz
from datetime import datetime

from auth import CognitoClient
from wp_db_handler import DBHandler


class CalendarManager:

    def __init__(self, db_handler: DBHandler):
        self._db_handler = db_handler

    @staticmethod
    def first_datetime_of_month(year: int, month: int) -> datetime:
        return datetime(year=year, month=month, day=1, tzinfo=pytz.timezone("Europe/London")).astimezone(pytz.timezone("utc"))

    def get_all_events(self, user):

        sql = "select calendar.id, calendar.notes, calendar.title, calendar.site, calendar.status, calendar.start, calendar.end, event_types.background_colour, event_types.name as `type`, calendar.user_sub, calendar.added_by " \
          "from calendar inner join event_types on calendar.event_type_id=event_types.id and calendar.status != 'Rejected'" \
          " and calendar.site in ('all', {})".format(",".join(["'{}'".format(group_name) for group_name in user.groups]))

        events = self._db_handler.fetchall(sql)
        tz_events = []
        for event in events:
            new_event = event
            new_event["start"] = new_event["start"].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
            new_event["end"] = new_event["end"].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
            tz_events.append(new_event)
            new_event["can_delete"] = False
            if (user and (user.sub == event["user_sub"] or user.sub == event["added_by"]) and event["status"] == "Approved") or user.is_admin is True:
                new_event["can_delete"] = True

        return tz_events
    
    def report_generator(self, cognito_client: CognitoClient, year: int, month: int):

        tz = pytz.timezone('Europe/London')

        month_start_dt = datetime(year, month, 1, 0, 0, tzinfo=tz)

        # repeat sql query for month
        month_utc = month_start_dt.astimezone(pytz.UTC)

        sql = """
                select calendar.id, et.description, calendar.user_sub, calendar.site, calendar.notes, calendar.start, calendar.end, calendar.days, calendar.status, calendar.added_by, calendar.created
                from calendar
                inner join event_types et on et.id=calendar.event_type_id
                where calendar.end >= '%s' and month(calendar.end)=%s 
              """ % (month_utc, month,)
        
        events = self._db_handler.fetchall(sql)

        all_users = cognito_client.list_users()

        return {
            "events": events,
            "users": all_users,
        }
    
    def report_generator_year(self, cognito_client: CognitoClient, year: int, month: int):

        if month <= 4:
            year -= 1

        tz = pytz.timezone('Europe/London')

        month_start_dt = datetime(year, 4, 1, 0, 0, tzinfo=tz)

        print(month_start_dt)

        # repeat sql query for month
        month_utc = month_start_dt.astimezone(pytz.UTC)

        sql = """
                select calendar.id, et.description, calendar.user_sub, calendar.site, calendar.notes, calendar.start, calendar.end, calendar.days, calendar.status, calendar.added_by, calendar.created
                from calendar
                inner join event_types et on et.id=calendar.event_type_id
                where calendar.end >= '%s' and month(calendar.end)=%s 

              """ % (month_utc, month,)
        
        events = self._db_handler.fetchall(sql)

        all_users = cognito_client.list_users()

        return {
            "events": events,
            "users": all_users,
        }
        