from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime, date, time

class MessageRequest(BaseModel):
    type: str = "text"
    message: str

class UpdateChannel(BaseModel):

    title: str

class ChannelOut(BaseModel):

    id: int
    avatarUrl: str = "https://www.svgrepo.com/show/535711/user.svg"
    title: str
    subtitle: Optional[str]
    date: Optional[Union[date, time, datetime]]
    unread: bool
    profile_name: str

class ChannelIn(BaseModel):

    name: str
    display_name: str
    number: str

class ChannelsOut(BaseModel):

    channels: list[ChannelOut]

class Template(BaseModel):

    id: int
    name: str
    description: str
    params: list[str]
    title: str
    message_preview: Optional[str]

class CreateChannelOut(ChannelsOut):

    new_channel_id: int

class MessageOut(BaseModel):

    id: int
    type: str
    message: str
    isMe: bool
    status: Optional[str]
    metadata: Optional[Union[list, dict]]

class MessagesOut(BaseModel):

    messages: list[MessageOut]
    open: bool
    empty_conversation: bool = False