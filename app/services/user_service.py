import logging

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError
from typing import Optional, Tuple

from app.models.user import User

from app.repositories.interfaces.i_user_repository import IUserRepository


class UserService:

    def __init__(self, user_repository: IUserRepository, db_session_factory: sessionmaker):

        logger.info("Hàm khởi tạo UserService được gọi")
        logger.debug(f"Nhận được user_repository: {user_repository}, kiểu: {type(user_repository)}")
        logger.debug(f"Nhận được db_session_factory: {db_session_factory}, kiểu: {type(db_session_factory)}")

        self.user_repository = user_repository
        self.db_session_factory = db_session_factory

    def login_user(self, username, password) -> Optional[User]:

        logger.debug(f"login_user called for username: {username}")
        if self.user_repository:
            user = self.user_repository.find_by_username(username)

            if user and user.check_password(password):

                logger.info(f"User '{username}' logged in successfully.")
                return user
            else:

                logger.info(f"Login failed for user: {username}")
                return None
        else:

            logger.warning("user_repository is None in login_user.")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:

        logger.debug(f"get_user_by_id called for user_id: {user_id}, type: {type(user_id)}")
        if self.user_repository:
            user = self.user_repository.find_by_id(user_id)

            logger.debug(f"get_user_by_id received user from Repository: {user}, type: {type(user)}")
            return user
        else:

            logger.warning("user_repository is None in get_user_by_id.")
            return None

    def register_user(self, username: str, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:

        logger.debug(f"register_user called for username: {username}, email: {email}")
        if not self.user_repository:
            logger.warning("user_repository is None in register_user.")
            return None, "Hệ thống đăng ký chưa sẵn sàng."

        existing_user_by_username = self.user_repository.find_by_username(username)
        if existing_user_by_username:
            logger.info(f"Registration failed: Username '{username}' already exists.")
            return None, "Tên đăng nhập đã tồn tại."

        existing_user_by_email = self.user_repository.find_by_email(email)
        if existing_user_by_email:
            logger.info(f"Registration failed: Email '{email}' already exists.")
            return None, "Email đã được sử dụng bởi tài khoản khác."

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        try:
            self.user_repository.save(new_user)

            logger.info(f"User '{username}' ({email}) registered successfully via repository save.")
            return new_user, None

        except Exception as e:

            logger.error(f"An error occurred during registration save for '{username}' ({email}): {e}", exc_info=True)
            if isinstance(e, IntegrityError):
                return None, "Lỗi dữ liệu: có thể email đã tồn tại."
            else:
                return None, "Đã xảy ra lỗi không mong muốn khi lưu thông tin đăng ký."


logger.info("Đã load module app/services/user_service.py.")
