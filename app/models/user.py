from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .chat_session import ChatSession

from app.core.database import Base

from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash


class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)

    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Thiết lập mật khẩu đã mã hóa."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Kiểm tra mật khẩu."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"
