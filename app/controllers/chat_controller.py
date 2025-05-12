# app/controllers/chat_controller.py

import logging
# logging khong dung nua, su dung print
# logger = logging.getLogger(__name__) # Co the xoa neu khong dung logger

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user

from app.core.database import SessionLocal
# <-- CHỈ GIỮ DÒNG IMPORT DATETIME NAY -->
from datetime import datetime
# <-- IMPORT SIMPLENAMESPACE O DAY -->
from types import SimpleNamespace

from app.repositories.implementations.sqlalchemy_chat_repository import SQLAlchemyChatRepository

from app.services.chat_service import ChatService
from app.services.chatbot_service import ChatbotService


# XOA CAC IMPORT NLP CU NEU CON
# from app.nlp.nlp_model import NLPModel
# from app.nlp.response_generator import ResponseGenerator


chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

CURRENT_SESSION_ID_KEY = 'current_chat_session_id'


@chat_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id

    chat_service_instance = None
    try:
        db_session_factory = SessionLocal
        if db_session_factory is None:
            # logger.error("SessionLocal factory is None in chat.index.") # Bo log
            print("ERROR: SessionLocal factory is None in chat.index.")
            raise Exception("SessionLocal factory is None.")

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)
        # Tao instance ChatbotService moi (khong can truyen dependency NLP cu)
        # ChatbotService moi tu khoi tao RAG Chain ben trong
        chatbot_service_instance = ChatbotService()

        # TAO INSTANCE CHATSERVICE (TRUYEN CHATBOTSERVICE MOI)
        chat_service_instance = ChatService(
            chat_repository=chat_repo_instance,
            chatbot_service=chatbot_service_instance, # <-- Truyen ChatbotService moi
            db_session_factory=db_session_factory
        )

        # logger.debug(f"index: Manually created ChatService instance for GET: {chat_service_instance}") # Bo log

    except Exception as e:
        # logger.error(f"index: Error manually creating dependencies for GET: {e}", exc_info=True) # Bo log
        print(f"ERROR: index: Error manually creating dependencies for GET: {e}")
        flash(f'Lỗi nội bộ khi chuẩn bị chức năng trò chuyện.', 'danger') # Bo hien thi chi tiet loi e
        return render_template('chat.html', chat_history=[], error_message="Lỗi nội bộ khi chuẩn bị chức năng trò chuyện.")


    # logger.debug(f"Processing GET request for chat history for user_id: {user_id}") # Bo log
    chat_history = []
    current_session_id = session.get(CURRENT_SESSION_ID_KEY)

    if chat_service_instance:
        try:
            chat_history = chat_service_instance.get_user_chat_history(
                user_id=user_id,
                session_id=current_session_id
            )
            # logger.debug(f"Got {len(chat_history)} messages for history.") # Bo log

            if current_session_id is None and chat_history:
                 inferred_session_id = chat_history[0].session_id if chat_history else None
                 if inferred_session_id:
                      session[CURRENT_SESSION_ID_KEY] = inferred_session_id
                      # logger.debug(f"Inferred and set current_chat_session_id in flask.session: {inferred_session_id}") # Bo log

        except Exception as e:
            # logger.error(f"Lỗi khi tải lịch sử trò chuyện: {e}", exc_info=True) # Bo log
            print(f"ERROR: Lỗi khi tải lịch sử trò chuyện: {e}")
            flash(f'Lỗi khi tải lịch sử trò chuyện.', 'danger') # Bo hien thi chi tiet loi e

    # Tao mot tin nhan chào mừng nếu lịch sử trống
    if not chat_history:
        initial_bot_message_content = "Chào bạn! Tôi là Chatbot hỗ trợ sinh viên. Tôi có thể giúp gì cho bạn liên quan đến nội quy và quy chế của nhà trường?"
        # Tao mot object gia de hien thi giong Message model cho template, KHONG luu DB
        # Can SimpleNamespace de tao object co cac thuoc tinh can thiet
        # SimpleNamespace da duoc import o dau file
        initial_bot_message = SimpleNamespace(
             sender_type='bot',
             content=initial_bot_message_content,
             timestamp=datetime.utcnow() # <-- datetime da import dung vi tri
        )
        chat_history = [initial_bot_message] # Thay the lich su rong bang tin nhan chao mung

    # Cac dong import sai vi tri da duoc chuyen len dau file
    # from datetime import datetime # <-- XOA DONG NAY
    # from types import SimpleNamespace # <-- XOA DONG NAY

    return render_template('chat.html', chat_history=chat_history)




