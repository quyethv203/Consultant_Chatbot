import inject

from inject import InjectorException

from app.repositories.interfaces.i_user_repository import IUserRepository
from app.repositories.implementations.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.repositories.interfaces.i_chat_repository import IChatRepository
from app.repositories.implementations.sqlalchemy_chat_repository import SQLAlchemyChatRepository

from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.services.chatbot_service import ChatbotService

from app.core.database import SessionLocal

from app.nlp.nlp_model import NLPModel
from app.nlp.response_generator import ResponseGenerator

print(f"DEBUG_DEPENDENCIES: Giá trị của SessionLocal sau khi import từ database.py (module level): {SessionLocal}")
print("DEBUG_DEPENDENCIES: Đã load module app/core/dependencies.py.")


def configure_inject(app):
    """
    Cấu hình Dependency Injection cho ứng dụng Flask.
    Hàm này được gọi trong create_app của app/__init__.py
    """
    print("DEBUG_DEPENDENCIES: Bắt đầu cấu hình inject (configure_inject function).")
    print("DEBUG_DEPENDENCIES: Đang gọi inject.configure...")

    inject.configure(config, clear=True)

    print("DEBUG_DEPENDENCIES: inject.configure đã chạy xong.")


def config(binder):
    """
    Hàm cấu hình chi tiết cho binder của inject.
    Được gọi bởi inject.configure.
    """
    print("DEBUG_DEPENDENCIES: Bắt đầu hàm config của inject.")

    print(f"DEBUG_DEPENDENCIES: Đang cố gắng bind SessionLocal: {SessionLocal}")
    if SessionLocal is None:
        print("DEBUG_DEPENDENCIES: Lỗi: SessionLocal là None. Không thể bind.")
        raise InjectorException("Database SessionLocal is not initialized. Check database.py setup.")

    binder.bind(SessionLocal, SessionLocal)
    print("DEBUG_DEPENDENCIES: Đã bind SessionLocal factory.")

    print("DEBUG_DEPENDENCIES: Đang cố gắng bind IUserRepository bằng Provider.")
    try:

        binder.bind(IUserRepository,
                    lambda: SQLAlchemyUserRepository(db_session_instance=inject.instance(SessionLocal)))
        print("DEBUG_DEPENDENCIES: Đã bind IUserRepository bằng Provider.")

    except NameError:
        print("DEBUG_DEPENDENCIES: Cảnh báo: Không tìm thấy UserRepository Implementation. Không bind User Repository.")
    except Exception as e:
        print(
            f"DEBUG_DEPENDENCIES: Lỗi khi bind IUserRepository bằng Provider: {e}. Kiểm tra lại lớp UserRepository và bind SessionLocal. Bind IUserRepository với None.")
        binder.bind(IUserRepository, None)

    print("DEBUG_DEPENDENCIES: Đang cố gắng bind IChatRepository bằng Provider.")
    try:

        binder.bind(IChatRepository,
                    lambda: SQLAlchemyChatRepository(db_session_instance=inject.instance(SessionLocal)))
        print("DEBUG_DEPENDENCIES: Đã bind IChatRepository bằng Provider.")

    except NameError:
        print(
            "DEBUG_DEPENDENCIES: Cảnh báo: Không tìm thấy Chat Repository Implementation. Không bind Chat Repository.")
    except Exception as e:
        print(
            f"DEBUG_DEPENDENCIES: Lỗi khi bind IChatRepository bằng Provider: {e}. Kiểm tra lại lớp ChatRepository và bind SessionLocal. Bind IChatRepository với None.")
        binder.bind(IChatRepository, None)

    print("DEBUG_DEPENDENCIES: Đang cố gắng bind UserService bằng Provider.")
    try:

        binder.bind(UserService, lambda: UserService(
            user_repository=inject.instance(IUserRepository),
            db_session_instance=inject.instance(SessionLocal)
        ))
        print("DEBUG_DEPENDIES: Đã bind UserService bằng Provider.")

    except NameError:
        print("DEBUG_DEPENDENCIES: Cảnh báo: Không tìm thấy UserService. Không bind User Service.")
    except Exception as e:
        print(
            f"DEBUG_DEPENDENCIES: Lỗi khi bind UserService bằng Provider: {e}. Kiểm tra lại lớp UserService và dependencies. Bind UserService với None.")
        binder.bind(UserService, None)

    print("DEBUG_DEPENDENCIES: Đang cố gắng bind ChatService bằng Provider.")
    try:

        binder.bind(ChatService, lambda: ChatService(chat_repository=inject.instance(IChatRepository)))
        print("DEBUG_DEPENDENCIES: Đã bind ChatService bằng Provider.")

    except NameError:
        print("DEBUG_DEPENDENCIES: Cảnh báo: Không tìm thấy ChatService. Không bind Chat Service.")
    except Exception as e:
        print(
            f"DEBUG_DEPENDENCIES: Lỗi khi bind ChatService bằng Provider: {e}. Kiểm tra lại lớp ChatService và dependency. Bind ChatService với None.")
        binder.bind(ChatService, None)

    print("DEBUG_DEPENDENCIES: Đang cố gắng bind NLPModel (trực tiếp instance).")
    try:

        binder.bind(NLPModel, NLPModel())
        print("DEBUG_DEPENDENCIES: Đã bind NLPModel (trực tiếp instance).")
    except NameError:
        print("DEBUG_DEPENDENCIES: Cảnh báo: Không tìm thấy NLPModel. Không bind NLPModel.")
    except Exception as e:
        print(
            f"DEBUG_DEPENDENCIES: Lỗi khi bind NLPModel (trực tiếp instance): {e}. Kiểm tra lại __init__ của NLPModel. Bind NLPModel với None.")
        binder.bind(NLPModel, None)

    print("DEBUG_DEPENDENCIES: Đang cố gắng bind ResponseGenerator (trực tiếp instance).")
    try:

        binder.bind(ResponseGenerator, ResponseGenerator())
        print("DEBUG_DEPENDENCIES: Đã bind ResponseGenerator (trực tiếp instance).")
    except NameError:
        print("DEBUG_DEPENDENCIES: Cảnh báo: Không tìm thấy ResponseGenerator. Không bind ResponseGenerator.")
    except Exception as e:
        print(
            f"DEBUG_DEPENDENCIES: Lỗi khi bind ResponseGenerator (trực tiếp instance): {e}. Kiểm tra lại __init__ of ResponseGenerator. Bind ResponseGenerator with None.")
        binder.bind(ResponseGenerator, None)

    print("DEBUG_DEPENDENCIES: Đang cố gắng bind ChatbotService (trực tiếp instance).")
    try:

        binder.bind(ChatbotService, ChatbotService())
        print("DEBUG_DEPENDENCIES: Đã bind ChatbotService (trực tiếp instance).")
    except NameError:
        print("DEBUG_DEPENDENCIES: Cảnh báo: Không tìm thấy ChatbotService. Không bind ChatbotService.")
    except Exception as e:
        print(
            f"DEBUG_DEPENDENCIES: Lỗi khi bind ChatbotService (trực tiếp instance): {e}. Kiểm tra lại __init__ của ChatbotService. Bind ChatbotService with None.")
        binder.bind(ChatbotService, None)

    print("DEBUG_DEPENDENCIES: Kết thúc hàm config của inject.")
