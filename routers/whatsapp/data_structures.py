from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime, date, time

class MessageRequest(BaseModel):
    type: str = "text"
    message: str

class ChannelOut(BaseModel):

    id: int
    avatarUrl: str = "https://www.svgrepo.com/show/535711/user.svg"
    title: str
    subtitle: str
    date: Optional[Union[date, time, datetime]]
    unread: bool

class ChannelsOut(BaseModel):

    channels: list[ChannelOut]

class MessageOut(BaseModel):

    id: int
    type: str
    message: str
    isMe: bool
    status: Optional[str]
    metadata: Optional[Union[list, dict]]

class MessagesOut(BaseModel):

    messages: list[MessageOut]