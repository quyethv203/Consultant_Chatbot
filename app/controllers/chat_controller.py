# app/controllers/chat_controller.py

from datetime import datetime

from flask import Blueprint, request, jsonify, session, flash, render_template
from flask_login import login_required, current_user

from app.core.database import SessionLocal  # Import SessionLocal để lấy db_session_factory
from app.repositories.implementations.sqlalchemy_chat_repository import SQLAlchemyChatRepository
from app.services.chat_service import ChatService
from app.services.chatbot_service import ChatbotService  # <-- Vẫn cần import ChatbotService ở đây

chat_bp = Blueprint('chat', __name__, url_prefix='/')
CURRENT_SESSION_ID_KEY = 'current_chat_session_id'


@chat_bp.route('/', methods=['GET'])
def index():
    """Main landing page - show homepage for everyone"""
    return render_template('index.html')


@chat_bp.route('/chat', methods=['GET'])
def chat_interface():
    """Main chat interface for all users"""
    # Kiểm tra xem user có đăng nhập không
    if current_user.is_authenticated:
        user_id = current_user.id
        return render_authenticated_chat(user_id)
    else:
        # User chưa đăng nhập - cho phép chat nhưng không lưu lịch sử
        return render_guest_chat()


def render_authenticated_chat(user_id):
    requested_session_id = request.args.get('session_id')  # Get session_id from URL parameter
    chat_service_instance = None

    try:
        db_session_factory = SessionLocal
        if db_session_factory is None:
            print("ERROR: SessionLocal factory is None in chat.chat_interface.")
            raise Exception("SessionLocal factory is None.")

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)
        chatbot_service_instance = ChatbotService()

        chat_service_instance = ChatService(
            chat_repository=chat_repo_instance,
            chatbot_service=chatbot_service_instance
        )

    except Exception as e:
        print(f"ERROR: chat_interface: Error manually creating dependencies for GET: {e}")
        flash(f'Lỗi nội bộ khi chuẩn bị chức năng trò chuyện.', 'danger')
        return render_template('chat.html', chat_history=[],
                               error_message="Lỗi nội bộ khi chuẩn bị chức năng trò chuyện.")
    chat_history = []
    current_session_id = session.get(CURRENT_SESSION_ID_KEY)

    if chat_service_instance:
        try:
            # If a specific session is requested, verify it belongs to the user and use it
            if requested_session_id:
                session_obj = chat_repo_instance.get_session_by_id(int(requested_session_id))
                if session_obj and session_obj.user_id == user_id:
                    current_session_id = int(requested_session_id)
                    session[CURRENT_SESSION_ID_KEY] = current_session_id
                    print(f"Switched to requested session: {current_session_id}")
                else:
                    print(f"ERROR: Requested session {requested_session_id} not found or unauthorized")
                    flash('Session không tồn tại hoặc bạn không có quyền truy cập.', 'warning')

            # If no valid session ID in Flask session or URL, try to get the latest session for this user
            if not current_session_id:
                latest_session = chat_repo_instance.get_latest_session_by_user_id(user_id)
                if latest_session:
                    current_session_id = latest_session.id
                    session[CURRENT_SESSION_ID_KEY] = current_session_id
                    print(f"Found existing session with ID: {current_session_id}")
                else:
                    # No existing session, create a new one
                    new_chat_session = chat_service_instance.create_new_chat_session(user_id=user_id)
                    if new_chat_session:
                        session[CURRENT_SESSION_ID_KEY] = new_chat_session.id
                        current_session_id = new_chat_session.id
                        print(f"Created new chat session with ID: {current_session_id}")
                    else:
                        print("ERROR: Could not create new chat session.")
                        flash('Không thể tạo phiên chat mới.', 'danger')
                        return render_template('chat.html', chat_history=[],
                                               error_message="Không thể tạo phiên chat mới.")  # Get chat history for current session
            if current_session_id:
                chat_history = chat_service_instance.get_chat_history(current_session_id)
                print(f"DEBUG: Retrieved {len(chat_history)} messages from chat session {current_session_id}")
                for i, msg in enumerate(chat_history):
                    print(
                        f"DEBUG: Message {i}: sender={msg.sender_type}, content_length={len(msg.content)}, timestamp={msg.timestamp}")
            else:
                print("DEBUG: No current_session_id found")
                chat_history = []

        except Exception as e:
            print(f"ERROR: chat_interface: Error getting chat history: {e}")
            flash('Lỗi khi tải lịch sử chat.', 'danger')

    return render_template('chat.html', chat_history=chat_history)


