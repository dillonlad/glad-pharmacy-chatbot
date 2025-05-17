from fastapi import APIRouter, Depends
from datetime import datetime
from pytz import utc

from wp_db_handler import DBHandler
from auth import verify_token
from routers.voicemails.data_structures import VoicemailOut
from voicemail_manager import VoicemailManager

router = APIRouter(prefix="/voicemails")

@router.get("/", response_model=dict[str, dict[str, list[VoicemailOut]]])
async def get_voicemails(user=Depends(verify_token)):

    db_handler = user.db_handler
    voicemail_manager = VoicemailManager(db_handler)
    return {
        "voicemails": voicemail_manager.get_all_unread_voicemails()
        }

@router.post("/regenerate", response_model=dict[str, dict[str, list[VoicemailOut]]])
async def regenerate_voicemails(
    db_handler = Depends(DBHandler.get_session),
):
    
    voicemail_manager = VoicemailManager(db_handler)
    return {
        "voicemails": voicemail_manager.regenerate_voicemails()
        }

@router.post("/mark-read", response_model=dict[str, dict[str, list[VoicemailOut]]])
async def mark_voicemail_read(
    voicemail_id: int,
    user=Depends(verify_token),
):
    """
    Mark a voicemail as 'read' so it's no longer an update.
    """
    
    db_handler = user.db_handler
    voicemail_manager = VoicemailManager(db_handler)
    unread_voicemails = voicemail_manager.get_all_unread_voicemails(exclude_id=voicemail_id)

    db_handler.execute("UPDATE voicemails set `read`=1 where id = %s" % (voicemail_id,))
    db_handler.commit()

    return {
        "voicemails": unread_voicemails
    }