@chat_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    user_id = current_user.id
    user_input = None

    try:
        request_data = request.get_json()
        if request_data:
             user_input = request_data.get('user_input')

        if not user_input:
             # logger.warning("Received empty user input from JSON body in /send_message.") # Bo log
             print("WARNING: Received empty user input from JSON body in /send_message.")
             return jsonify({"error": "Input tin nhắn không được rỗng."}), 400
    except Exception as e:
         # logger.error(f"Error getting JSON data in /send_message: {e}", exc_info=True) # Bo log
         print(f"ERROR: Error getting JSON data in /send_message: {e}")
         return jsonify({"error": "Lỗi định dạng dữ liệu JSON."}), 400


    # logger.debug(f"Received user input (POST /send_message, from JSON): {user_input}") # Bo log

    chat_service_instance = None
    try:
        db_session_factory = SessionLocal
        if db_session_factory is None:
            # logger.error("SessionLocal factory is None in chat.send_message.") # Bo log
            print("ERROR: SessionLocal factory is None in chat.send_message.")
            raise Exception("SessionLocal factory is None.")

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)

        # TAO INSTANCE CHATBOTSERVICE MOI
        chatbot_service_instance = ChatbotService()


        # TAO INSTANCE CHATSERVICE (TRUYEN CHATBOTSERVICE MOI)
        chat_service_instance = ChatService(
            chat_repository=chat_repo_instance,
            chatbot_service=chatbot_service_instance, # <-- Truyen ChatbotService moi
            db_session_factory=db_session_factory
        )

        # logger.debug(f"send_message: Manually created ChatService instance: {chat_service_instance}") # Bo log

    except Exception as e:
        # logger.error(f"send_message: Error manually creating dependencies: {e}", exc_info=True) # Bo log
        print(f"ERROR: send_message: Error manually creating dependencies: {e}")
        return jsonify({"error": "Lỗi nội bộ khi chuẩn bị dịch vụ."}), 500 # Bo hien thi chi tiet loi e

    current_session_id = session.get(CURRENT_SESSION_ID_KEY)

    if chat_service_instance:
        try:
            # logger.debug(f"Calling ChatService.process_user_message for user {user_id} with input '{user_input}' and session_id {current_session_id}.") # Bo log
            print(f"Calling ChatService.process_user_message for user {user_id} with input '{user_input}' and session_id {current_session_id}.")

            # <-- CACH NHAN GIA TRI TRA VE DA DUOC SUA DE UNPACK DUNG 3 GIA TRI -->
            # Ham service tra ve: content (str), timestamp (datetime), session_id (int)
            result_tuple = chat_service_instance.process_user_message(
                user_id=user_id,
                user_input=user_input,
                session_id=current_session_id
            )

            # Kiem tra dinh dang ket qua tra ve (mong doi la tuple 3 phan tu)
            if isinstance(result_tuple, tuple) and len(result_tuple) == 3:
                # UNPACK DUNG 3 gia tri vao cac bien rieng
                bot_response_text, bot_response_timestamp, used_session_id = result_tuple

                # Cap nhat session ID trong Flask session neu can
                if current_session_id is None or current_session_id != used_session_id:
                    session[CURRENT_SESSION_ID_KEY] = used_session_id
                    print(f"Updated current_chat_session_id in flask.session: {used_session_id}")


                # Kiem tra xem timestamp co hop le khong truoc khi goi isoformat()
                if isinstance(bot_response_timestamp, datetime):
                    bot_response_data = {
                       'bot_response': bot_response_text, # Su dung content da unpack
                       'bot_timestamp': bot_response_timestamp.isoformat() # Goi isoformat tren datetime object
                    }
                    print("Returning JSON response for bot message.")
                    return jsonify(bot_response_data), 200
                else:
                    # Neu timestamp khong phai datetime (vd: None do loi trong service)
                    print(f"ERROR: ChatService.process_user_message returned invalid timestamp type: {type(bot_response_timestamp)}. Text: {bot_response_text}")
                    return jsonify({"error": "Đã xảy ra lỗi khi xử lý tin nhắn (Thời gian phản hồi không hợp lệ)."}), 500


            else:
                # Neu service tra ve ket qua khong dung dinh dang mong doi (khong phai tuple 3 phan tu)
                print(f"ERROR: ChatService.process_user_message returned unexpected format: {result_tuple}")
                # Ban co the thu kiem tra xem result_tuple[0] co phai la thong bao loi khong
                # neu co, gui thong bao do cho nguoi dung
                error_message = "Đã xảy ra lỗi nội bộ với dịch vụ chat (Kết quả trả về không hợp lệ)."
                # Cố gắng trích xuất thông báo lỗi nếu kết quả trả về là chuỗi
                if isinstance(result_tuple, str):
                     error_message = result_tuple
                return jsonify({"error": error_message}), 500


        except Exception as e:
             print(f"ERROR: Error during ChatService.process_user_message: {e}")
             # Tra ve thong bao loi chung cho nguoi dung
             return jsonify({"error": "Lỗi khi xử lý tin nhắn."}), 500
    else:
         print("ERROR: ChatService instance is None.")
         return jsonify({"error": "Hệ thống trò chuyện tạm thời không sẵn sàng."}), 500



