from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request, Security

# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz
from api.db.session import get_db
from api.utils.user import get_current_user
from api.v1.models.contact import Contact
from api.v1.models.user import User
from api.v1.schemas.contact import (
    ContactCreate,
    ContactDetail,
    ContactOut,
    ContactBlock,
    ContactResponse,
)
from api.v1.services.contact import (
    add_contact,
    get_contact_by_email_or_id_or_username,
    restrict_contact,
    get_contacts,
    remove_contact,
    unrestrict_contact,
)
from api.v1.services.user import UserService

contact_router = APIRouter(prefix="/contact", tags=["Contacts"])

# Global rate limiter
limiter = Limiter(key_func=get_remote_address)

# security = HTTPBearer()


# Create contact API - Add contact by id, username, email, or phone_number
@contact_router.post("/contacts", response_model=ContactOut)
def create_contact(
    contact: ContactCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_service = UserService(db)

    # Search for user using provided contact detail (email, username, id, phone_number)
    target_user = user_service.get_user_by_detail(
        contact.email_or_username_or_id_or_phone
    )

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a contact.")

    # Check if contact already exists
    existing_contact = (
        db.query(Contact)
        .filter(
            Contact.user_id == current_user.id, Contact.contact_id == target_user.id
        )
        .first()
    )
    if existing_contact:
        raise HTTPException(status_code=400, detail="Contact already exists.")

    return add_contact(db, target_user.id, current_user.id)


# Get a single contact by email, id, or username
@contact_router.get("/contacts/detail", response_model=ContactDetail)
def get_single_contact(
    email_or_username_or_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return get_contact_by_email_or_id_or_username(
        db, email_or_username_or_id, current_user.id
    )


# List contacts API - Get detailed contact info
@contact_router.get("/contacts", response_model=List[ContactOut])
def list_contacts(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return get_contacts(db, current_user.id)


# Block contact API
@contact_router.put("/contacts/block", response_model=ContactBlock)
def block_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    contact = (
        db.query(Contact)
        .filter(Contact.user_id == current_user.id, Contact.contact_id == contact_id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")
    return restrict_contact(db, contact_id, current_user.id)


# Unblock contact API
@contact_router.put("/contacts/unblock", response_model=ContactBlock)
def unblock_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    contact = (
        db.query(Contact)
        .filter(Contact.user_id == current_user.id, Contact.contact_id == contact_id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")
    return unrestrict_contact(db, contact_id, current_user.id)


# Remove contact API
@contact_router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    contact = (
        db.query(Contact)
        .filter(Contact.user_id == current_user.id, Contact.contact_id == contact_id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")
    remove_contact(db, contact_id, current_user.id)
    return {"detail": "Contact removed successfully."}


@contact_router.get("/contacts/search", response_model=dict)  # You can specify the response model here if needed
@limiter.limit("10/minute")
async def search_contacts(
    query: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Search for contacts based on partial matching with username or email
    contacts = (
        db.query(User)
        .filter(
            User.id != current_user.id,  # Exclude self
            User.is_active == True,  # Only active users
        )
        .all()
    )

    # Filter contacts using fuzzy matching with a threshold
    matched_contacts = [
        contact
        for contact in contacts
        if fuzz.partial_ratio(contact.username, query) > 60
        or fuzz.partial_ratio(contact.email, query) > 60
    ]

    # Exclude contacts blocked by the current user or who have blocked the current user
    filtered_contacts = [
        contact
        for contact in matched_contacts
        if not current_user.is_blocking(contact, db)
        and not contact.is_blocking(current_user, db)
    ]

    if not filtered_contacts:
        return {"message": "No matching contacts found"}

    # Create response using the ContactResponse model
    response_contacts = [ContactResponse.from_orm(contact) for contact in filtered_contacts]
    
    return {"contacts": response_contacts}