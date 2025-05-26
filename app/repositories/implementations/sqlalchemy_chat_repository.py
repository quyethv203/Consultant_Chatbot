import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session, sessionmaker

from typing import List, Optional

from app.models.chat_session import ChatSession
from app.models.message import Message

from app.repositories.interfaces.i_chat_repository import IChatRepository


class SQLAlchemyChatRepository(IChatRepository):
    """SQLAlchemy implementation of the Chat Repository."""

    def __init__(self, db_session_factory: sessionmaker):
        logger.info("Hàm khởi tạo SQLAlchemyChatRepository được gọi")
        logger.debug(f"Nhận được db_session_factory: {db_session_factory}, kiểu: {type(db_session_factory)}")
        self.db_session_factory = db_session_factory

    def create_session(self, user_id: int) -> ChatSession:
        logger.debug(f"create_session called for user_id: {user_id}")

        db_session_instance: Optional[Session] = None
        new_session = None
        try:
            db_session_instance = self.db_session_factory()

            new_session = ChatSession(user_id=user_id)

            db_session_instance.add(new_session)
            db_session_instance.commit()

            db_session_instance.refresh(new_session)

            logger.info(f"ChatSession id {new_session.id} created successfully for user_id {user_id}.")
            return new_session

        except Exception as e:
            logger.error(f"Lỗi khi tạo ChatSession trong repo: {e}", exc_info=True)
            if db_session_instance:
                db_session_instance.rollback()
            raise e
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong create_session.")

    def get_latest_session_by_user_id(self, user_id: int) -> Optional[ChatSession]:
        logger.debug(f"get_latest_session_by_user_id called for user_id: {user_id}")
        db_session_instance: Optional[Session] = None
        session_obj = None
        try:
            db_session_instance = self.db_session_factory()

            session_obj = db_session_instance.query(ChatSession) \
                .filter_by(user_id=user_id) \
                .order_by(ChatSession.start_time.desc()) \
                .first()

            if session_obj:

                logger.debug(f"Found latest ChatSession id {session_obj.id} for user_id {user_id}.")
            else:

                logger.debug(f"No ChatSession found for user_id {user_id}.")

            return session_obj

        except Exception as e:
            logger.error(f"Lỗi khi lấy ChatSession mới nhất trong repo: {e}", exc_info=True)
            return None

        finally:
            if db_session_instance:
                db_session_instance.close()

                logger.debug("Session instance đóng trong get_latest_session_by_user_id.")

    def get_session_by_id(self, session_id: int) -> Optional[ChatSession]:

        logger.debug(f"get_session_by_id called for session_id: {session_id}")

        db_session_instance: Optional[Session] = None
        session_obj = None
        try:
            db_session_instance = self.db_session_factory()

            session_obj = db_session_instance.query(ChatSession) \
                .filter_by(id=session_id) \
                .first()

            if session_obj:

                logger.debug(f"Found ChatSession id {session_obj.id}.")
            else:

                logger.debug(f"No ChatSession found with id {session_id}.")

            return session_obj

        except Exception as e:
            logger.error(f"Lỗi khi lấy ChatSession theo ID trong repo: {e}", exc_info=True)
            return None
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong get_session_by_id.")

    def save_message(self, session_id: int, sender_type: str, content: str) -> Message:
        """Luu mot tin nhan vao database cho phien chat."""
        print(f"SQLAlchemyChatRepository.save_message called for session_id: {session_id}")

        with self.db_session_factory() as db:
            # Sử dụng Vietnam timezone
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            vietnam_time = datetime.now(vietnam_tz).replace(tzinfo=None)  # Convert to naive datetime

            new_message = Message(
                session_id=session_id,
                sender_type=sender_type,
                content=content,
                timestamp=vietnam_time
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            return new_message

    def get_messages_by_session_id(self, session_id: int) -> List[Message]:
        logger.debug(f"get_messages_by_session_id called for session_id: {session_id}")
        db_session_instance: Optional[Session] = None
        messages: List[Message] = []
        try:
            db_session_instance = self.db_session_factory()
            messages = db_session_instance.query(Message) \
                .filter_by(session_id=session_id) \
                .order_by(Message.timestamp) \
                .all()
            logger.debug(f"Found {len(messages)} messages for session_id {session_id}.")
            return messages
        except Exception as e:
            logger.error(f"Lỗi khi lấy tin nhắn theo session ID trong repo: {e}", exc_info=True)
            return []
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong get_messages_by_session_id.")

    def get_all_sessions_by_user_id(self, user_id: int) -> List[ChatSession]:
        """Get all chat sessions for a specific user"""
        logger.debug(f"get_all_sessions_by_user_id called for user_id: {user_id}")
        print(f"REPO: get_all_sessions_by_user_id called for user_id: {user_id}")
        db_session_instance: Optional[Session] = None
        sessions: List[ChatSession] = []
        try:
            db_session_instance = self.db_session_factory()
            sessions = db_session_instance.query(ChatSession) \
                .filter_by(user_id=user_id) \
                .order_by(ChatSession.start_time.desc()) \
                .all()
            logger.debug(f"Found {len(sessions)} sessions for user_id {user_id}.")
            print(f"REPO: Found {len(sessions)} sessions for user_id {user_id}")
            return sessions
        except Exception as e:
            logger.error(f"Lỗi khi lấy tất cả session theo user ID trong repo: {e}", exc_info=True)
            print(f"REPO ERROR: {e}")
            import traceback
            print(f"REPO TRACEBACK: {traceback.format_exc()}")
            return []
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong get_all_sessions_by_user_id.")

    def delete_session(self, session_id: int) -> bool:
        """Delete a chat session and all its messages"""
        logger.debug(f"delete_session called for session_id: {session_id}")
        db_session_instance: Optional[Session] = None
        try:
            db_session_instance = self.db_session_factory()

            # First delete all messages in the session
            messages_deleted = db_session_instance.query(Message) \
                .filter_by(session_id=session_id) \
                .delete()

            # Then delete the session itself
            session_deleted = db_session_instance.query(ChatSession) \
                .filter_by(id=session_id) \
                .delete()

            db_session_instance.commit()

            logger.info(f"Deleted session {session_id} with {messages_deleted} messages.")
            return session_deleted > 0

        except Exception as e:
            logger.error(f"Lỗi khi xóa session {session_id}: {e}", exc_info=True)
            if db_session_instance:
                db_session_instance.rollback()
            return False
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong delete_session.")
