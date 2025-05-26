import logging

logger = logging.getLogger(__name__)

from flask import Flask, render_template, jsonify, request

from flask_login import LoginManager

from app.core.database import SessionLocal, init_db

from app.repositories.implementations.sqlalchemy_user_repository import SQLAlchemyUserRepository

from app.services.user_service import UserService

from app.controllers.user_controller import user_bp
from app.controllers.chat_controller import chat_bp

from app.models import user
from app.models import chat_session
from app.models import message

from app.core.config import Config


def create_app():
    logger.info("Bắt đầu tạo ứng dụng Flask.")

    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    logger.debug(f"Flask app static_folder configured as: {app.static_folder}")

    app.config.from_object(Config)

    login_manager = LoginManager()
    login_manager.login_view = 'user.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        if user_id is not None:
            try:
                user_id_int = int(user_id)
                logger.debug(f"load_user called for user_id: {user_id_int}, type: {type(user_id_int)}")

                user_service_instance = None
                try:
                    db_session_factory = SessionLocal
                    if db_session_factory is None:
                        logger.error("SessionLocal factory is None in load_user.")
                        return None

                    user_repo_instance = SQLAlchemyUserRepository(db_session_factory=db_session_factory)
                    user_service_instance = UserService(user_repository=user_repo_instance,
                                                        db_session_factory=db_session_factory)

                    logger.debug(f"load_user created UserService instance manually: {user_service_instance}")

                except Exception as e:
                    logger.error(f"Error manually creating dependencies in load_user: {e}", exc_info=True)
                    return None

                if user_service_instance:
                    user = user_service_instance.get_user_by_id(user_id_int)

                    logger.debug(f"load_user received user from UserService: {user}, type: {type(user)}")
                    logger.debug(f"load_user FINAL return: {user}, type: {type(user)}")
                    return user
                else:
                    logger.error("UserService instance is None after manual creation in load_user.")
                    return None

            except ValueError:
                logger.warning(f"Invalid user_id format in load_user: {user_id}")
                return None
        return None

    logger.debug("Bắt đầu chạy hàm init_db từ __init__.py.")
    init_db()
    logger.debug("Kết thúc hàm init_db từ __init__.py.")

    logger.info("Đang đăng ký Blueprints.")

    app.register_blueprint(user_bp)
    app.register_blueprint(chat_bp)
    logger.info("Đã đăng ký Blueprints.")

    @app.errorhandler(404)
    def page_not_found(error):
        logger.warning(f"404 Not Found: {request.url}")

        return render_template('404.html', error=error), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"500 Internal Server Error: {error}", exc_info=True)

        return render_template('500.html', error=error), 500

    @app.errorhandler(Exception)
    def handle_exception(e):

        logger.error(f"Unhandled Exception: {e}", exc_info=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:

            return jsonify({"error": "Đã xảy ra lỗi server nội bộ không mong muốn."}), 500
        else:
            return internal_server_error(e)    # Custom Jinja2 filter to handle newlines
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to <br> tags."""
        if not text:
            return text
        # Handle various newline formats
        text = str(text)
        text = text.replace('\r\n', '<br>')
        text = text.replace('\n', '<br>')
        text = text.replace('\r', '<br>')
        text = text.replace('\\n', '<br>')
        return text

    # Custom Jinja2 filter to handle markdown bold
    @app.template_filter('markdown_bold')
    def markdown_bold_filter(text):
        """Convert **text** to <strong>text</strong>."""
        if not text:
            return text
        import re
        # Replace **text** with <strong>text</strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', str(text))
        return text

    logger.info("Kết thúc tạo ứng dụng Flask.")
    return app


logger.info("Đã load module app/__init__.py.")
