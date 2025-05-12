import logging

logger = logging.getLogger(__name__)

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError

from app.core.config import Config

logger.debug("Bắt đầu import module database.py.")

SQLALCHEMY_DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI
logger.debug(f"SQLALCHEMY_DATABASE_URL: {SQLALCHEMY_DATABASE_URL}")

engine = None

try:

    logger.debug("Đang tạo SQLAlchemy Engine...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
    logger.debug(f"Engine đã tạo: {engine}")

    logger.debug("Đang tạo SessionLocal factory...")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.debug(f"SessionLocal factory đã tạo: {SessionLocal}")

    logger.debug("Đang tạo Base declarative base...")
    Base = declarative_base()
    logger.debug(f"Base đã tạo: {Base}")

except OperationalError as e:

    logger.critical(f"Lỗi kết nối database: {e}", exc_info=True)


except Exception as e:

    logger.error(f"Lỗi trong quá trình setup module level của database.py: {e}", exc_info=True)

logger.debug("Kết thúc import module database.py.")


def init_db():
    logger.debug("Bắt đầu chạy hàm init_db.")
    try:

        if engine is None or Base is None:
            logger.error("Lỗi: Engine hoặc Base là None trong init_db. Kiểm tra lỗi module level.")

            return

        from app.models import user
        from app.models import chat_session
        from app.models import message

        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables created or already exist.")
    except Exception as e:

        logger.error(f"Lỗi trong quá trình Base.metadata.create_all: {e}", exc_info=True)

    logger.debug("Kết thúc hàm init_db.")
