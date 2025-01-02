from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.v1.models.contact import Contact
from api.v1.models.user import User
from api.v1.schemas.contact import ContactCreate, ContactDetail, ContactOut


def add_contact(db: Session, contact_id: str, user_id: str):
    # Check if the reverse relationship exists first to avoid duplicates
    reverse_contact_exists = (
        db.query(Contact)
        .filter(Contact.user_id == contact_id, Contact.contact_id == user_id)
        .first()
    )

    # Add contact for User A -> User B
    new_contact = Contact(user_id=user_id, contact_id=contact_id)
    db.add(new_contact)

    # If reverse contact does not exist, add contact for User B -> User A
    if not reverse_contact_exists:
        reverse_contact = Contact(user_id=contact_id, contact_id=user_id)
        db.add(reverse_contact)

    db.commit()
    db.refresh(new_contact)

    # Fetch the target user's details
    contact_user = db.query(User).filter(User.id == contact_id).first()

    # Return the contact details in the format expected by the `ContactOut` schema
    return ContactOut(
        contact_id=contact_user.id,
        username=contact_user.username,
        email=contact_user.email,
        phone_number=contact_user.phone_number,
        is_blocked=new_contact.is_blocked,
    )



def get_contacts(db: Session, user_id: str):
    # Fetch contacts added by the user (user_id is the owner of the contacts)
    contacts = (
        db.query(Contact)
        .filter(Contact.user_id == user_id)  # Ensure you're fetching by user_id
        .join(User, Contact.contact_id == User.id)  # Join to get contact user details
        .all()
    )

    return [
        ContactOut(
            contact_id=contact.contact_id,  # This should be the ID of the contact user
            username=contact.contact_user.username,  # Details of the contact user
            email=contact.contact_user.email,
            phone_number=contact.contact_user.phone_number,
            is_blocked=contact.is_blocked,
        )
        for contact in contacts
    ]


def get_contact_by_email_or_id_or_username(
    db: Session, contact_identifier: str, user_id: str
):
    contact = (
        db.query(Contact)
        .join(User, Contact.contact_id == User.id)
        .filter(
            (User.email == contact_identifier)
            | (User.username == contact_identifier)
            | (User.id == contact_identifier)
        )
        .first()
    )

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")

    return ContactDetail(
        contact_id=contact.contact_id,
        username=contact.contact_user.username,
        email=contact.contact_user.email,
        phone_number=contact.contact_user.phone_number,
        bio=contact.contact_user.bio,
        dpUrl=contact.contact_user.dpUrl,
    )


def restrict_contact(db: Session, contact_id: str, user_id: str):
    contact = (
        db.query(Contact)
        .filter(Contact.user_id == user_id, Contact.contact_id == contact_id)
        .first()
    )
    contact.is_blocked = True
    db.commit()
    return contact


def unrestrict_contact(db: Session, contact_id: str, user_id: str):
    contact = (
        db.query(Contact)
        .filter(Contact.user_id == user_id, Contact.contact_id == contact_id)
        .first()
    )
    contact.is_blocked = False
    db.commit()
    return contact


def remove_contact(db: Session, contact_id: str, user_id: str):
    contact = (
        db.query(Contact)
        .filter(Contact.user_id == user_id, Contact.contact_id == contact_id)
        .first()
    )
    db.delete(contact)
    db.commit()
