from fastapi import APIRouter, Depends
from auth import verify_token
from wp_db_handler import DBHandler
from woocommerce_manager import WoocommerceManager
from whatsapp_client import WhatsAppClient
from voicemail_manager import VoicemailManager
from routers.updates.data_structures import UpdatesOut


router = APIRouter()


@router.get("/updates", response_model=UpdatesOut)
async def get_updates(user=Depends(verify_token)):
    """
    Get all updates for WhatsApp, repeats, contact forms and enquiries.
    """
    
    db_handler = user.db_handler
    # Get latest shop orders
    wc_manager = WoocommerceManager(db_handler)
    orders_out = wc_manager.get_orders()
    # Get latest whatsapp messages
    whatsapp_client = WhatsAppClient(db_handler)
    number_of_unread_whatsapps = whatsapp_client.get_unread_conversations()

    voicemail_manager = VoicemailManager(db_handler)
    number_of_unread_voicemails = voicemail_manager.get_total_unread_voicemails()
    
    sql = """
            SELECT `form_name`, COUNT(`id`) AS `unread_entries`
            FROM wp_form_entries
            WHERE `viewed`=0
            GROUP BY `form_name`;
          """
    unread_forms = db_handler.fetchall(sql)
    repeats = next((_form_count["unread_entries"] for _form_count in unread_forms if _form_count["form_name"] == "repeat-prescription-sign-up"), 0)
    contact_forms = next((_form_count["unread_entries"] for _form_count in unread_forms if _form_count["form_name"] == "contact-form"), 0)
    
    return UpdatesOut(
        orders=orders_out, 
        unread_whatsapps=number_of_unread_whatsapps, 
        repeats=repeats,
        contact_forms=contact_forms,
        unread_voicemails=number_of_unread_voicemails,
        is_admin=user.is_admin,
        sites=user.groups,
    )


# Example root endpoint
@router.get("/")
async def root():
    return {"message": "Hugging Face Model API is running!"}