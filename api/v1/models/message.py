from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.session import Base
import uuid

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    status = Column(String, default="sent")  # could be 'sent', 'delivered', 'read'
    pinned = Column(Boolean, default=False)
    translation = Column(Text, nullable=True)
    detected_language = Column(String, nullable=True)

    # Foreign key to the chat
    chat_id = Column(String, ForeignKey("chats.id"))
    chat = relationship("Chat", back_populates="messages")

    # Foreign key to the sender (user)
    sender_id = Column(String, ForeignKey("users.id"))
    sender = relationship("User")
    
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")