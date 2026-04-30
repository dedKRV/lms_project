import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, LoginManager, login_required, logout_user, current_user

from data import db_session
from data.users import User
from data.notifications import Notification
from data.add_user import AddUserForm
from data.login_form import LoginForm
from course_routes import init_course_routes
from lesson_routes import init_lesson_routes
from block_routes import init_block_routes
from notification_routes import init_notification_routes
from ai_routes import init_ai_routes
from profile_routes import init_profile_routes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
FILES_FOLDER = os.path.join(BASE_DIR, "files")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["FILES_FOLDER"] = FILES_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FILES_FOLDER, exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)

init_course_routes(app)
init_lesson_routes(app)
init_block_routes(app)
init_notification_routes(app)
init_ai_routes(app)
init_profile_routes(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.create_session().close()

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, int(user_id))
    db_sess.close()
    return user

@app.route('/api/notifications/count')
@login_required
def notifications_count():
    db_sess = db_session.create_session()
    count = db_sess.query(Notification).filter_by(
        user_id=current_user.id, is_read=False
    ).count()
    db_sess.close()
    return jsonify({'count': count})

@app.route('/')
def index():
    return render_template("index.html", hide_nav_auth=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = AddUserForm()

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if not name or not email or not password or not role:
            flash("Все поля обязательны для заполнения")
            return render_template('register.html', form=form, hide_nav_auth=True)

        db_sess = db_session.create_session()

        existing_user = db_sess.query(User).filter(User.email == email).first()
        if existing_user:
            db_sess.close()
            flash("Email уже зарегистрирован")
            return render_template('register.html', form=form, hide_nav_auth=True)

        user = User()
        user.name = name
        user.email = email
        user.role = role
        user.set_password(password)

        db_sess.add(user)
        db_sess.commit()
        db_sess.close()

        flash("Регистрация успешна! Теперь войдите.")
        return redirect("/login")

    return render_template('register.html', form=form, hide_nav_auth=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember_me') else False

        if not email or not password:
            flash("Введите email и пароль")
            return render_template('login.html', form=form, hide_nav_auth=True)

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == email).first()
        db_sess.close()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect("/dashboard")

        flash("Неверный email или пароль")
        return render_template('login.html', form=form, hide_nav_auth=True)

    return render_template('login.html', form=form, hide_nav_auth=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def main():
    db_session.global_init("db/lms.db")
    app.run(debug=True)

if __name__ == '__main__':
    main()