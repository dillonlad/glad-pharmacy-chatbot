from pydantic import BaseModel

class MessageRequest(BaseModel):
    phone_number: str
    message: str