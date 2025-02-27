from fastapi import APIRouter, Depends
import base64
import json

from routers.whatsapp.data_structures import MessageRequest, ChannelsOut, MessagesOut
from auth import verify_token
from whatsapp_client import WhatsAppClient
from wp_db_handler import DBHandler

router = APIRouter(prefix="/whatsapp")


@router.get("/get-channels/", response_model=ChannelsOut)
async def get_channels(user=Depends(verify_token)):
    """
    Get a list of conversations and their latest messages
    """
    db_handler = DBHandler()
    db_handler.start_session()

    whatsapp_client = WhatsAppClient(db_handler)
    channels = whatsapp_client.get_channels()
    db_handler.end_session()

    return channels


@router.get("/conversation/{id}/", response_model=MessagesOut)
async def get_conversation(id: int, user=Depends(verify_token)):
    """
    Get a list of messages in a converation.
    """

    db_handler = DBHandler()
    db_handler.start_session()

    whatsapp_client = WhatsAppClient(db_handler)
    messages = whatsapp_client.get_conversation(id)
    db_handler.end_session()

    return messages



@router.post("/send-message/{id}/", response_model=MessagesOut)
async def send_message(
    id: int,
    request: MessageRequest,
    user=Depends(verify_token)
):
    """
    Send an individual whatsapp message.
    """

    db_handler = DBHandler()
    db_handler.start_session()

    whatsapp_client = WhatsAppClient(db_handler)
    updated_messages = whatsapp_client.send_message(id, request.type, request.message)
    db_handler.end_session()
    
    return updated_messages
