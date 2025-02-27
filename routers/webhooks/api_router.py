from fastapi import APIRouter, BackgroundTasks

from wp_db_handler import DBHandler
from whatsapp_client import WhatsAppClient
from sqs_client import SQSClient

router = APIRouter(prefix="/webhooks")


@router.get("/process-queue")
async def process_queue(background_tasks: BackgroundTasks):

    db_handler = DBHandler()
    db_handler.start_session()

    whatsapp_client = WhatsAppClient(db_handler)
    sqs_client = SQSClient(whatsapp_client)
    background_tasks.add_task(
        sqs_client.process_queue
    )
    
    return {
        "Status": "Ok"
    }