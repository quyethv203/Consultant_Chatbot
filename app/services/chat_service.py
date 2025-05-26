# app/services/chat_service.py

from datetime import datetime
import pytz
from types import SimpleNamespace

from app.models.chat_session import ChatSession
from app.repositories.implementations.sqlalchemy_chat_repository import SQLAlchemyChatRepository
# Import ChatbotService (vẫn cần để khai báo kiểu dữ liệu)
from app.services.chatbot_service import ChatbotService


class ChatService:
    # Thay đổi __init__ để nhận chatbot_service làm tham số
    def __init__(self, chat_repository: SQLAlchemyChatRepository, chatbot_service: ChatbotService):
        self.chat_repository = chat_repository
        self.chatbot_service = chatbot_service  # Gán instance chatbot_service được truyền vào

    def process_user_message(self, user_id: int, user_message: str, session_id: int = None):
        print(
            f"Calling ChatService.process_user_message for user {user_id} with input '{user_message}' and session_id {session_id}.")

        # 1. Lấy hoặc tạo session
        session_obj = None
        if session_id:
            session_obj = self.chat_repository.get_session_by_id(session_id)
            if not session_obj:
                # Nếu session_id không hợp lệ, tạo session mới
                session_obj = self.chat_repository.create_session(user_id)
                print(
                    f"WARNING: Session ID {session_id} khong hop le hoac khong ton tai. Tao session moi voi ID: {session_obj.id}")
        else:
            session_obj = self.chat_repository.create_session(user_id)
            print(f"Tao session moi voi ID: {session_obj.id}")

        # 2. Lưu tin nhắn người dùng vào lịch sử chat
        self.chat_repository.save_message(session_obj.id, "user", user_message)
        print(f"Tin nhắn người dùng đã lưu thành công.")  # 3. Gọi chatbot để lấy phản hồi
        bot_response_content = ""
        try:
            # Lấy RAG Chain từ chatbot_service đã được inject
            rag_chain = self.chatbot_service.get_rag_chain_instance()
            if rag_chain is None:
                bot_response_content = "RAG Chain khong the khoi tao. Vui long thu lai sau."
                print("ERROR: get_rag_chain() tra ve None. RAG Chain khong the khoi tao.")
            else:
                print(f"Dang goi RAG Chain.invoke() voi input: '{user_message}'")

                # Kiểm tra nếu đang sử dụng Advanced RAG
                chatbot_info = self.chatbot_service.get_chatbot_info()
                print(f"Sử dụng {chatbot_info['type']} với các tính năng: {', '.join(chatbot_info['features'])}")

                # Gọi RAG chain với input phù hợp
                if chatbot_info['type'] == 'Advanced RAG':
                    # Advanced RAG chỉ cần string input
                    response = rag_chain.invoke(user_message)
                else:
                    # Basic RAG cần dict input
                    response = rag_chain.invoke({"question": user_message})

                bot_response_content = response
                print(f"Nhan phan hoi tu RAG Chain: '{bot_response_content}'")
                newline_char = '\n'
                print(f"DEBUG - Bot response contains newlines: {newline_char in bot_response_content}")
                print(f"DEBUG - Bot response repr: {repr(bot_response_content)}")

        except Exception as e:
            bot_response_content = f"Đã xảy ra lỗi khi xử lý yêu cầu của bạn: {e}"
            print(f"ERROR: Loi khi goi RAG Chain.invoke(): {e}")

        # 4. Lưu phản hồi của chatbot vào lịch sử chat
        self.chat_repository.save_message(session_obj.id, "bot", bot_response_content)  # 5. Trả về kết quả
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time = datetime.now(vietnam_tz)
        return {
            "session_id": session_obj.id,
            "user_message": user_message,
            "bot_response": bot_response_content,
            "timestamp": current_time.isoformat()
        }

    def get_chat_history(self, session_id: int):
        # Lấy lịch sử tin nhắn của một session cụ thể
        messages = self.chat_repository.get_messages_by_session_id(session_id)
        print(f"Đã lấy {len(messages)} tin nhắn.")
        for i, msg in enumerate(messages):
            print(f"DEBUG Message {i}: timestamp from DB = {msg.timestamp}, type = {type(msg.timestamp)}")
            newline_char = '\n'
            print(f"DEBUG Message {i}: content has newlines = {newline_char in str(msg.content)}")

        history = [
            SimpleNamespace(
                sender_type=msg.sender_type,
                content=msg.content,
                timestamp=msg.timestamp  # Sử dụng timestamp trực tiếp từ DB (đã là local time)
            )
            for msg in messages
        ]
        return history

    def create_new_chat_session(self, user_id: int) -> ChatSession:
        print(f"Creating new chat session for user {user_id}")
        new_session = self.chat_repository.create_session(user_id)
        self.chat_repository.save_message(new_session.id, "bot",
                                          "Chào bạn! Tôi là Chatbot hỗ trợ sinh viên. Tôi có thể giúp gì cho bạn liên quan đến nội quy và quy chế của nhà trường?")
        return new_session

    def get_user_chat_history(self, user_id: int, session_id: int = None):
        if session_id:
            return self.get_chat_history(session_id)
        else:
            sessions = self.chat_repository.get_messages_by_session_id(user_id)
            if sessions:
                latest_session = max(sessions, key=lambda s: s.created_at)
                return self.get_chat_history(latest_session.id)
            return []

    def reset_chatbot_conversation_history(self):
        """Reset lịch sử hội thoại của chatbot (chỉ dành cho Advanced RAG)"""
        try:
            self.chatbot_service.reset_conversation_history()
            return {"status": "success", "message": "Đã reset lịch sử hội thoại chatbot"}
        except Exception as e:
            print(f"ERROR khi reset conversation history: {e}")
            return {"status": "error", "message": f"Lỗi: {str(e)}"}

    def get_chatbot_info(self):
        """Lấy thông tin về chatbot đang sử dụng"""
        try:
            return self.chatbot_service.get_chatbot_info()
        except Exception as e:
            print(f"ERROR khi lấy chatbot info: {e}")
            return {
                "type": "Unknown",
                "features": [],
                "description": "Không thể lấy thông tin chatbot"
            }

    def get_all_chat_sessions(self, user_id: int):
        """Lấy tất cả chat sessions của user bao gồm cả messages"""
        print(f"CHAT_SERVICE: get_all_chat_sessions called for user_id {user_id}")
        try:
            # Lấy tất cả sessions của user từ repository
            sessions = self.chat_repository.get_all_sessions_by_user_id(user_id)
            print(f"CHAT_SERVICE: Repository returned {len(sessions)} sessions")

            # Tạo list result để tránh detached instance error
            result_sessions = []

            for session in sessions:
                messages = self.chat_repository.get_messages_by_session_id(session.id)
                print(f"CHAT_SERVICE: Session {session.id} has {len(messages)} messages")

                # Tạo object mới từ session data để tránh detached instance
                session_dict = {
                    'id': session.id,
                    'user_id': session.user_id,
                    'start_time': session.start_time,
                    'messages': messages
                }

                # Tạo SimpleNamespace object để có thể truy cập như attribute
                from types import SimpleNamespace
                session_obj = SimpleNamespace(**session_dict)
                result_sessions.append(session_obj)

            # Sắp xếp theo thời gian tạo mới nhất
            result_sessions.sort(key=lambda x: x.start_time if x.start_time else datetime.min, reverse=True)

            print(f"CHAT_SERVICE: Returning {len(result_sessions)} sessions")
            return result_sessions
        except Exception as e:
            print(f"ERROR: Error getting all chat sessions for user {user_id}: {e}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            return []
