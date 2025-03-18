from fastapi import APIRouter, Depends
from auth import verify_token
from cognito_user import CognitoUser
import json
from wp_db_handler import DBHandler
from routers.subscriptions.data_structures import SubscriptionIn
from webpush_client import WebpushClient

router = APIRouter(prefix="/subscriptions")


@router.post("/", response_model=dict)
async def subscribe_device(
    params: SubscriptionIn,
    user: CognitoUser = Depends(verify_token),
):
    """
    Subscribe a device to push notifs.
    """

    db_handler = user.db_handler
    # Check if the subscription already exists
    existing_sub = db_handler.fetchone(
        "SELECT id FROM dashboard_subscriptions WHERE endpoint = '%s'" % (params.endpoint,),
    )

    if existing_sub:
        return {"success": True, "message": "Already subscribed"}

    # Insert new subscription
    db_handler.execute(
        """
        INSERT INTO dashboard_subscriptions (sub, endpoint, p256dh, auth)
        VALUES ('%s', '%s', '%s', '%s')
        """ % (user.sub, params.endpoint, params.keys.p256dh, params.keys.auth,),
    )
    db_handler.commit()

    return {
        "success": True
    }

@router.post("/send-notifs", response_model=dict)
async def send_notifications():

    db_handler = DBHandler()
    db_handler.start_session()

    webpush_client = WebpushClient(db_handler)
    webpush_client.send_push("This is a notif", "from api")
    db_handler.end_session()
    return {"success": True}