from pydantic_settings import BaseSettings
import json
import traceback
from pywebpush import webpush


class WebpushSettings(BaseSettings):

    class Config:
        env_prefix = "web_push_"
        case_sensitive = False

    public_key: str
    private_key: str
    vapid_claims: dict = {"sub": "mailto:dad82434@gmail.com"}


class WebpushClient:

    def __init__(self, db_handler):
        self._db_handler = db_handler
        self._settings = WebpushSettings()

    def send_push(self, title, body, uri, sites=[]):

        all_subs = self._db_handler.fetchall(
                """
                SELECT sub.endpoint, sub.p256dh, sub.auth 
                FROM dashboard_sites sites
                inner join dashboard_users users on sites.id = users.site_id
                inner join dashboard_subscriptions sub on users.sub=sub.sub
                where sites.name in ({})
                """.format(",".join(["'{}'".format(site_name) for site_name in ["all"] + sites]))
            )


        for sub in all_subs:
            try:
                resp = webpush(
                    subscription_info={
                        "endpoint": sub["endpoint"],
                        "keys": {
                            "p256dh": sub["p256dh"],
                            "auth": sub["auth"]
                        }
                    },
                    data=json.dumps({
                        "title": title, 
                        "body": body,
                        "icon": "/notification.png",
                        "url": uri
                        }),
                    vapid_private_key=self._settings.private_key,
                    vapid_claims=self._settings.vapid_claims,
                )

                print(resp.text)
            except:
                print(traceback.format_exc())