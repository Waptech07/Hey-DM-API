from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationCreate(BaseModel):
    user_id: str  # String type for user ID (UUID)
    message: str
    notification_type: str

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: str
    user_id: str
    message: str
    notification_type: str
    read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
