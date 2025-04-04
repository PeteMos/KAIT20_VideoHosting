import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import re
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads/videos'  # Папка для загрузки видео
db = SQLAlchemy(app)

ROLE_TRANSLATIONS = {
    'student': 'Студент',
    'teacher': 'Преподаватель',
    'admin': 'Администратор',
}

# Создаем папку для загрузки видео, если она не существует
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) 

# Модель видео
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.String(10), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(150), nullable=False)

@app.before_request
def create_tables():
    db.create_all()

# Декоратор для проверки роли
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session or session.get('role') != role:
                flash('У вас нет прав для доступа к этой странице.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    full_name = session.get('username')
    return render_template('index.html', username=full_name, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('images', filename)

def get_user_from_db(login):
    # Проверяем, является ли ввод email
    if re.match(r"[^@]+@[^@]+\.[^@]+", login):
        return User.query.filter_by(email=login).first()
    else:
        return User.query.filter_by(username=login).first()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        
        user = get_user_from_db(login)  # Используем новую функцию для получения пользователя

        # Проверяем, существует ли пользователь и правильный ли пароль
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['role'] = user.role  # Сохраняем роль пользователя в сессии
            flash('Вы успешно вошли в систему.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('login.html', ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/register', methods=['GET', 'POST'])
@role_required('admin')  # Добавляем проверку роли
def register():
    if request.method == 'POST':
        username = request.form['username']
        login = request.form['login']  # Это email
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        role = request.form['role']

        # Проверка на пустые поля
        if not username:
            flash('Имя пользователя не может быть пустым.', 'error')
            return redirect(url_for('register'))

        if not login or not re.match(r"[^@]+@[^@]+\.[^@]+", login):
            flash('Введите корректный email.', 'error')
            return redirect(url_for('register'))

        if not password or not password_confirm:
            flash('Пароль и подтверждение пароля обязательны.', 'error')
            return redirect(url_for('register'))

        if password != password_confirm:
            flash('Пароли не совпадают. Пожалуйста, попробуйте снова.', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter((User .email == login) | (User .username == username)).first()
        if existing_user:
            flash('Пользователь с указанным email или именем пользователя уже существует. Пожалуйста, используйте другой.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        # Создаем нового пользователя с выбранной ролью
        new_user = User(username=username, email=login, password=hashed_password, role=role)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('index'))  # Перенаправление на главную страницу
        except Exception as e:
            db.session.rollback()  # Откат транзакции в случае ошибки
            print(f'Ошибка при регистрации: {e}')  # Вывод ошибки в консоль
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html', ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


def generate_reset_token(email):
    token = jwt.encode({'reset_password': email, 'exp':
    datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_reset_token(token):
    try:
        email = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    return email

@app.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.email)
            # Здесь можно добавить код для отправки email с токеном
            flash('Инструкции по сбросу пароля отправлены на ваш email.', 'info')
        else:
            flash('Если такой email существует в нашей базе, вы получите инструкции по сбросу пароля.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('reset-password-request.html', ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if email is None:
        flash('Недействительный или истекший токен', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Пароли не совпадают. Пожалуйста, попробуйте снова.', 'error')
            return redirect(url_for('reset_password', token=token))

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Пароль успешно сброшен!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Пользователь не найден.', 'error')
            return redirect(url_for('login'))

    return render_template('reset-password.html', token=token)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)  # Удаляем роль из сессии
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/add_video', methods=['GET', 'POST'])
@role_required('teacher')
def add_video():
    if request.method == 'POST':
        video_title = request.form['title']
        video_description = request.form['description']
        video_duration = request.form['duration']
        video_author = request.form['author']
        video_course = request.form['course']
        video_file = request.files.get('video_file')

        # Проверка, что файл был загружен и имеет допустимый формат
        if video_file and allowed_file(video_file.filename):
            filename = secure_filename(video_file.filename)
            video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Сохраняем информацию о видео в базе данных
            new_video = Video(title=video_title, description=video_description,
                              duration=video_duration, author=video_author,
                              course=video_course, filename=filename)
            db.session.add(new_video)
            db.session.commit()

            flash('Видео успешно добавлено!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Пожалуйста, загрузите корректный видеофайл.', 'error')

    return render_template('add_video.html', current_user=session, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

def allowed_file(filename):
    allowed_extensions = {'mp4', 'avi', 'mov', 'mkv'}  # Добавьте нужные форматы
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/course/programming')
def course_programming():
    course_title = "Основы программирования"
    return render_template('course-programming.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/web-development')
def course_web_development():
    course_title = "Веб-разработка"
    return render_template('course-web-development.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/design')
def course_design():
    course_title = "Основы дизайна"
    return render_template('course-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/javascript')
def course_javascript():
    course_title = "Основы JavaScript"
    return render_template('course-javascript.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/machine-learning')
def course_machine_learning():
    course_title = "Введение в машинное обучение"
    return render_template('course-machine-learning.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/mobile-development')
def course_mobile_development():
    course_title = "Разработка мобильных приложений"
    return render_template('course-mobile-development.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/cybersecurity')
def course_cybersecurity():
    course_title = "Основы кибербезопасности"
    return render_template('course-cybersecurity.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/database')
def course_database():
    course_title = "Работа с базами данных"
    return render_template('course-database.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/ux-ui-design')
def course_ux_ui_design():
    course_title = "UX/UI дизайн"
    return render_template('course-ux-ui-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/devops')
def course_devops():
    course_title = "Основы DevOps"
    return render_template('course-devops.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/graphic-design')
def course_graphic_design():
    course_title = "Основы графического дизайна"
    return render_template('course-graphic-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/digital-marketing')
def course_digital_marketing():
    course_title = "Основы цифрового маркетинга"
    return render_template('course-digital-marketing.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

if __name__ == '__main__':
    app.run(debug=True)