@chat_bp.route('/history', methods=['GET'])
@login_required
def chat_history():
    """Display chat history for the current user"""
    user_id = current_user.id
    print(f"CHAT_HISTORY: Current user ID = {user_id}")
    chat_service_instance = None
    all_sessions = []

    try:
        db_session_factory = SessionLocal
        if db_session_factory is None:
            print("ERROR: SessionLocal factory is None in chat.chat_history.")
            raise Exception("SessionLocal factory is None.")

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)
        chatbot_service_instance = ChatbotService()

        chat_service_instance = ChatService(
            chat_repository=chat_repo_instance,
            chatbot_service=chatbot_service_instance
        )
        
        # Get all chat sessions for the user
        all_sessions = chat_service_instance.get_all_chat_sessions(user_id=user_id)
        print(f"CHAT_HISTORY: Retrieved {len(all_sessions)} chat sessions for user {user_id}")
        
        # Debug: Print session details
        for i, session in enumerate(all_sessions[:3]):  # Show first 3 sessions
            print(f"Session {i}: ID={session.id}, start_time={session.start_time}, messages_count={len(session.messages) if hasattr(session, 'messages') and session.messages else 0}")

    except Exception as e:
        print(f"ERROR: chat_history: Error getting chat sessions: {e}")
        flash('Lỗi khi tải lịch sử chat.', 'danger')

    print(f"CHAT_HISTORY: Passing {len(all_sessions)} sessions to template")
    return render_template('chat_history.html', chat_sessions=all_sessions)


def render_guest_chat():
    """Render chat interface for guest users (no login required)"""
    # Trả về template với lịch sử chat trống
    return render_template('chat.html', chat_history=[], is_guest=True)


@chat_bp.route('/send_message', methods=['POST'])
def send_message():
    # Kiểm tra xem user có đăng nhập không
    if current_user.is_authenticated:
        user_id = current_user.id
        return send_message_authenticated(user_id)
    else:
        # Guest user - xử lý tin nhắn nhưng không lưu lịch sử
        return send_message_guest()


def send_message_authenticated(user_id):
    """Handle message sending for authenticated users with chat history saving"""
    user_input = None

    try:
        request_data = request.get_json()
        if request_data:
            user_input = request_data.get('user_input')

        if not user_input:
            print("WARNING: Received empty user input from JSON body in /send_message.")
            return jsonify({"error": "Input tin nhắn không được rỗng."}), 400
    except Exception as e:

        print(f"ERROR: Error getting JSON data in /send_message: {e}")
        return jsonify({"error": "Lỗi định dạng dữ liệu JSON."}), 400

    chat_service_instance = None
    try:
        db_session_factory = SessionLocal
        if db_session_factory is None:
            print("ERROR: SessionLocal factory is None in chat.send_message.")
            raise Exception("SessionLocal factory is None.")

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)
        chatbot_service_instance = ChatbotService()  # <-- Khởi tạo ChatbotService ở đây

        chat_service_instance = ChatService(
            chat_repository=chat_repo_instance,
            chatbot_service=chatbot_service_instance  # <-- Truyền instance vào ChatService
        )
    except Exception as e:
        print(f"ERROR: send_message: Error manually creating dependencies: {e}")
        return jsonify({"error": "Lỗi nội bộ khi chuẩn bị dịch vụ."}), 500

    current_session_id = session.get(CURRENT_SESSION_ID_KEY)

    if chat_service_instance:
        try:
            print(
                f"Calling ChatService.process_user_message for user {user_id} with input '{user_input}' and session_id {current_session_id}.")
            result_dict = chat_service_instance.process_user_message(  # Đổi tên biến để rõ ràng hơn
                user_id=user_id,
                user_message=user_input,
                session_id=current_session_id
            )

            # Kiểm tra định dạng trả về từ ChatService.process_user_message
            if isinstance(result_dict, dict):
                bot_response_text = result_dict.get('bot_response')
                bot_response_timestamp_str = result_dict.get('timestamp')
                used_session_id = result_dict.get('session_id')

                if bot_response_timestamp_str:
                    bot_response_timestamp = datetime.fromisoformat(bot_response_timestamp_str)
                else:
                    bot_response_timestamp = datetime.utcnow()  # Fallback

                if current_session_id is None or current_session_id != used_session_id:
                    session[CURRENT_SESSION_ID_KEY] = used_session_id
                    print(f"Updated current_chat_session_id in flask.session: {used_session_id}")

                bot_response_data = {
                    'bot_response': bot_response_text,
                    'bot_timestamp': bot_response_timestamp.isoformat()
                }
                print("Returning JSON response for bot message.")
                return jsonify(bot_response_data), 200
            else:
                print(f"ERROR: ChatService.process_user_message returned unexpected format: {result_dict}")
                error_message = "Đã xảy ra lỗi nội bộ với dịch vụ chat (Kết quả trả về không hợp lệ)."
                if isinstance(result_dict, str):
                    error_message = result_dict
                return jsonify({"error": error_message}), 500


        except Exception as e:
            print(f"ERROR: Error during ChatService.process_user_message: {e}")
            return jsonify({"error": "Lỗi khi xử lý tin nhắn."}), 500
    else:
        print("ERROR: ChatService instance is None.")
        return jsonify({"error": "Hệ thống trò chuyện tạm thời không sẵn sàng."}), 500


