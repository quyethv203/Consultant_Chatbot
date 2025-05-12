import logging

logger = logging.getLogger(__name__)

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from app.core.database import SessionLocal

from app.repositories.implementations.sqlalchemy_user_repository import SQLAlchemyUserRepository

from app.services.user_service import UserService

user_bp = Blueprint('user', __name__)


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    logger.debug(f"'/login' accessed. current_user.is_authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        logger.info("User already authenticated, redirecting to chat.")
        return redirect(url_for('chat.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Vui lòng nhập tên đăng nhập và mật khẩu.', 'warning')
            return render_template('login.html', username=username)

        user_service_instance = None
        try:
            db_session_factory = SessionLocal
            if db_session_factory is None:
                logger.error("SessionLocal factory is None in user.login.")
                raise Exception("SessionLocal factory is None.")

            repo_instance = SQLAlchemyUserRepository(db_session_factory=db_session_factory)
            user_service_instance = UserService(user_repository=repo_instance, db_session_factory=db_session_factory)

            logger.debug(f"login: Manually created UserService instance: {user_service_instance}")

        except Exception as e:

            logger.error(f"login: Error manually creating dependencies: {e}", exc_info=True)
            flash(f'Lỗi nội bộ khi chuẩn bị chức năng đăng nhập: {e}', 'danger')
            return render_template('login.html', username=username)

        if user_service_instance:
            user = user_service_instance.login_user(username, password)

            if user:
                login_user(user)

                logger.info(f"Flask-Login login_user called successfully for user: {user.username}")

                logger.debug(f"Session content after Flask-Login login_user: {session}")
                logger.debug(f"Session _user_id after Flask-Login login_user: {session.get('_user_id')}")

                flash('Đăng nhập thành công!', 'success')
                return redirect(url_for('chat.index'))

            else:
                flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')

                logger.info(f"Login failed for username: {username}")
        else:
            pass

        return render_template('login.html', username=username)

    return render_template('login.html')


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    logger.debug(f"'/register' accessed. current_user.is_authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        logger.info(f"User {current_user.username} is logged in, redirecting from register.")
        return redirect(url_for('chat.index'))
    username = None
    email = None
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password or not confirm_password:
            flash('Vui lòng điền đầy đủ thông tin.', 'warning')
            return render_template('register.html', username=username, email=email)

        if password != confirm_password:
            flash('Mật khẩu và xác nhận mật khẩu không khớp.', 'warning')
            return render_template('register.html', username=username, email=email)

        user_service_instance = None
        try:
            db_session_factory = SessionLocal
            if db_session_factory is None:
                logger.error("SessionLocal factory is None in user.register.")
                raise Exception("SessionLocal factory is None.")

            repo_instance = SQLAlchemyUserRepository(db_session_factory=db_session_factory)
            user_service_instance = UserService(user_repository=repo_instance, db_session_factory=db_session_factory)

            logger.debug(f"register: Manually created UserService instance: {user_service_instance}")

        except Exception as e:

            logger.error(f"register: Error manually creating dependencies: {e}", exc_info=True)
            flash(f'Lỗi nội bộ khi chuẩn bị chức năng đăng ký: {e}', 'danger')
            return render_template('register.html', username=username, email=email)

        if user_service_instance:
            try:
                user, message = user_service_instance.register_user(username, email, password)

                if user:
                    flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
                    return redirect(url_for('user.login'))
                else:
                    flash(message, 'danger')

                    logger.info(f"Registration failed for '{username}' ({email}): {message}")
                    return render_template('register.html', username=username, email=email)

            except ValueError as e:
                flash(str(e), 'danger')

                logger.info(f"Registration failed for '{username}' ({email}): {e}")
                return render_template('register.html', username=username, email=email)
            except Exception as e:
                flash('Đã xảy ra lỗi không mong muốn trong quá trình đăng ký. Vui lòng thử lại sau.', 'danger')

                logger.error(f"An unexpected error occurred during registration for '{username}' ({email}): {e}",
                             exc_info=True)
                return render_template('register.html', username=username, email=email)

        else:
            pass

    return render_template('register.html', username=username, email=email)


@user_bp.route('/logout')
@login_required
def logout():
    logger.debug(f"'/logout' accessed for user: {current_user.username}")
    logout_user()
    flash('Bạn đã đăng xuất.', 'info')

    logger.info("Flask-Login logout_user called.")
    return redirect(url_for('user.login'))


logger.info("Đã load module app/controllers/user_controller.py.")
