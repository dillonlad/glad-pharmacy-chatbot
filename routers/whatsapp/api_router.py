from fastapi import APIRouter, Depends
import base64
import json

from routers.whatsapp.data_structures import MessageRequest, ChannelsOut, MessagesOut
from auth import verify_token
from whatsapp_client import WhatsAppClient
from wp_db_handler import DBHandler

router = APIRouter(prefix="/whatsapp")


@router.get("/get-channels/", response_model=ChannelsOut)
async def get_channels(db_handler=Depends(verify_token)):
    """
    Get a list of conversations and their latest messages
    """

    whatsapp_client = WhatsAppClient(db_handler)
    channels = whatsapp_client.get_channels()

    return channels


@router.get("/conversation/{id}/", response_model=MessagesOut)
async def get_conversation(id: int, db_handler=Depends(verify_token)):
    """
    Get a list of messages in a converation.
    """

    whatsapp_client = WhatsAppClient(db_handler)
    messages = whatsapp_client.get_conversation(id)

    return messages



@router.post("/send-message/{id}/", response_model=MessagesOut)
async def send_message(
    id: int,
    request: MessageRequest,
    db_handler=Depends(verify_token)
):
    """
    Send an individual whatsapp message.
    """

    whatsapp_client = WhatsAppClient(db_handler)
    updated_messages = whatsapp_client.send_message(id, request.type, request.message)

    return updated_messages

@router.post("/send-template/{id}/{template_name}/")
async def send_template(
    id: int,
    template_name: str,
    db_handler=Depends(verify_token)
):

    whatsapp_client = WhatsAppClient(db_handler)
    updated_messages = whatsapp_client.send_template_message(id, template_name)

    return updated_messages

