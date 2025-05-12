# app/services/chat_service.py
import logging
# logging khong dung nua, su dung print
# logger = logging.getLogger(__name__) # Co the xoa neu khong dung logger

from typing import Optional, Tuple # Import Tuple de dinh nghia return type
from datetime import datetime # Can cho timestamp

from sqlalchemy.orm import Session, sessionmaker # Can de lam viec voi DB session

from app.repositories.interfaces.i_chat_repository import IChatRepository
from app.services.chatbot_service import ChatbotService # Import ChatbotService moi
# <-- SUA LAI IMPORT MODELS -->
from app.models.chat_session import ChatSession # Import ChatSession tu file chat_session.py
from app.models.message import Message # Import Message tu file message.py

# from app.core.database import SessionLocal # Khong import SessionLocal truc tiep o day nua

# XOA import NLP cu (COMMENTED OUT) de code sach hon
# from app.nlp.nlp_model import NLPModel # XOA import NLP cu
# from app.nlp.response_generator import ResponseGenerator


class ChatService:
    """
    Service quan ly logic nghiep vu lien quan den chat sessions va messages.
    No su dung ChatRepository de luu tru va ChatbotService de lay phan hoi tu bot.
    """
    def __init__(self, chat_repository: IChatRepository, chatbot_service: ChatbotService, db_session_factory: sessionmaker):
        # logger.info("Hàm khởi tạo ChatService được gọi") # Bo log
        print("Hàm khởi tạo ChatService được gọi")
        self.chat_repository = chat_repository
        self.chatbot_service = chatbot_service # Nhận ChatbotService mới
        self.db_session_factory = db_session_factory
        # logger.debug(f"Nhận được chat_repository: {self.chat_repository}, kiểu: {type(self.chat_repository)}") # Bo log
        # logger.debug(f"Nhận được chatbot_service: {self.chatbot_service}, kiểu: {type(self.chatbot_service)}") # Bo log
        # logger.debug(f"Nhận được db_session_factory: {self.db_session_factory}, kiểu: {type(self.db_session_factory)}") # Bo log


    def create_new_chat_session(self, user_id: int) -> ChatSession | None:
        """
        Tao mot phien chat moi cho nguoi dung.
        """
        # logger.debug(f"Đang tạo phiên chat mới cho người dùng ID: {user_id}") # Bo log
        print(f"Đang tạo phiên chat mới cho người dùng ID: {user_id}")
        try:
            new_session = self.chat_repository.create_session(user_id=user_id)
            # logger.info(f"Đã tạo phiên chat mới với ID: {new_session.id}") # Bo log
            print(f"Đã tạo phiên chat mới với ID: {new_session.id}")
            return new_session
        except Exception as e:
            # logger.error(f"Lỗi khi tạo phiên chat mới cho người dùng {user_id}: {e}", exc_info=True) # Bo log
            print(f"ERROR: Lỗi khi tạo phiên chat mới cho người dùng {user_id}: {e}")
            return None


    # Sua dinh nghia return type hint
    def process_user_message(self, user_id: int, user_input: str, session_id: Optional[int]) -> Tuple[Optional[str], Optional[datetime], Optional[int]]:
        """
        Xử lý tin nhắn từ người dùng: tìm/tạo session, lấy phản hồi từ bot,
        lưu cả tin nhắn người dùng và bot vào database.
        Trả về nội dung và timestamp của tin nhắn bot, cùng session ID đã sử dụng.
        """
        # logger.debug(f"process_user_message called for user_id: {user_id}, input: '{user_input}', provided session_id: {session_id}") # Bo log
        print(f"process_user_message called for user_id: {user_id}, input: '{user_input}', provided session_id: {session_id}")

        current_session = None

        # 1. Tìm hoặc tạo ChatSession
        if session_id is not None:
            # logger.debug(f"Tìm kiếm session hiện có với ID: {session_id}") # Bo log
            current_session = self.chat_repository.get_session_by_id(session_id=session_id)
            # logger.debug(f"Kết quả tìm session: {current_session}") # Bo log

        if current_session is None:
            # logger.debug(f"Không tìm thấy session hoặc session_id là None. Tìm session gần nhất hoặc tạo mới cho user {user_id}.") # Bo log
            print(f"Không tìm thấy session hoặc session_id là None. Tìm session gần nhất hoặc tạo mới cho user {user_id}.")
            latest_session = self.chat_repository.get_latest_session_by_user_id(user_id=user_id)

            if latest_session:
                current_session = latest_session
                # logger.info(f"Đã tìm thấy session gần nhất: {current_session.id} cho user {user_id}.") # Bo log
                print(f"Đã tìm thấy session gần nhất: {current_session.id} cho user {user_id}.")
            else:
                # logger.info(f"Không tìm thấy session hiện có cho user {user_id}. Tạo một session mới.") # Bo log
                print(f"Không tìm thấy session hiện có cho user {user_id}. Tạo một session mới.")
                current_session = self.create_new_chat_session(user_id=user_id)
                if current_session is None:
                     # logger.error(f"ERROR: Không thể tạo session mới cho user {user_id}.") # Bo log
                     print(f"ERROR: Không thể tạo session mới cho user {user_id}.")
                     # Tra ve gia tri None cho tat ca neu that bai
                     return None, None, None # <-- TRa ve 3 None neu that bai tao session


        if current_session is None:
             # logger.error("ERROR: current_session là None sau khi tìm hoặc tạo. Lỗi nghiêm trọng.") # Bo log
             print("ERROR: current_session là None sau khi tìm hoặc tạo. Lỗi nghiêm trọng.")
             # Tra ve gia tri None cho tat ca neu that bai
             return None, None, None # <-- Tra ve 3 None neu session la None


        # 2. Lưu tin nhắn người dùng
        try:
            # logger.debug(f"Đang lưu tin nhắn người dùng vào session {current_session.id}") # Bo log
            user_message = self.chat_repository.save_message(
                session_id=current_session.id,
                sender_type='user',
                content=user_input
            )
            # logger.info(f"Tin nhắn người dùng đã lưu thành công với ID: {user_message.id}") # Bo log
            print(f"Tin nhắn người dùng đã lưu thành công với ID: {user_message.id}")
        except Exception as e:
             # logger.error(f"ERROR: Lỗi khi lưu tin nhắn người dùng vào session {current_session.id}: {e}", exc_info=True) # Bo log
             print(f"ERROR: Lỗi khi lưu tin nhắn người dùng vào session {current_session.id}: {e}")
             # Tra ve mot phan hoi loi cho bot va None timestamp/session_id (hoac session.id hien tai)
             return "Đã xảy ra lỗi khi lưu tin nhắn của bạn.", None, current_session.id # <-- Tra ve 3 gia tri neu gap loi luu


        # 3. Lấy phản hồi từ Chatbot (RAG)
        bot_response_content = self.chatbot_service.get_chatbot_response(user_input=user_input)
        # logger.info(f"Chatbot responded with text: '{bot_response_content}'") # Bo log
        print(f"Chatbot responded with text: '{bot_response_content}'")


        # 4. Lưu tin nhắn Bot
        try:
            # logger.debug(f"Đang lưu tin nhắn bot vào session {current_session.id}") # Bo log
            bot_message = self.chat_repository.save_message(
                session_id=current_session.id,
                sender_type='bot',
                content=bot_response_content
            )
            # logger.info(f"Tin nhắn bot đã lưu thành công với ID: {bot_message.id}") # Bo log
            print(f"Tin nhắn bot đã lưu thành công với ID: {bot_message.id}")
        except Exception as e:
             # logger.error(f"ERROR: Lỗi khi lưu tin nhắn bot vào session {current_session.id}: {e}", exc_info=True) # Bo log
             print(f"ERROR: Lỗi khi lưu tin nhắn bot vào session {current_session.id}: {e}")
             # Van co the tra ve content va timestamp cua user message vua luu? Hoac None cho bot message?
             # Hay tra ve content bot, None cho timestamp bot, va session ID
             return bot_response_content, None, current_session.id # <-- Tra ve 3 gia tri neu gap loi luu bot


        # 5. Cập nhật session ID trong Flask session (ko o day)
        # Logic nay nam o controller


        # 6. Trả về nội dung và timestamp của tin nhắn bot, và session ID đã sử dụng
        # logger.debug("Trả về nội dung và timestamp của tin nhắn bot.") # Bo log
        # Ham nay tra ve content(string), timestamp(datetime), session_id(int)
        return bot_message.content, bot_message.timestamp, current_session.id


    def get_user_chat_history(self, user_id: int, session_id: Optional[int]) -> list[Message]:
        """
        Lay lich su tin nhan cho nguoi dung va session cu the.
        Neu session_id la None, lay session gan nhat.
        """
        # logger.debug(f"get_user_chat_history called for user_id: {user_id}, provided session_id: {session_id}") # Bo log
        print(f"get_user_chat_history called for user_id: {user_id}, provided session_id: {session_id}")

        current_session = None

        # 1. Tìm ChatSession
        if session_id is not None:
            # logger.debug(f"Tìm kiếm session với ID: {session_id}") # Bo log
            current_session = self.chat_repository.get_session_by_id(session_id=session_id)
            # logger.debug(f"Kết quả tìm session: {current_session}") # Bo log

        if current_session is None:
             # logger.debug(f"Không tìm thấy session hoặc session_id là None. Tìm session gần nhất cho user {user_id}.") # Bo log
             print(f"Không tìm thấy session hoặc session_id là None. Tìm session gần nhất cho user {user_id}.")
             current_session = self.chat_repository.get_latest_session_by_user_id(user_id=user_id)
             # logger.debug(f"Kết quả tìm session gần nhất: {current_session}") # Bo log
             print(f"Kết quả tìm session gần nhất: {current_session}")


        # 2. Lấy lịch sử tin nhắn từ session đó
        if current_session:
            # logger.debug(f"Đang lấy tin nhắn cho session ID: {current_session.id}") # Bo log
            messages = self.chat_repository.get_messages_by_session_id(session_id=current_session.id)
            # logger.debug(f"Đã lấy {len(messages)} tin nhắn.") # Bo log
            print(f"Đã lấy {len(messages)} tin nhắn.")
            return messages
        else:
            # logger.debug(f"Không có session nào được tìm thấy cho user {user_id}. Trả về lịch sử trống.") # Bo log
            print(f"Không có session nào được tìm thấy cho user {user_id}. Trả về lịch sử trống.")
            return [] # Trả về danh sách trống nếu không có session