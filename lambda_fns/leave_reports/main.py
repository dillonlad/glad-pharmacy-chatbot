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

SES_REGION = "eu-west-2"
TO_EMAILS = os.environ.get("TO_EMAILS", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "")

def calculate_days(row, target_month, target_year):
    """
    Safely parses and calculates the calendar days or fractions of a day 
    an event consumes strictly within the target billing month.
    """
    try:
        # Crucial Fix: Convert raw strings/objects from API to localized pandas datetimes first
        start = pd.to_datetime(row['start']).tz_localize('UTC').tz_convert('Europe/London')
        end = pd.to_datetime(row['end']).tz_localize('UTC').tz_convert('Europe/London')
    except Exception:
        print('errorr')
        import traceback
        print(traceback.format_exc())
        return 0.0

    # Define boundaries for the targeted month
    _, last_day = calendar.monthrange(int(target_year), int(target_month))
    month_start = pd.Timestamp(year=int(target_year), month=int(target_month), day=1, tz='Europe/London')
    month_end = pd.Timestamp(year=int(target_year), month=int(target_month), day=last_day, hour=23, minute=59, second=59, tz='Europe/London')

    # Clamp time ranges to the current target month view 
    effective_start = max(start, month_start)
    effective_end = min(end, month_end)

    if effective_start >= effective_end:
        return 0.0

    # Condition 1: Single calendar day calculation (Fraction of 8-hour / 28800s day)
    if effective_start.date() == effective_end.date():
        seconds_diff = (effective_end - effective_start).total_seconds()
        return min(seconds_diff / 28800, 1.0)

    # Condition 2: Multi-day span calculation
    days_diff = (effective_end.date() - effective_start.date()).days + 1
    return float(days_diff)


def calculate_hours(start_str, end_str):
    try:
        start = parser.isoparse(start_str)
        end = parser.isoparse(end_str)
        return round((end - start).total_seconds() / 3600, 2)
    except Exception:
        return 0.0


def lambda_handler(event, context):
    headers = {
        "x-access-key": os.environ.get("ACCESS_KEY", "")
    }

    # Set up safe structural fallback datetimes if event is triggered without a payload context
    now = pd.Timestamp.now(tz='Europe/London')
    month = int(event.get("month") if event.get("month") is not None else now.month)
    year = int(event.get("year") if event.get("year") is not None else now.year)

    params = {"month": month, "year": year}
    
    print(f"Fetching events for: {year}-{month:02d}")
    response = requests.get("https://api.gladpharmacy.co.uk/webhooks/get-all-events", params=params, headers=headers)
    
    if response.status_code != 200:
        print(f"Request failed with status code {response.status_code}")
        return {"statusCode": response.status_code, "body": "Failed fetching user data profile elements."}
    
    data = response.json()
    users = data.get("users", {"Users": []})
    events = data.get("events", [])

    user_map = {}
    for user in users.get("Users", []):
        sub = next((attr["Value"] for attr in user.get("Attributes", []) if attr["Name"] == "sub"), None)
        name = next((attr["Value"] for attr in user.get("Attributes", []) if attr["Name"] == "name"), "Unknown")
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
    files_added_to_zip = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for user_name, user_events in events_by_user.items():
            
            # Pre-filter user events to verify they actually match target reporting categories
            valid_events = [e for e in user_events if e.get("description") in ["Annual Leave", "Sickness", "Extra Hours"]]
            if not valid_events:
                continue

            output = io.BytesIO()
            has_sheets = False  
            
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for event_type in ["Annual Leave", "Sickness", "Extra Hours"]:
                    filtered = [e for e in user_events if e.get("description") == event_type]
                    if not filtered:
                        continue
                    
                    df = pd.DataFrame(filtered)
                    has_sheets = True 

                    if event_type in ["Annual Leave", "Sickness"]:
                        # Fixed: Signature now accepts target_year properly
                        df['days'] = df.apply(calculate_days, axis=1, target_month=month, target_year=year)
                        total_days = df['days'].sum()
                        
                        blank_row = pd.Series({col: "" for col in df.columns})
                        summary_row = pd.Series({**{col: "" for col in df.columns}, "days": f"Total: {total_days}"})
                        df = pd.concat([df, blank_row.to_frame().T, summary_row.to_frame().T], ignore_index=True)
                        
                    elif event_type == "Extra Hours":
                        df["duration_hours"] = df.apply(
                            lambda row: calculate_hours(row.get("start"), row.get("end")), axis=1
                        )
                        total_hours = df["duration_hours"].sum()
                        
                        blank_row = pd.Series({col: "" for col in df.columns})
                        summary_row = pd.Series({**{col: "" for col in df.columns}, "duration_hours": f"Total: {total_hours}"})
                        df = pd.concat([df, blank_row.to_frame().T, summary_row.to_frame().T], ignore_index=True)

                    df.to_excel(writer, sheet_name=event_type, index=False)
            
            # Only package up file streams that successfully passed openpyxl validation
            if has_sheets:
                zipf.writestr(f"{user_name}.xlsx", output.getvalue())
                files_added_to_zip += 1

    zip_buffer.seek(0)
    zip_data = zip_buffer.getvalue()

    if files_added_to_zip == 0:
        print("No valid user excel files generated. Email sending skipped.")
        return {"statusCode": 200, "body": "No relevant records matched criteria for this billing period."}

    print("Sending reports package via SES...")
    ses_client = boto3.client("ses", region_name=SES_REGION)
    try:
        ses_client.send_raw_email(
            Source=FROM_EMAIL,
            Destinations=TO_EMAILS.split(","), 
            RawMessage={"Data": build_email_with_attachment(zip_data)}
        )
    except ClientError as e:
        print(f"Email sending failed: {e}")
        raise

    return {"statusCode": 200, "body": "Email with reports sent."}


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