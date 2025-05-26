import logging

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session, sessionmaker
from typing import Optional, List
from app.models.user import User
from app.repositories.interfaces.i_user_repository import IUserRepository


class SQLAlchemyUserRepository(IUserRepository):
    """SQLAlchemy implementation of the User Repository."""

    def __init__(self, db_session_factory: sessionmaker):

        logger.info("Hàm khởi tạo SQLAlchemyUserRepository được gọi")
        logger.debug(f"Nhận được db_session_factory: {db_session_factory}, kiểu: {type(db_session_factory)}")

        self.db_session_factory = db_session_factory

    def find_by_id(self, user_id: int) -> Optional[User]:
        logger.debug(f"find_by_id called for user_id: {user_id}, type: {type(user_id)}")
        db_session_instance: Optional[Session] = None
        user = None
        try:
            db_session_instance = self.db_session_factory()
            user = db_session_instance.query(User).get(user_id)
            logger.debug(f"find_by_id query result: {user}, type: {type(user)}")
            return user
        except Exception as e:
            logger.error(f"Lỗi khi lấy user bằng ID trong repo: {e}", exc_info=True)
            return None
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong find_by_id.")

    def find_by_username(self, username: str) -> Optional[User]:
        logger.debug(f"find_by_username called for username: {username}")
        db_session_instance: Optional[Session] = None
        user = None
        try:
            db_session_instance = self.db_session_factory()
            user = db_session_instance.query(User).filter_by(username=username).first()
            logger.debug(f"find_by_username found user: {user}")
            return user
        except Exception as e:
            logger.error(f"Lỗi khi lấy user bằng username trong repo: {e}", exc_info=True)
            return None
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong find_by_username.")

    def find_by_email(self, email: str) -> Optional[User]:
        logger.debug(f"find_by_email called for email: {email}")
        db_session_instance: Optional[Session] = None
        user = None
        try:
            db_session_instance = self.db_session_factory()
            user = db_session_instance.query(User).filter_by(email=email).first()
            logger.debug(f"find_by_email found user: {user}")
            return user
        except Exception as e:
            logger.error(f"Lỗi khi lấy user bằng email trong repo: {e}", exc_info=True)
            return None
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong find_by_email.")

    def save(self, user: User) -> None:
        logger.debug(f"save called for user: {user}")
        db_session_instance: Optional[Session] = None
        try:
            db_session_instance = self.db_session_factory()
            db_session_instance.add(user)
            db_session_instance.commit()
            logger.info(f"User {user.username} đã lưu thành công.")
        except Exception as e:
            logger.error(f"Lỗi khi lưu user trong repo: {e}", exc_info=True)
            if db_session_instance:
                db_session_instance.rollback()
            raise e
        finally:
            if db_session_instance:
                db_session_instance.close()
                logger.debug("Session instance đóng trong save.")

