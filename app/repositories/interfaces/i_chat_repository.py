from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.chat_session import ChatSession
from app.models.message import Message


class IChatRepository(ABC):

    @abstractmethod
    def create_session(self, user_id: int) -> ChatSession:
        pass

    @abstractmethod
    def get_latest_session_by_user_id(self, user_id: int) -> Optional[ChatSession]:
        pass

    @abstractmethod
    def get_session_by_id(self, session_id: int) -> Optional[ChatSession]:
        pass

    @abstractmethod
    def save_message(self, message: Message) -> None:
        pass

    @abstractmethod
    def get_messages_by_session_id(self, session_id: int) -> List[Message]:
        pass
