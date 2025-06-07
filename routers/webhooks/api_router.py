from datetime import datetime, timedelta
from fastapi import APIRouter, BackgroundTasks, Depends
import pytz

from auth import CognitoClient, verify_api_key
from calendar_manager import CalendarManager
from wp_db_handler import DBHandler
from whatsapp_client import WhatsAppClient
from sqs_client import SQSClient
from voicemail_manager import VoicemailManager


router = APIRouter(prefix="/webhooks")


@router.get("/process-queue")
async def process_queue(background_tasks: BackgroundTasks):
    """
    Ingest items in SQS Queue.
    """

    db_handler = DBHandler()
    db_handler.start_session()

    whatsapp_client = WhatsAppClient(db_handler)
    sqs_client = SQSClient(whatsapp_client)
    voicemail_manager = VoicemailManager(db_handler)
    background_tasks.add_task(
        sqs_client.process_queue
    )
    background_tasks.add_task(
        voicemail_manager.scan_voicemails
    )
    
    return {
        "Status": "Ok"
    }

@router.get("/get-all-events")
async def get_all_events(year: int = None, month: int = None, db_handler: DBHandler = Depends(verify_api_key)):
    """
    Get all of the events needed to generate a report for the last month.
    """

    report_year = year
    report_month = month

    if report_year is None and report_month is None:

        tz = pytz.timezone('Europe/London')
        # Get current date in Europe/London
        now = datetime.now(tz)

        yesterday_dt = now - timedelta(days=1)

        report_year = yesterday_dt.year
        report_month = yesterday_dt.month

    calendar_manager = CalendarManager(db_handler)
    cognito_client = CognitoClient()

    return calendar_manager.report_generator(cognito_client, report_year, report_month)

@router.get("/s3-extract")
async def s3_extract(object_key:str):

    # from email import policy
    # from email.parser import BytesParser

    # settings = S3Settings()
    # settings.form_uploads_bucket = "glad-voicemail"
    # s3_client = S3Client(settings=settings)
    # email_obj = s3_client._s3_client.get_object(Bucket="glad-voicemail", Key=object_key)

    # print(email_obj)

    # email_bytes = email_obj["Body"].read()


    # # Parse the email
    # msg = BytesParser(policy=policy.default).parsebytes(email_bytes)

    # print(msg["subject"], msg["from"])


    # # Extract attachments
    # for part in msg.iter_attachments():
    #     filename = part.get_filename()
    #     if filename:
    #         attachment_content = part.get_payload(decode=True)

    #         # Save attachment to S3
    #         attachment_key = f"attachments/{filename}"
    #         s3_client._s3_client.put_object(
    #             Bucket="glad-voicemail",
    #             Key=attachment_key,
    #             Body=attachment_content
    #         )
    #         print(f"Saved attachment: {filename} to glad-voicemail")



    db_handler = DBHandler()
    db_handler.start_session()
    voicemail_manager = VoicemailManager(db_handler)
    voicemail_manager.scan_voicemails()
    db_handler.end_session()
    return {"succes": True}