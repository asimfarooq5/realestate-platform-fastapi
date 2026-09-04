from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatUserSummary(BaseModel):
    id: str
    name: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    text: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    text: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StartConversationRequest(BaseModel):
    other_user_id: str
    property_id: Optional[str] = None
    message: str


class ConversationResponse(BaseModel):
    id: str
    other_user: Optional[ChatUserSummary] = None
    property_id: Optional[str] = None
    property_title: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]


class CommunityPostCreate(BaseModel):
    title: str
    body: str
    image_url: Optional[str] = None


class CommunityPostResponse(BaseModel):
    id: str
    title: str
    body: str
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
