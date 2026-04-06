import math

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
    
    def get_time_remaining(self, month_utc, end_utc, user_sub,):

        sql = """
                select calendar.id, et.description, calendar.user_sub, calendar.site, calendar.notes, calendar.start, calendar.end, calendar.days, calendar.status, calendar.added_by, calendar.created
                from calendar
                inner join event_types et on et.id=calendar.event_type_id
                where (calendar.end between '%s' and '%s' or calendar.start between '%s' and '%s')
                and calendar.user_sub='%s' and calendar.status='approved'
              """ % (month_utc, end_utc, month_utc, end_utc, user_sub,)
        
        events = self._db_handler.fetchall(sql)
        total_days = 0
        remaining_hours = 0
        for event in events:
            month_tz = month_utc.replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
            end_month_tz = end_utc.replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
            event_start = event["start"].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
            event_end = event["end"].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
            if (event_start.hour == 0 and event_start.minute == 0) and (event_end.hour == 23 and event_end.minute == 59):
                if event_start < month_tz:
                    event_days = event_end - month_tz
                    total_days += (event_days.days + 1)
                elif event_end > end_month_tz:
                    event_days = end_month_tz - event_start
                    total_days += (event_days.days + 1)
                else:
                    event_days = event_end - event_start
                    total_days += (event_days.days + 1)
            else:
                event_time = event_end - event_start
                seconds_taken = event_time.seconds
                hours_taken = seconds_taken / 60 / 60
                remaining_hours += hours_taken

        remaining_hours_days = remaining_hours / 8
        total_days_taken = total_days + remaining_hours_days

        return round(total_days_taken, 2)

    
    def has_enough_time(self, user_sub, al_entitlement, request_start_utc: datetime, request_end_utc: datetime,) -> bool:

        current_dt = request_start_utc

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

        total_days_taken = self.get_time_remaining(month_utc, end_utc, user_sub)
        
        request_start_local = request_start_utc.replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
        request_end_local = request_end_utc.replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
        print(request_start_local.hour, request_start_utc.minute)
        print(request_end_local.hour, request_end_local.minute)
        if request_start_local.hour == 0 and request_start_local.minute == 0 and request_end_local.hour == 23 and request_end_local.minute == 59:
            if request_start_utc < month_utc:
                print("here 1")
                requested_duration = request_end_local - month_utc
                requested_days = requested_duration.days + 1
            elif request_end_utc > end_utc:
                print("here 2")
                requested_duration = end_utc - request_start_local
                requested_days = requested_duration.days + 1
            else:
                print("here 3")
                requested_duration = request_end_local - request_start_local
                requested_days = requested_duration.days + 1
        else:
            print("here 4")
            requested_duration = request_end_local - request_start_local
            request_seconds_taken = requested_duration.seconds
            request_hours_taken = request_seconds_taken / 60 / 60
            requested_days = request_hours_taken / 8

        print("requested days", requested_days)

        return total_days_taken + requested_days <= float(al_entitlement)


    
    def report_generator(self, cognito_client: CognitoClient, year: int, month: int):

        tz = pytz.timezone('Europe/London')

        month_start_dt = datetime(year, month, 1, 0, 0, tzinfo=tz)

        # repeat sql query for month
        month_utc = month_start_dt.astimezone(pytz.UTC)

        sql = """
                select calendar.id, et.description, calendar.user_sub, calendar.site, calendar.notes, calendar.start, calendar.end, calendar.days, calendar.status, calendar.added_by, calendar.created
                from calendar
                inner join event_types et on et.id=calendar.event_type_id
                where (month(calendar.end)=%s  or month(calendar.start) = %s) and year(calendar.end) = %s
              """ % (month, month, year)
        
        events = self._db_handler.fetchall(sql)

        all_users = cognito_client.list_users()

        return {
            "events": events,
            "users": all_users,
        }
    
    def report_generator_year(self, cognito_client: CognitoClient, year: int, month: int, year_to: int, month_to: int):


        if month <= 4:
            year -= 1

        tz = pytz.timezone('Europe/London')

        month_start_dt = datetime(year, 4, 1, 0, 0, tzinfo=tz)
        month_end_dt = datetime(year_to, month_to, 1, 0, 0, tzinfo=tz)

        print(month_start_dt)
        print(month_end_dt)

        # repeat sql query for month
        month_utc = month_start_dt.astimezone(pytz.UTC)
        end_utc = month_end_dt.astimezone(pytz.UTC)

        sql = """
                select calendar.id, et.description, calendar.user_sub, calendar.site, calendar.notes, calendar.start, calendar.end, calendar.days, calendar.status, calendar.added_by, calendar.created
                from calendar
                inner join event_types et on et.id=calendar.event_type_id
                where calendar.end >= '%s'
                and calendar.end < '%s'
              """ % (month_utc, end_utc,)
        
        events = self._db_handler.fetchall(sql)

        all_users = cognito_client.list_users()

        return {
            "events": events,
            "users": all_users,
        }
        