@chat_bp.route('/new_session', methods=['POST'])
@login_required
def new_session():
    user_id = current_user.id

    chat_service_instance = None
    try:
        db_session_factory = SessionLocal
        if db_session_factory is None:
            print("ERROR: SessionLocal factory is None in chat.new_session.")
            raise Exception("SessionLocal factory is None.")

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)

        # TAO INSTANCE CHATBOTSERVICE MOI
        chatbot_service_instance = ChatbotService()


        # TAO INSTANCE CHATSERVICE (TRUYEN CHATBOTSERVICE MOI)
        chat_service_instance = ChatService(
            chat_repository=chat_repo_instance,
            chatbot_service=chatbot_service_instance, # <-- Truyen ChatbotService moi
            db_session_factory=db_session_factory
        )

    except Exception as e:
        print(f"ERROR: new_session: Error manually creating dependencies: {e}")
        return jsonify({"error": "Lỗi nội bộ khi chuẩn bị dịch vụ."}), 500


    if chat_service_instance:
        try:
            print(f"Calling Service to create new chat session for user {user_id}.")
            new_chat_session = chat_service_instance.create_new_chat_session(user_id=user_id)

            if new_chat_session:
                 print(f"New session ID {new_chat_session.id} created for user {user_id}.")
                 session[CURRENT_SESSION_ID_KEY] = new_chat_session.id
                 return jsonify({"success": True, "session_id": new_chat_session.id}), 201
            else:
                 print("ERROR: ChatService.create_new_chat_session returned None.")
                 return jsonify({"error": "Không thể tạo phiên chat mới."}), 500

        except Exception as e:
             print(f"ERROR: Error during ChatService.create_new_chat_session: {e}")
             return jsonify({"error": "Lỗi khi tạo phiên chat mới."}), 500
    else:
         print("ERROR: ChatService instance is None.")
         return jsonify({"error": "Hệ thống trò chuyện tạm thời không sẵn sàng."}), 500