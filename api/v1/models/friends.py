from sqlalchemy import ARRAY, UUID, Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.session import Base
import uuid


class Friendship(Base):
    __tablename__ = 'friendships'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    receiver_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    status = Column(String, default="pending")  # "pending", "accepted", "blocked"
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
