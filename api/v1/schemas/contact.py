from typing import Optional
from pydantic import BaseModel


class ContactCreate(BaseModel):
    email_or_username_or_id_or_phone: str


class ContactOut(BaseModel):
    contact_id: str
    username: str
    email: str
    phone_number: Optional[str]
    is_blocked: bool


class ContactDetail(BaseModel):
    contact_id: str
    username: str
    email: str
    phone_number: Optional[str]
    bio: Optional[str]
    dpUrl: Optional[str]


class ContactBlock(BaseModel):
    contact_id: str
    is_blocked: bool

class ContactResponse(BaseModel):
    id: str
    username: str
    email: str
    is_verified: bool
    dpUrl: Optional[str]  # Profile picture URL
    is_online: Optional[bool]  # Online status

    class Config:
        from_attributes = True  