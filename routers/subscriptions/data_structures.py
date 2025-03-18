from pydantic import BaseModel

class SubsKeys(BaseModel):

    p256dh: str
    auth: str

class SubscriptionIn(BaseModel):
    endpoint: str
    keys: SubsKeys  # Contains "p256dh" and "auth"