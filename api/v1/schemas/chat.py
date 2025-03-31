from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    is_online: bool

class MessageInfo(BaseModel):
    id: str
    content: str
    sender_id: str
    timestamp: datetime
    status: str
    pinned: bool

class ChatResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    user1: UserInfo
    user2: UserInfo
    last_message: Optional[MessageInfo]
    unread_count: int
    is_pinned: bool

class ChatListResponse(BaseModel):
    chats: List[ChatResponse]