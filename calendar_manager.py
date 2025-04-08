import pytz

from wp_db_handler import DBHandler


class CalendarManager:

    def __init__(self, db_handler: DBHandler):
        self._db_handler = db_handler

    def get_all_events(self, user):

        sql = "select calendar.id, calendar.notes, calendar.title, calendar.site, calendar.status, calendar.start, calendar.end, event_types.background_colour, calendar.user_sub, calendar.added_by " \
          "from calendar inner join event_types on calendar.event_type_id=event_types.id and calendar.status != 'Rejected'" \
          " and calendar.site in ({})".format(",".join(["'{}'".format(group_name) for group_name in user.groups]))
        print(sql)

        events = self._db_handler.fetchall(sql)
        tz_events = []
        for event in events:
            new_event = event
            new_event["start"] = new_event["start"].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
            new_event["end"] = new_event["end"].replace(tzinfo=pytz.utc).astimezone(tz=pytz.timezone("Europe/London"))
            tz_events.append(new_event)
            new_event["can_delete"] = False
            if (user and (user.sub == event["user_sub"] or user.sub == event["added_by"])) or user.is_admin is True:
                new_event["can_delete"] = True

        return tz_events