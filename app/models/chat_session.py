from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class ChatSession(Base):
    """Represents a single chat session or conversation."""
    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="chat_sessions")

    messages = relationship("Message", back_populates="chat_session", cascade="all, delete-orphan",
                            order_by="Message.timestamp")

    def __repr__(self):
        return f"<ChatSession id={self.id} user_id={self.user_id} start_time={self.start_time}>"
