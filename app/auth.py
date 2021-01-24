from functools import wraps

from flask import Blueprint, render_template, url_for, request, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

from app import mysql, query_ex
from users_policy import UsersPolicy

bp = Blueprint('auth', __name__, url_prefix='/auth')


class User(UserMixin):
    def __init__(self, user_id, login, role_id):
        super().__init__()
        self.id = user_id
        self.login = login
        self.role_id = role_id

    def can(self, action, record=None):
        policy = UsersPolicy(record=record)
        method = getattr(policy, action, None)
        if method:
            return method()
        return False


def load_record(user_id):
    if user_id is None:
        return None
    with mysql.connection.cursor(named_tuple=True) as cursor:
        search_users = "SELECT * FROM users WHERE id = %s;"
        record = query_ex(search_users, [user_id], cursor, 'one')
    return record


def load_user(user_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        search_users = "SELECT * FROM users WHERE id = %s;"
        db_user = query_ex(search_users, [user_id], cursor, 'one')
    if db_user:
        return User(user_id=db_user.id,
                    login=db_user.login,
                    role_id=db_user.role)
    return None


def check_rights(action):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            record = load_record(kwargs.get('user_id'))
            if not current_user.can(action, record=record):
                flash('У вас недостаточно прав для доступа к данной странице.',
                      'danger')
                return redirect(url_for('index'))
            return func(*args, **kwargs)

        return wrapper

    return decorator


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = dict(request.form)
        if user_data['login'] and user_data['password']:
            with mysql.connection.cursor(named_tuple=True) as cursor:
                search_user = "SELECT * FROM users WHERE login = %s AND password_hash = SHA2(%s, 256);"
                db_user = query_ex(search_user,
                                   [user_data['login'], user_data['password']],
                                   cursor, 'one')
            if db_user:
                user_object = User(user_id=db_user.id,
                                   login=db_user.login,
                                   role_id=db_user.role)
                login_user(user_object,
                           remember=user_data.get('remember') == 'on')
                flash("u're logged in", 'success')
                return redirect(request.args.get('next') or url_for('index'))
            else:
                flash("incorrect login/pass", 'danger')
    return render_template('users/login.html')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


def init_login_manager(app):
    login_man = LoginManager()
    login_man.init_app(app)
    login_man.login_view = 'auth.login'
    login_man.login_message = 'need auth'
    login_man.login_message_category = 'danger'
    login_man.user_loader(load_user)
