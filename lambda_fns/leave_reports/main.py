import json
import calendar
import boto3
import requests
import pandas as pd
import zipfile
import io
import os
from botocore.exceptions import ClientError
from dateutil import parser

SES_REGION = "eu-west-2"  # Change if needed
TO_EMAILS = os.environ.get("TO_EMAILS")
FROM_EMAIL = os.environ.get("FROM_EMAIL")  # Must be verified in SES

def calculate_days(row, target_month):
    start = row['start']
    end = row['end']
    
    # Convert to London time to check against local 00:00 and 23:59
    start_local = start.tz_convert('Europe/London')
    end_local = end.tz_convert('Europe/London')
    
    # Condition 1: End date is in another month
    if end.month != start.month:
        # Get the number of days in the specific 'month' variable
        # calendar.monthrange returns (weekday of first day, number of days)
        _, days_in_month = calendar.monthrange(start.year, target_month)
        return float(days_in_month)

    # Condition 2: Same month, full day coverage (00:00:00 to 23:59:00 in London time)
    if (start.month == end.month and 
        start_local.time() == pd.Timestamp("00:00:00").time() and 
        end_local.time() == pd.Timestamp("23:59:00").time()):
        # Assuming you want to treat this as the full calendar difference + 1 day
        return (end - start).days + 1

    # Condition 3: Same day calculation (Fraction of 8-hour/28800s day)
    if start.date() == end.date():
        seconds_diff = (end - start).total_seconds()
        return seconds_diff / 28800

    # Default fallback (if none of the specific logic above hits)
    return (end - start).days

def lambda_handler(event, context):
    # Step 1: Get users and events
    headers = {
        "x-access-key": os.environ.get("ACCESS_KEY")
    }

    month = event.get("month", None)
    year = event.get("year", None)

    params = None

    if month is not None and year is not None:
        params = {"month": month, "year": year}
    print("here 1")
    response = requests.get("https://api.gladpharmacy.co.uk/webhooks/get-all-events", params=params, headers=headers)
    print("here 2")
    if response.status_code != 200:
        print("Request failed.")
        return
    
    data = response.json()

    print(data)
    users = data.get("users", {"Users": []})
    events = data.get("events", [])

    user_map = {}
    for user in users["Users"]:
        sub = next((attr["Value"] for attr in user["Attributes"] if attr["Name"] == "sub"), None)
        name = next((attr["Value"] for attr in user["Attributes"] if attr["Name"] == "name"), "Unknown")
        if sub:
            user_map[sub] = name

    events_by_user = {}
    for _event in events:
        user_sub = _event.get("user_sub")
        if not user_sub:
            continue
        user_name = user_map.get(user_sub, "Unknown")
        events_by_user.setdefault(user_name, []).append(_event)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for user_name, user_events in events_by_user.items():
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for event_type in ["Annual Leave", "Sickness", "Extra Hours"]:
                    filtered = [e for e in user_events if e.get("description") == event_type]
                    if not filtered:
                        continue
                    df = pd.DataFrame(filtered)
                    df['days'] = df.apply(calculate_days, axis=1, target_month=month)

                    if event_type in ["Annual Leave", "Sickness"]:
                        total_days = df.get("days", pd.Series(dtype=float)).sum()
                        df.loc[len(df.index)] = {col: "" for col in df.columns}
                        df.loc[len(df.index)] = {**{col: "" for col in df.columns}, "days": total_days}
                    elif event_type == "Extra Hours":
                        df["duration_hours"] = df.apply(
                            lambda row: calculate_hours(row.get("start"), row.get("end")), axis=1
                        )
                        total_hours = df["duration_hours"].sum()
                        df.loc[len(df.index)] = {col: "" for col in df.columns}
                        df.loc[len(df.index)] = {**{col: "" for col in df.columns}, "duration_hours": total_hours}

                    df.to_excel(writer, sheet_name=event_type, index=False)

            zipf.writestr(f"{user_name}.xlsx", output.getvalue())

    zip_buffer.seek(0)
    print("sending emails")
    ses_client = boto3.client("ses", region_name=SES_REGION)
    try:
        ses_client.send_raw_email(
            Source=FROM_EMAIL,
            Destinations=TO_EMAILS.split(","), 
            RawMessage={"Data": build_email_with_attachment(zip_buffer.getvalue())}
        )
    except ClientError as e:
        print(f"Email sending failed: {e}")
        raise

    return {"statusCode": 200, "body": "Email with reports sent."}


def calculate_hours(start_str, end_str):
    try:
        start = parser.isoparse(start_str)
        end = parser.isoparse(end_str)
        return round((end - start).total_seconds() / 3600, 2)
    except Exception:
        return 0.0

def build_email_with_attachment(zip_data):

    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg['Subject'] = "User Events Reports"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAILS

    body = MIMEText("Please find attached the zipped Excel reports for each user.", 'plain')
    msg.attach(body)

    attachment = MIMEApplication(zip_data)
    attachment.add_header('Content-Disposition', 'attachment', filename="user_events.zip")
    msg.attach(attachment)

    return msg.as_string()


# if __name__=="__main__":
#     lambda_handler(None, None)