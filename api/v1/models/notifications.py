from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.session import Base
import uuid

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)  # String type for UUID
    message = Column(String, nullable=False)
    notification_type = Column(String, nullable=False)  # e.g., "friend_request", "message"
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship with User model
    user = relationship("User", back_populates="notifications")