@chat_bp.route('/new_session', methods=['POST'])
def new_session():
    # Chỉ user đã đăng nhập mới có thể tạo session mới
    if not current_user.is_authenticated:
        return jsonify({"error": "Bạn cần đăng nhập để lưu phiên chat."}), 401
    user_id = current_user.id

    chat_service_instance = None
    try:
        db_session_factory = SessionLocal
        if db_session_factory is None:
            print("ERROR: SessionLocal factory is None in chat.new_session.")
            raise Exception("SessionLocal factory is None.")

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)
        chatbot_service_instance = ChatbotService()  # <-- Khởi tạo ChatbotService ở đây

        chat_service_instance = ChatService(
            chat_repository=chat_repo_instance,
            chatbot_service=chatbot_service_instance  # <-- Truyền instance vào ChatService
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


@chat_bp.route('/chatbot_info', methods=['GET'])
def get_chatbot_info():
    """Get information about the chatbot"""
    try:
        chatbot_info = {
            'name': 'AI Assistant for Students',
            'version': '2.0.0',
            'type': 'Advanced RAG với AI',
            'description': 'Tôi là Chatbot hỗ trợ sinh viên với khả năng AI tiên tiến. Tôi có thể giúp bạn tìm hiểu về nội quy, quy chế của nhà trường và trả lời các câu hỏi học tập.',
            'features': [
                'Tìm kiếm thông tin trong tài liệu',
                'Trả lời câu hỏi về nội quy trường học',
                'Hỗ trợ học tập và nghiên cứu',
                'Ghi nhớ ngữ cảnh cuộc trò chuyện',
                'Tìm kiếm thông minh với AI'
            ],
            'rag_type': 'Advanced RAG với AI',
            'last_updated': '2024-01-15'
        }
        return jsonify(chatbot_info), 200
    except Exception as e:
        print(f"ERROR: Error getting chatbot info: {e}")
        return jsonify({"error": "Không thể lấy thông tin chatbot."}), 500


@chat_bp.route('/reset_conversation', methods=['POST'])
def reset_conversation():
    """Reset the current conversation and start a new session"""
    # Guest users có thể reset conversation nhưng không tạo session mới
    if not current_user.is_authenticated:
        try:
            # Chỉ reset conversation memory trong chatbot service
            chatbot_service_instance = ChatbotService()
            chatbot_service_instance.reset_conversation()
            
            return jsonify({
                "success": True,
                "message": "Cuộc trò chuyện đã được reset.",
                "session_id": None
            }), 200
        except Exception as e:
            print(f"ERROR: Error resetting conversation for guest: {e}")
            return jsonify({"error": "Lỗi khi reset cuộc trò chuyện."}), 500
    user_id = current_user.id

    try:
        # Clear the current session from Flask session
        if CURRENT_SESSION_ID_KEY in session:
            del session[CURRENT_SESSION_ID_KEY]

        # Create dependencies
        db_session_factory = SessionLocal
        if db_session_factory is None:
            print("ERROR: SessionLocal factory is None in chat.reset_conversation.")
            raise Exception("SessionLocal factory is None.")

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)
        chatbot_service_instance = ChatbotService()

        chat_service_instance = ChatService(
            chat_repository=chat_repo_instance,
            chatbot_service=chatbot_service_instance
        )

        # Reset conversation memory in the chatbot service
        chatbot_service_instance.reset_conversation()

        # Create a new chat session
        new_chat_session = chat_service_instance.create_new_chat_session(user_id=user_id)

        if new_chat_session:
            session[CURRENT_SESSION_ID_KEY] = new_chat_session.id
            print(f"Conversation reset. New session ID: {new_chat_session.id}")

            return jsonify({
                "success": True,
                "message": "Cuộc trò chuyện đã được reset.",
                "session_id": new_chat_session.id
            }), 200
        else:
            return jsonify({"error": "Không thể tạo phiên chat mới sau khi reset."}), 500

    except Exception as e:
        print(f"ERROR: Error resetting conversation: {e}")
        return jsonify({"error": "Lỗi khi reset cuộc trò chuyện."}), 500


