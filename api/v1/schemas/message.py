from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    is_online: bool

class ReactionInfo(BaseModel):
    id: str
    reaction: str
    user: UserInfo
    timestamp: datetime

class MessageResponse(BaseModel):
    id: str
    content: str
    sender: UserInfo
    timestamp: datetime
    status: str
    pinned: bool
    reactions: List[ReactionInfo]
    translation: Optional[str]
    detected_language: Optional[str]

class MessageListResponse(BaseModel):
    messages: List[MessageResponse]

class MessageCreate(BaseModel):
    content: str
