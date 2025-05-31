from enum import Enum
from datetime import datetime
import pytz


class EditableAttribute(Enum):

    NAME = "name"
    EMAIL = "email"
    ANNUAL_LEAVE_ENTITLEMENT = "al_entitlement"

class CognitoUser:
    """
    Holder class for authorizations.
    """
    
    def __init__(self, sub, email, name, is_admin, groups, db_handler, cognito_client):
        self.sub = sub
        self.email = email
        self.name = name
        self.is_admin = is_admin   
        self.groups = groups
        self.db_handler = db_handler
        self.cognito_client = cognito_client

    def get_users_manager(self):

        admin_users_response = self.cognito_client.list_users_in_group("glad_admin")
        admin_users = admin_users_response.get("Users", [])
        users_managers = []
        for _user in admin_users:
            _user_sub = next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "sub"), "")
            if self.is_colleague(_user_sub) is True:
                users_managers.append({
                    "sub": _user_sub,
                    "email": next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "email"), ""),
                    "name": next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "name"), ""),
                })
        return users_managers

    def get_colleagues(self, add_calendar = False):

        members = []

        # Define timezone
        tz = pytz.timezone('Europe/London')
        # Get current date in Europe/London
        now = datetime.now(tz)

        # Determine most recent April 1st
        if now.month >= 4:
            april_start_date = datetime(now.year, 4, 1, 0, 0, tzinfo=tz)
        else:
            april_start_date = datetime(now.year - 1, 4, 1, 0, 0, tzinfo=tz)

        current_month_start_dt = datetime(now.year, now.month, 1, 0, 0, tzinfo=tz)

        # Convert to UTC
        recent_april_utc = april_start_date.astimezone(pytz.UTC)

        # repeat sql query for month
        recent_month_utc = current_month_start_dt.astimezone(pytz.UTC)

        calendar_results = []
        if add_calendar is True:
            # Annual leave year starts from April.
            sql = """
                    select calendar.user_sub, event_types.name, sum(calendar.days) as `days`
                    from calendar
                    inner join event_types on calendar.event_type_id = event_types.id
                    where calendar.status='Approved'
                    and calendar.start >= '%s'
                    group by calendar.user_sub, event_types.name
                  """ % (recent_april_utc,)
            
            calendar_results = self.db_handler.fetchall(sql)

            month_sql = """
                    select calendar.user_sub, event_types.name, sum(calendar.days) as `days`
                    from calendar
                    inner join event_types on calendar.event_type_id = event_types.id
                    where calendar.status='Approved'
                    and calendar.end >= '%s'
                    group by calendar.user_sub, event_types.name
                  """ % (recent_month_utc,)
            print(month_sql)

        added_user_subs = []
        for group in self.groups:
            group_users_response = self.cognito_client.list_users_in_group(group)
            group_users = group_users_response.get("Users", [])

            for _user in group_users:
                _user_sub = next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "sub"), "")
                if _user_sub not in added_user_subs:
                    al_entitlement = next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] in ["al_entitlement", "custom:al_entitlement"]), 25)
                    al_used = next((_user_calendar["days"] for _user_calendar in calendar_results if _user_calendar["user_sub"] == _user_sub and _user_calendar["name"] == "annual_leave"), 0)
                    sickness_used = next((_user_calendar["days"] for _user_calendar in calendar_results if _user_calendar["user_sub"] == _user_sub and _user_calendar["name"] == "sickness"), 0)
                    members.append({
                        "username": _user["Username"],
                        "sub": _user_sub,
                        "email": next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "email"), ""),
                        "name": next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "name"), ""),
                        "al_entitlement": float(al_entitlement),
                        "al_used": float(al_used),
                        "al_remaining": float(al_entitlement) - float(al_used),
                        "sickness_used": float(sickness_used),
                    })
                    added_user_subs.append(_user_sub)

        return members
    
    def is_colleague(self, other_user_sub) -> bool:
        colleagues = self.get_colleagues()
        matching_colleague = next((colleague for colleague in colleagues if colleague["sub"] == other_user_sub), None)
        return True if matching_colleague is not None else False