@chat_bp.route('/delete_session/<session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    """Delete a specific chat session"""
    user_id = current_user.id

    try:
        db_session_factory = SessionLocal
        if db_session_factory is None:
            print("ERROR: SessionLocal factory is None in delete_session.")
            return jsonify({"error": "Database connection error."}), 500

        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)

        # Verify that the session belongs to the current user
        session_obj = chat_repo_instance.get_session_by_id(session_id)
        if not session_obj:
            return jsonify({"error": "Session không tồn tại."}), 404

        if session_obj.user_id != user_id:
            return jsonify({"error": "Bạn không có quyền xóa session này."}), 403

        # Delete the session and all its messages
        success = chat_repo_instance.delete_session(session_id)

        if success:
            # If this was the current session, clear it from Flask session
            if session.get(CURRENT_SESSION_ID_KEY) == session_id:
                del session[CURRENT_SESSION_ID_KEY]

            return jsonify({"success": True, "message": "Đã xóa cuộc trò chuyện thành công."}), 200
        else:
            return jsonify({"error": "Không thể xóa cuộc trò chuyện."}), 500

    except Exception as e:
        print(f"ERROR: Error deleting session {session_id}: {e}")
        return jsonify({"error": "Lỗi khi xóa cuộc trò chuyện."}), 500


@chat_bp.route('/debug/sessions', methods=['GET'])
@login_required
def debug_sessions():
    """Debug route để kiểm tra sessions và messages"""
    user_id = current_user.id

    try:
        db_session_factory = SessionLocal
        chat_repo_instance = SQLAlchemyChatRepository(db_session_factory=db_session_factory)

        # Lấy tất cả sessions của user
        all_sessions = chat_repo_instance.get_all_sessions_by_user_id(user_id)

        debug_info = {
            'user_id': user_id,
            'total_sessions': len(all_sessions),
            'sessions': []
        }

        for session in all_sessions:
            messages = chat_repo_instance.get_messages_by_session_id(session.id)
            debug_info['sessions'].append({
                'session_id': session.id,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'total_messages': len(messages),
                'messages': [
                    {
                        'id': msg.id,
                        'sender_type': msg.sender_type,
                        'content': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                        'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
                    }
                    for msg in messages
                ]
            })

        return jsonify(debug_info), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def send_message_guest():
    """Handle message sending for guest users without saving chat history"""
    user_input = None

    try:
        request_data = request.get_json()
        if request_data:
            user_input = request_data.get('user_input')

        if not user_input:
            print("WARNING: Received empty user input from guest user in /send_message.")
            return jsonify({"error": "Input tin nhắn không được rỗng."}), 400
    except Exception as e:
        print(f"ERROR: Error getting JSON data from guest user: {e}")
        return jsonify({"error": "Lỗi định dạng dữ liệu JSON."}), 400

    try:
        # Tạo ChatbotService để xử lý tin nhắn
        chatbot_service_instance = ChatbotService()
        
        # Lấy RAG Chain để xử lý tin nhắn
        rag_chain = chatbot_service_instance.get_rag_chain_instance()
        if rag_chain is None:
            bot_response_content = "Hệ thống chatbot hiện không khả dụng. Vui lòng thử lại sau."
            print("ERROR: RAG Chain không thể khởi tạo cho guest user.")
        else:
            print(f"Guest user - Đang gọi RAG Chain với input: '{user_input}'")
            
            # Kiểm tra loại RAG và gọi phù hợp
            chatbot_info = chatbot_service_instance.get_chatbot_info()
            if chatbot_info['type'] == 'Advanced RAG':
                response = rag_chain.invoke(user_input)
            else:
                response = rag_chain.invoke({"question": user_input})
            
            bot_response_content = response
            print(f"Guest user - Nhận phản hồi từ RAG Chain: '{bot_response_content}'")

        # Trả về phản hồi cho guest user
        from datetime import datetime
        import pytz
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time = datetime.now(vietnam_tz)
        
        bot_response_data = {
            'bot_response': bot_response_content,
            'bot_timestamp': current_time.isoformat()
        }
        print("Guest user - Returning JSON response for bot message.")
        return jsonify(bot_response_data), 200

    except Exception as e:
        print(f"ERROR: Error processing guest user message: {e}")
        return jsonify({"error": "Lỗi khi xử lý tin nhắn."}), 500
