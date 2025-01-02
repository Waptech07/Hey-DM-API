from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Session
from api.db.session import Base
# from api.v1.models.user import User

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    contact_id = Column(String, ForeignKey("users.id"))
    is_blocked = Column(Boolean, default=False)

    # Relationship fields
    user = relationship("User", foreign_keys=[user_id], back_populates="contacts")
    contact_user = relationship("User", foreign_keys=[contact_id], back_populates="added_by_contacts")
    
    def is_blocking(self, user: "User", db: Session) -> bool:
        """Check if the contact has blocked the specified user."""
        return self.is_blocked and self.user_id == user.id