from fastapi import APIRouter, Depends, HTTPException
import phonenumbers

from routers.whatsapp.data_structures import Template, MessageRequest, ChannelsOut, MessagesOut, ChannelIn, CreateChannelOut, UpdateChannel
from auth import verify_token
from whatsapp_client import WhatsAppClient
from wp_db_handler import DBHandler

router = APIRouter(prefix="/whatsapp")

@router.get("/templates/", response_model=dict[str, list[Template]])
async def get_templates(user=Depends(verify_token)):
    """
    Get a list of conversations and their latest messages
    """

    db_handler = user.db_handler

    sql = "select id, name, description, params, title, message_preview from whatsapp_templates where selectable=1"
    templates = db_handler.fetchall(sql)
    formatted_templates = []
    for tempate in templates:
        formatted_template = tempate
        formatted_template["params"] = tempate["params"].split(",") if tempate["params"] else []
        formatted_templates.append(formatted_template)

    return {
        "templates": formatted_templates,
    }

@router.get("/get-channels/", response_model=ChannelsOut)
async def get_channels(user=Depends(verify_token)):
    """
    Get a list of conversations and their latest messages
    """

    db_handler = user.db_handler

    whatsapp_client = WhatsAppClient(db_handler)
    channels = whatsapp_client.get_channels()

    return channels

@router.post("/channel", response_model=CreateChannelOut)
async def create_channel(
    params: ChannelIn,
    user=Depends(verify_token),
):
    """
    Start a new chat with someone.
    """

    db_handler = user.db_handler
    try:
        # Parse the phone number with the default region (GB)
        parsed_number = phonenumbers.parse(params.number, "GB")
        
        # Check if the number is valid
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError("Invalid phone number")
        
        # Format the number in international format and remove the "+"
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        whatsapp_number = formatted_number[1:]  # Remove the leading '+'
    
    except Exception as e:
        raise HTTPException(status_code=550, detail="Invalid phone number.")
    
    existing_number = db_handler.fetchone("SELECT id from `conversations` where phone_number = '%s'" % (whatsapp_number,))
    if existing_number is not None:
        raise HTTPException(status_code=550, detail="Phone number exists.")
    
    db_handler.execute(
        "INSERT INTO `conversations` (phone_number, profile_name, display_name, `read`) VALUES ('%s', '%s', '%s', 1)" % (whatsapp_number, params.name, params.display_name,)
    )
    new_row = db_handler.commit(last_row_id = True)

    whatsapp_client = WhatsAppClient(db_handler)
    channels = whatsapp_client.get_channels()

    return {
        "channels": channels["channels"],
        "new_channel_id": new_row,
    }


@router.put("/channel", response_model=ChannelsOut)
async def update_channel(
    channel_id: int, 
    params: UpdateChannel,
    user=Depends(verify_token)
):

    db_handler = user.db_handler

    channel_sql = "select id from conversations where id=%s and active=1" % (channel_id,)
    existing_channel = db_handler.fetchone(channel_sql)
    if existing_channel is None:
        raise HTTPException(status_code=404, detail="Channel not found.")
    
    update_sql = "update conversations set display_name='%s' where id=%s" % (params.title, channel_id,)
    db_handler.execute(update_sql, True)

    whatsapp_client = WhatsAppClient(db_handler)
    channels = whatsapp_client.get_channels()

    return channels


@router.get("/conversation/{id}/", response_model=MessagesOut)
async def get_conversation(id: int, user=Depends(verify_token)):
    """
    Get a list of messages in a converation.
    """

    db_handler = user.db_handler
    whatsapp_client = WhatsAppClient(db_handler)
    messages = whatsapp_client.get_conversation(id)

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

    db_handler = user.db_handler
    whatsapp_client = WhatsAppClient(db_handler)
    updated_messages = whatsapp_client.send_message(id, request.type, request.message)

    return updated_messages

@router.post("/send-template/{id}/{template_name}/")
async def send_template(
    id: int,
    template_name: str,
    params: dict,
    user=Depends(verify_token)
):
    db_handler = user.db_handler
    whatsapp_client = WhatsAppClient(db_handler)
    
    whatsapp_parameters = params.get("params", None)
    
    components = None
    if whatsapp_parameters is not None:
        message_params = []
        for param_name, param_value in whatsapp_parameters.items():
            message_params.append({"type": "text", "parameter_name": param_name, "text": param_value})
        components = [
            {
                "type": "body",
                "parameters": message_params,
            }
        ]
    updated_messages = whatsapp_client.send_template_message(id, template_name, components=components)

    return updated_messages

