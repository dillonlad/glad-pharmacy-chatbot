import boto3
import requests
import pandas as pd
import zipfile
import io
import os
from botocore.exceptions import ClientError

SES_REGION = "eu-west-2"  # Change if needed
TO_EMAIL = "dlad82434@gmail.com"
FROM_EMAIL = os.environ.get("FROM_EMAIL", "your-verified-sender@example.com")  # Must be verified in SES

def lambda_handler(event, context):
    # Step 1: Get users and events
    response = requests.get("https://api.gladpharmacy.co.uk/webhooks/get-all-events")
    data = response.json()
    users = data.get("users", [])
    events = data.get("events", [])

    # Step 2: Convert users to dict by sub for quick lookup
    user_map = {}
    for user in users:
        sub_attr = next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'sub'), None)
        name_attr = next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'name'), None)
        if sub_attr:
            user_map[sub_attr] = name_attr or "Unknown"

    # Step 3: Group events by user name
    events_by_user = {}
    for event in events:
        user_sub = event.get("user_sub")
        if not user_sub:
            continue
        user_name = user_map.get(user_sub, "Unknown")
        events_by_user.setdefault(user_name, []).append(event)

    # Step 4: Create Excel files in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for user_name, user_events in events_by_user.items():
            df = pd.DataFrame(user_events)
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            zipf.writestr(f"{user_name}.xlsx", excel_buffer.getvalue())

    zip_buffer.seek(0)

    # Step 5: Send email with zip attachment
    ses_client = boto3.client("ses", region_name=SES_REGION)

    try:
        ses_client.send_raw_email(
            RawMessage={"Data": build_email_with_attachment(zip_buffer.getvalue())}
        )
    except ClientError as e:
        print(f"Failed to send email: {e}")
        raise

    return {"statusCode": 200, "body": "Email sent successfully."}


def build_email_with_attachment(zip_data):
    import email
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg['Subject'] = "User Events Reports"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    body = MIMEText("Please find attached the zipped Excel reports for each user.", 'plain')
    msg.attach(body)

    attachment = MIMEApplication(zip_data)
    attachment.add_header('Content-Disposition', 'attachment', filename="user_events.zip")
    msg.attach(attachment)

    return msg.as_string()
