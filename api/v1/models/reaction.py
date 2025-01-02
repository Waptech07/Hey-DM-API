from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.session import Base

class Reaction(Base):
    __tablename__ = "reactions"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    reaction = Column(String, nullable=False)  # This can store the reaction (e.g., emoji or text)
    created_at = Column(DateTime, default=datetime.now)
    
    message = relationship("Message", back_populates="reactions")
    user = relationship("User")
