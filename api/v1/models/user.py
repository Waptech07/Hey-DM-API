from sqlalchemy import ARRAY, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship, Session
from datetime import datetime
from api.db.session import Base
import uuid

from api.v1.models.contact import Contact


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    dpUrl = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_online = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime, nullable=True)
    otp_code = Column(Integer, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    otp_invalid = Column(Boolean, default=False)
    social_id = Column(String, unique=True, nullable=True)
    provider = Column(String, nullable=True)

    # Newly added fields for 2FA Auth
    otp_secret = Column(String, nullable=True)  # To store 2FA secret
    backup_codes = Column(ARRAY(String), nullable=True)  # Optional for backup codes
    two_FA_enabled = Column(Boolean, default=False)  # Track if 2FA is enabled
    otp_verified = Column(
        Boolean, default=False
    )  # Track if OTP has been successfully verified
    last_otp_verified_at = Column(
        DateTime, nullable=True
    )  # Optional: track time of last OTP verification

    # notifications
    notifications = relationship("Notification", back_populates="user")

    # relationships with contacts
    contacts = relationship(
        "Contact", back_populates="user", foreign_keys="[Contact.user_id]"
    )
    added_by_contacts = relationship(
        "Contact", back_populates="contact_user", foreign_keys="[Contact.contact_id]"
    )

    def is_blocking(self, other_user: "User", db: Session) -> bool:
        """Check if the current user has blocked the specified user."""
        # Query the contacts to check if the current user has blocked the other user
        blocked_contact = (
            db.query(Contact)
            .filter(
                Contact.user_id == self.id,
                Contact.contact_id == other_user.id,
                Contact.is_blocked.is_(True)
            )
            .first()
        )
        return blocked_contact is not None