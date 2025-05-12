from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

from .chat_session import ChatSession


class Message(Base):
    """Represents a single message within a chat session."""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False)

    content = Column(Text, nullable=False)

    sender_type = Column(String(10), nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    chat_session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<Message id={self.id} session_id={self.session_id} sender={self.sender_type} timestamp={self.timestamp}>"
