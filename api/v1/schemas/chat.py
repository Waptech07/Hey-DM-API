from pydantic import BaseModel
from typing import List

class ChatCreate(BaseModel):
    recipient_id: str

class ChatResponse(BaseModel):
    chat_id: str
    message: str
