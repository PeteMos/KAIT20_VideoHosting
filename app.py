import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import make_response
from models import db, User, Video, TestResult
from test import questions_data
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import datetime
import re
import jwt
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads/videos'  # Папка для загрузки видео
db.init_app(app)

def __repr__(self):
        return f'<Video {self.title}>'

@app.route('/test')
def test():
    return render_template('test.html', questions_data=questions_data, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

ROLE_TRANSLATIONS = {
    'student': 'Студент',
    'teacher': 'Преподаватель',
    'admin': 'Администратор',
}

# Создаем папку для загрузки видео, если она не существует
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    username = session.get('username') or request.cookies.get('username', 'Гость')
    role = session.get('role') or request.cookies.get('role', 'Пользователь')
    if not username or not role:
        # Логика для обработки отсутствия данных
        print("Cookies не найдены, используем значения по умолчанию.")
    return render_template('index.html', username=username, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

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
        
        user = get_user_from_db(login)

        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['role'] = user.role

            # Сохранение в cookies
            response = make_response(redirect(url_for('index')))
            response.set_cookie('username', user.username)
            response.set_cookie('role', user.role)
            return response
            
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

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    # Проверка авторизации пользователя
    if 'username' not in session:
        return redirect(url_for('login'))  # Перенаправление на страницу входа, если не авторизован

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.filter_by(username=session.get('username')).first()

        if user and check_password_hash(user.password, current_password):
            if new_password == confirm_password:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('index'))  # Возврат после успешного изменения пароля
            else:
                flash('Новые пароли не совпадают.', 'error')
        else:
            flash('Неверный текущий пароль.', 'error')

    # Возврат шаблона для GET-запроса или после неудачи в POST
    return render_template('change-password.html', ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    
    # Удаление cookies
    response = make_response(redirect(url_for('index')))
    response.set_cookie('username', '', expires=0)
    response.set_cookie('role', '', expires=0)
    
    flash('Вы вышли из системы.', 'info')
    return response

@app.route('/uploads/videos/<path:filename>')
def uploaded_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_video', methods=['GET', 'POST'])
@role_required('teacher')  # Проверка роли
def add_video():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        duration = request.form['duration']
        course = request.form['course']
        video_file = request.files['video_file']  # Получаем файл

        # Проверяем, что файл загружен и имеет допустимый формат
        if video_file and allowed_file(video_file.filename):
            filename = secure_filename(video_file.filename)
            video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_file_path) 

            # Создаем новый объект Video
            new_video = Video(title=title, description=description, duration=duration, course=course, filename=filename, author=session.get('username'))
            db.session.add(new_video)
            db.session.commit()
            try:
                db.session.commit()  # Сохраняем изменения в базе данных
                flash('Видео успешно добавлено!', 'success')
            except Exception as e:
                db.session.rollback()  # Откатываем изменения в случае ошибки
                flash(f'Ошибка при добавлении видео: {str(e)}', 'error')
        else:
            flash('Пожалуйста, загрузите файл видео с допустимым форматом.', 'error')

    # Извлечение всех видео из базы данных для отображения
    videos = Video.query.filter_by(author=session.get('username')).all()
    return render_template('add_video.html', videos=videos, current_user=session, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/delete_video/<int:video_id>', methods=['POST'])
@role_required('teacher')  # Проверка роли
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], video.filename))
    flash('Видео успешно удалено!', 'success')
    return redirect(url_for('add_video'))

@app.route('/submit_test', methods=['POST'])
def submit_test():
    data = request.get_json()
    username = data.get('username')
    course = data.get('course')
    score = data.get('score')

    # Установка времени в московском часовом поясе
    moscow_tz = pytz.timezone('Europe/Moscow')
    timestamp = datetime.datetime.now(moscow_tz)  # Получаем текущее московское время

    try:
        # Сохранение результата в базе данных
        new_result = TestResult(username=username, course=course, score=score, timestamp=timestamp)
        db.session.add(new_result)
        db.session.commit()
        return jsonify({"result_id": new_result.id}), 200  # Возвращаем ответ в формате JSON
    except Exception as e:
        db.session.rollback()  # Откат транзакции в случае ошибки
        print(f'Ошибка при сохранении результата: {e}')  # Вывод ошибки в консоль
        return jsonify({"error": "Не удалось сохранить результат."}), 500

@app.route('/student_result/<int:result_id>')
def show_student_result(result_id):
    result = TestResult.query.get(result_id)
    if result:
        total_questions = len(questions_data[result.course])  # Получаем общее количество вопросов для курса
        return render_template('student_result.html', result=result, total_questions=total_questions, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)
    else:
        flash('Результат не найден.', 'error')
        return redirect(url_for('index'))  # Или на другую страницу

@app.route('/results')
@role_required('teacher')  # Проверка роли
def results():
    results = TestResult.query.all()  # Извлечение всех результатов из базы данных
    return render_template('results.html', results=results, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/delete_result/<int:result_id>', methods=['POST'])
@role_required('teacher')  # Проверка роли
def delete_result(result_id):
    result = TestResult.query.get(result_id)
    if result:
        db.session.delete(result)
        db.session.commit()
        flash('Результат успешно удален!', 'success')
    else:
        flash('Результат не найден.', 'error')
    return redirect(url_for('results'))

# @app.route('/course/programming')
# def course_programming():
#     if 'username' not in session:
#         flash('Вы должны быть авторизованы для просмотра видео.', 'error')
#         return redirect(url_for('login'))  # Перенаправляем на страницу входа
#     course_title = "Основы программирования"
#     videos = Video.query.filter_by(course="Основы программирования").all()  # Получаем видео для курса
#     return render_template('course-programming.html', videos=videos, page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/programming')
def course_programming():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправляем на страницу входа
    course_title = "Основы программирования"
    return render_template('course-programming.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/web-development')
def course_web_development():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Веб-разработка"
    return render_template('course-web-development.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/design')
def course_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы дизайна"
    return render_template('course-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/javascript')
def course_javascript():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы JavaScript"
    return render_template('course-javascript.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/machine-learning')
def course_machine_learning():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Введение в машинное обучение"
    return render_template('course-machine-learning.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/mobile-development')
def course_mobile_development():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Разработка мобильных приложений"
    return render_template('course-mobile-development.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/cybersecurity')
def course_cybersecurity():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы кибербезопасности"
    return render_template('course-cybersecurity.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/database')
def course_database():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Работа с базами данных"
    return render_template('course-database.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/ux-ui-design')
def course_ux_ui_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "UX/UI дизайн"
    return render_template('course-ux-ui-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/devops')
def course_devops():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы DevOps"
    return render_template('course-devops.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/graphic-design')
def course_graphic_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы графического дизайна"
    return render_template('course-graphic-design.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/digital-marketing')
def course_digital_marketing():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))
    course_title = "Основы цифрового маркетинга"
    return render_template('course-digital-marketing.html', page_title=course_title, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov', 'mkv'}

if __name__ == '__main__':
    app.run(debug=True)