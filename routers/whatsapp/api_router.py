from fastapi import APIRouter, Depends
import base64
import json

from routers.whatsapp.data_structures import MessageRequest
from auth import verify_token
from whatsapp_client import WhatsAppClient
from wp_db_handler import DBHandler
import boto3

# Initialize the AWS client for End User Messaging Social
client = boto3.client('socialmessaging')

router = APIRouter(prefix="/whatsapp")


@router.get("/get-channels/")
async def get_channels(user=Depends(verify_token)):
    db_handler = DBHandler()
    db_handler.start_session()

    whatsapp_client = WhatsAppClient(db_handler)
    db_handler.end_session()
    return whatsapp_client.get_channels()


@router.post("/send-message/")
async def send_message(
    request: MessageRequest,
    user=Depends(verify_token)
):
    # Construct the message payload
    message_payload = {
        "messaging_product": "whatsapp",
        "to": request.phone_number,
        "type": "text",
        "text": {"body": request.message}
    }
    
    # Encode the message payload to base64
    encoded_message = json.dumps(message_payload).encode()
    # Send the message using AWS End User Messaging Social
    response = client.send_whatsapp_message(
        message=encoded_message,
        originationPhoneNumberId='phone-number-id-ebd337836e614bd89ad52c6626538a58',
        metaApiVersion='v20.0'
    )
    
    return response