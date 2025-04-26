import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import make_response
from models import db, User, Video, TestResult
from test import questions_data
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from moviepy import VideoFileClip
from PIL import Image
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
    return render_template('index.html', page_title=None, is_home=True, username=username, ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

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

@app.route('/thumbnails/<filename>')
def thumbnails(filename):
    # Возврат изображения
    return send_from_directory('uploads/thumbnails', filename)

def extract_frame(video_path, output_path):
    with VideoFileClip(video_path) as video:
        # Извлекаем кадр из середины видео
        frame_time = video.duration / 2
        frame = video.get_frame(frame_time)
        
        # Сохраняем кадр как изображение
        image = Image.fromarray(frame)
        image.save(output_path)

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

            # Извлекаем кадр из видео и сохраняем его как превью
            thumbnail_path = f'uploads/thumbnails/{filename}.jpg'  # Путь для сохранения превью
            extract_frame(video_file_path, thumbnail_path)  # Извлечение кадра

            # Создаем новый объект Video
            new_video = Video(
                title=title,
                description=description,
                duration=duration,
                course=course,
                filename=filename,
                author=session.get('username'),
                timestamp=datetime.datetime.now()
            )
            db.session.add(new_video)
            try:
                db.session.commit()  # Сохраняем изменения в базе данных
                flash('Видео успешно добавлено!', 'success')
                return redirect(url_for(f'course_{course.lower().replace(" ", "_")}'))
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

@app.route('/course/programming')
def course_programming():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправляем на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы программирования").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в программирование",
            "description": "В этом видео мы познакомимся с основами программирования и его значением в современном мире.",
            "duration": "8:00",
            "timestamp": "01.01.2025",
            "author": "Иван Иванов",
            "filename": "programming-intro.mp4"
        },
        {
            "title": "Переменные и типы данных",
            "description": "В этом видео мы обсудим, что такое переменные и какие типы данных существуют в Python.",
            "duration": "10:00",
            "timestamp": "02.01.2025",
            "author": "Анна Петрова",
            "filename": "variables.mp4"
        },
        {
            "title": "Условные операторы",
            "description": "В этом видео мы изучим, как использовать условные операторы для управления потоком программы.",
            "duration": "12:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Кузнецов",
            "filename": "conditional-statements.mp4"
        },
        {
            "title": "Циклы",
            "description": "В этом видео мы рассмотрим, что такое циклы и как их использовать в программировании.",
            "duration": "14:00",
            "timestamp": "04.01.2025",
            "author": "Ольга Воронова",
            "filename": "loops.mp4"
        },
        {
            "title": "Функции",
            "description": "В этом видео мы узнаем, как создавать и использовать функции в Python.",
            "duration": "11:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Федоров",
            "filename": "functions.mp4"
        },
        {
            "title": "Обработка исключений",
            "description": "В этом видео мы изучим, как обрабатывать исключения в Python.",
            "duration": "13:00",
            "timestamp": "06.01.2025",
            "author": "Анна Смирнова",
            "filename": "exception-handling.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-programming.html', 
                           page_title="Основы<br>программирования", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/web-development')
def course_web_development():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы веб-разработки").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в веб-разработку",
            "description": "Создайте свой первый веб-сайт с помощью HTML и CSS.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Иван Иванов",
            "filename": "videos/web-development-intro.mp4"
        },
        {
            "title": "CSS для начинающих",
            "description": "Изучите основы CSS для стилизации веб-страниц.",
            "duration": "15:00",
            "timestamp": "01.02.2025",
            "author": "Анна Петрова",
            "filename": "videos/css_basics.mp4"
        },
        {
            "title": "JavaScript для веб-разработчиков",
            "description": "Научитесь писать скрипты на JavaScript.",
            "duration": "20:00",
            "timestamp": "01.03.2025",
            "author": "Сергей Смирнов",
            "filename": "videos/javascript_basics.mp4"
        },
        {
            "title": "Создание адаптивного дизайна",
            "description": "Узнайте, как сделать ваш сайт адаптивным.",
            "duration": "25:00",
            "timestamp": "01.04.2025",
            "author": "Мария Иванова",
            "filename": "videos/responsive_design.mp4"
        },
        {
            "title": "Основы работы с API",
            "description": "Научитесь взаимодействовать с API для получения данных.",
            "duration": "18:00",
            "timestamp": "01.05.2025",
            "author": "Алексей Кузнецов",
            "filename": "videos/api_basics.mp4"
        },
        {
            "title": "Введение в фреймворк React",
            "description": "Изучите основы работы с фреймворком React.",
            "duration": "22:00",
            "timestamp": "01.06.2025",
            "author": "Ольга Сидорова",
            "filename": "videos/react_intro.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-web-development.html', 
                           page_title="Основы<br>веб-разработки", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/design')
def course_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6
    
    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы дизайна").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в Figma",
            "description": "Основы работы с Figma и интерфейс программы.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Анна Иванова",
            "filename": "videos/figma-intro.mp4"
        },
        {
            "title": "Создание прототипов",
            "description": "Как создавать интерактивные прототипы в Figma.",
            "duration": "12:00",
            "timestamp": "02.01.2025",
            "author": "Мария Петрова",
            "filename": "videos/figma-prototypes.mp4"
        },
        {
            "title": "Работа с компонентами",
            "description": "Изучите, как создавать и использовать компоненты в Figma.",
            "duration": "15:00",
            "timestamp": "03.01.2025",
            "author": "Алексей Смирнов",
            "filename": "videos/figma-components.mp4"
        },
        {
            "title": "Создание дизайн-системы",
            "description": "Как создать свою дизайн-систему в Figma.",
            "duration": "20:00",
            "timestamp": "04.01.2025",
            "author": "Ирина Кузнецова",
            "filename": "videos/figma-design-system.mp4"
        },
        {
            "title": "Экспорт ресурсов",
            "description": "Научитесь экспортировать ваши ресурсы из Figma.",
            "duration": "8:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Волков",
            "filename": "videos/figma-export.mp4"
        },
        {
            "title": "Советы по дизайну",
            "description": "Полезные советы для улучшения вашего дизайна в Figma.",
            "duration": "10:00",
            "timestamp": "06.01.2025",
            "author": "Ольга Сергеева",
            "filename": "videos/figma-design-tips.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-design.html', 
                           page_title="Основы<br>дизайна", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)

@app.route('/course/javascript')
def course_javascript():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы JavaScript").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в JavaScript",
            "description": "Научитесь основам JavaScript и его синтаксису.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Иван Петров",
            "filename": "videos/javascript-intro.mp4"
        },
        {
            "title": "Работа с переменными",
            "description": "Как использовать переменные в JavaScript.",
            "duration": "8:00",
            "timestamp": "02.01.2025",
            "author": "Анна Смирнова",
            "filename": "videos/javascript-variables.mp4"
        },
        {
            "title": "Условия и циклы",
            "description": "Изучите условия и циклы в JavaScript.",
            "duration": "12:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Кузнецов",
            "filename": "videos/javascript-conditions-loops.mp4"
        },
        {
            "title": "Функции",
            "description": "Как создавать и использовать функции.",
            "duration": "10:00",
            "timestamp": "04.01.2025",
            "author": "Ольга Воронова",
            "filename": "videos/javascript-functions.mp4"
        },
        {
            "title": "Объекты",
            "description": "Изучите основы работы с объектами в JavaScript.",
            "duration": "9:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Федоров",
            "filename": "videos/javascript-objects.mp4"
        },
        {
            "title": "Асинхронное программирование",
            "description": "Как работать с асинхронным кодом.",
            "duration": "11:00",
            "timestamp": "06.01.2025",
            "author": "Елена Соколова",
            "filename": "videos/javascript-async.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-javascript.html', 
                           page_title="Основы<br>JavaScript", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/machine-learning')
def course_machine_learning():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы машинного обучения").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в машинное обучение",
            "description": "Познакомьтесь с основами машинного обучения и его применения.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Иван Иванов",
            "filename": "videos/machine-learning-intro.mp4"
        },
        {
            "title": "Типы машинного обучения",
            "description": "Изучите различные типы машинного обучения: supervised, unsupervised и reinforcement.",
            "duration": "12:00",
            "timestamp": "02.01.2025",
            "author": "Мария Петрова",
            "filename": "videos/machine-learning-types.mp4"
        },
        {
            "title": "Алгоритмы машинного обучения",
            "description": "Узнайте о популярных алгоритмах, таких как линейная регрессия и деревья решений.",
            "duration": "15:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Кузнецов",
            "filename": "videos/machine-learning-algorithms.mp4"
        },
        {
            "title": "Обработка данных",
            "description": "Научитесь обрабатывать и подготавливать данные для обучения моделей.",
            "duration": "11:00",
            "timestamp": "04.01.2025",
            "author": "Ольга Воронова",
            "filename": "videos/machine-learning-data-preprocessing.mp4"
        },
        {
            "title": "Оценка моделей",
            "description": "Как оценивать и улучшать производительность моделей машинного обучения.",
            "duration": "14:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Федоров",
            "filename": "videos/machine-learning-model-evaluation.mp4"
        },
        {
            "title": "Супервизорное обучение",
            "description": "Изучите основные принципы супервизорного обучения.",
            "duration": "13:00",
            "timestamp": "06.01.2025",
            "author": "Анна Смирнова",
            "filename": "videos/machine-learning-supervised-learning.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-machine-learning.html', 
                           page_title="Основы<br>vашинного обучения", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/mobile-development')
def course_mobile_development():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Разработка мобильных приложений").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в разработку мобильных приложений",
            "description": "Создайте свое первое мобильное приложение на React Native.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Алексей Смирнов",
            "filename": "videos/mobile-development-intro.mp4"
        },
        {
            "title": "Установка окружения",
            "description": "Научитесь устанавливать необходимые инструменты для разработки.",
            "duration": "12:00",
            "timestamp": "02.01.2025",
            "author": "Ирина Петрова",
            "filename": "videos/mobile-development-setup.mp4"
        },
        {
            "title": "Создание простого приложения",
            "description": "Создайте простое приложение с использованием компонентов React Native.",
            "duration": "15:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Кузнецов",
            "filename": "videos/mobile-development-simple-app.mp4"
        },
        {
            "title": "Работа с API",
            "description": "Научитесь взаимодействовать с API для получения данных.",
            "duration": "14:00",
            "timestamp": "04.01.2025",
            "author": "Ольга Воронова",
            "filename": "videos/mobile-development-api.mp4"
        },
        {
            "title": "Публикация приложения",
            "description": "Узнайте, как опубликовать ваше приложение в App Store и Google Play.",
            "duration": "13:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Федоров",
            "filename": "videos/mobile-development-publishing.mp4"
        },
        {
            "title": "Тестирование приложения",
            "description": "Изучите методы тестирования мобильных приложений.",
            "duration": "11:00",
            "timestamp": "06.01.2025",
            "author": "Анна Смирнова",
            "filename": "videos/mobile-development-testing.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-mobile-development.html', 
                           page_title="Разработка<br>мобильных приложений", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/cybersecurity')
def course_cybersecurity():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы кибербезопасности").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в кибербезопасности",
            "description": "Узнайте, как защитить свои данные и устройства.",
            "duration": "8:00",
            "timestamp": "01.01.2025",
            "author": "Алексей Смирнов",
            "filename": "cybersecurity_intro.mp4"
        },
        {
            "title": "Основы сетевой безопасности",
            "description": "Обзор основных принципов сетевой безопасности.",
            "duration": "10:00",
            "timestamp": "02.01.2025",
            "author": "Мария Иванова",
            "filename": "network_security.mp4"
        },
        {
            "title": "Защита от вредоносного ПО",
            "description": "Как защитить свои устройства от вирусов и вредоносных программ.",
            "duration": "12:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Петров",
            "filename": "malware_protection.mp4"
        },
        {
            "title": "Социальная инженерия",
            "description": "Изучите методы социальной инженерии и как от них защититься.",
            "duration": "9:00",
            "timestamp": "04.01.2025",
            "author": "Ольга Кузнецова",
            "filename": "social_engineering.mp4"
        },
        {
            "title": "Безопасность мобильных устройств",
            "description": "Как защитить свои мобильные устройства от угроз.",
            "duration": "11:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Сидоров",
            "filename": "mobile_security.mp4"
        },
        {
            "title": "Шифрование данных",
            "description": "Основы шифрования и его важность для безопасности.",
            "duration": "15:00",
            "timestamp": "06.01.2025",
            "author": "Анна Сергеева",
            "filename": "data_encryption.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-cybersecurity.html', 
                           page_title="Основы<br>кибербезопасности", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/database')
def course_database():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы работы с базами данных").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в базы данных",
            "description": "Основы работы с базами данных.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Иван Иванов",
            "filename": "introduction_to_databases.mp4"
        },
        {
            "title": "SQL для начинающих",
            "description": "Изучите основы SQL.",
            "duration": "12:00",
            "timestamp": "02.01.2025",
            "author": "Мария Петрова",
            "filename": "sql_for_beginners.mp4"
        },
        {
            "title": "Проектирование баз данных",
            "description": "Как проектировать эффективные базы данных.",
            "duration": "15:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Сидоров",
            "filename": "database_design.mp4"
        },
        {
            "title": "Оптимизация запросов",
            "description": "Советы по оптимизации SQL-запросов.",
            "duration": "14:00",
            "timestamp": "04.01.2025",
            "author": "Ольга Кузнецова",
            "filename": "query_optimization.mp4"
        },
        {
            "title": "Работа с NoSQL",
            "description": "Основы работы с NoSQL базами данных.",
            "duration": "13:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Смирнов",
            "filename": "working_with_nosql.mp4"
        },
        {
            "title": "Безопасность баз данных",
            "description": "Как защитить свои базы данных.",
            "duration": "16:00",
            "timestamp": "06.01.2025",
            "author": "Анна Сергеева",
            "filename": "database_security.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-database.html', 
                           page_title="Основы работы<br>с базами данных", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/ux-ui-design')
def course_ux_ui_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="UX/UI Дизайн").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в UX/UI дизайн",
            "description": "В этом видео мы познакомимся с основами UX/UI дизайна и его значением.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Анастасия Смирнова",
            "filename": "videos/ux-ui-design-intro.mp4"
        },
        {
            "title": "Исследование пользователей",
            "description": "Научитесь проводить исследования для понимания потребностей пользователей.",
            "duration": "12:00",
            "timestamp": "02.01.2025",
            "author": "Олег Петров",
            "filename": "videos/ux-ui-design-research.mp4"
        },
        {
            "title": "Создание прототипов",
            "description": "Изучите методы создания прототипов для тестирования идей.",
            "duration": "15:00",
            "timestamp": "03.01.2025",
            "author": "Ирина Коваленко",
            "filename": "videos/ux-ui-design-prototyping.mp4"
        },
        {
            "title": "Дизайн интерфейса",
            "description": "Как создавать привлекательные и функциональные интерфейсы.",
            "duration": "11:00",
            "timestamp": "04.01.2025",
            "author": "Максим Иванов",
            "filename": "videos/ux-ui-design-interface.mp4"
        },
        {
            "title": "Тестирование пользовательского опыта",
            "description": "Научитесь проводить тестирование для улучшения дизайна.",
            "duration": "13:00",
            "timestamp": "05.01.2025",
            "author": "Светлана Фролова",
            "filename": "videos/ux-ui-design-testing.mp4"
        },
        {
            "title": "Продвинутые техники UX/UI",
            "description": "Изучите более сложные техники и подходы в UX/UI дизайне.",
            "duration": "14:00",
            "timestamp": "06.01.2025",
            "author": "Алексей Романов",
            "filename": "videos/ux-ui-design-advanced.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-ux-ui-design.html', 
                           page_title="Основы<br>UX/UI дизайна", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/devops')
def course_devops():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы DevOps").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в DevOps",
            "description": "Изучите практики DevOps и автоматизацию процессов разработки.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Алексей Смирнов",
            "filename": "videos/devops-intro.mp4"
        },
        {
            "title": "CI/CD в DevOps",
            "description": "Как настроить непрерывную интеграцию и доставку.",
            "duration": "12:00",
            "timestamp": "02.01.2025",
            "author": "Мария Петрова",
            "filename": "videos/devops-ci-cd.mp4"
        },
        {
            "title": "Контейнеризация с Docker",
            "description": "Основы работы с Docker и контейнерами.",
            "duration": "15:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Кузнецов",
            "filename": "videos/devops-docker.mp4"
        },
        {
            "title": "Мониторинг и логирование",
            "description": "Как эффективно мониторить и логировать приложения.",
            "duration": "8:00",
            "timestamp": "04.01.2025",
            "author": "Анна Иванова",
            "filename": "videos/devops-monitoring-logging.mp4"
        },
        {
            "title": "Управление конфигурацией",
            "description": "Изучите инструменты управления конфигурацией.",
            "duration": "10:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Федоров",
            "filename": "videos/devops-configuration-management.mp4"
        },
        {
            "title": "Автоматизация с Ansible",
            "description": "Изучите, как использовать Ansible для автоматизации.",
            "duration": "14:00",
            "timestamp": "06.01.2025",
            "author": "Ирина Сидорова",
            "filename": "videos/devops-ansible.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-devops.html', 
                           page_title="Основы<br>DevOps", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/graphic-design')
def course_graphic_design():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы графического дизайна").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в графический дизайн",
            "description": "Научитесь основам графического дизайна и работе с Adobe Photoshop.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Иван Петров",
            "filename": "videos/graphic-design-intro.mp4"
        },
        {
            "title": "Работа с цветом",
            "description": "Как использовать цвет в графическом дизайне.",
            "duration": "8:00",
            "timestamp": "02.01.2025",
            "author": "Анна Смирнова",
            "filename": "videos/graphic-design-color.mp4"
        },
        {
            "title": "Основы композиции",
            "description": "Изучите правила композиции в дизайне.",
            "duration": "12:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Кузнецов",
            "filename": "videos/graphic-design-composition.mp4"
        },
        {
            "title": "Создание логотипов",
            "description": "Как создать эффективный логотип для бренда.",
            "duration": "10:00",
            "timestamp": "04.01.2025",
            "author": "Ольга Воронова",
            "filename": "videos/graphic-design-logos.mp4"
        },
        {
            "title": "Работа с типографикой",
            "description": "Изучите основы работы с шрифтами в дизайне.",
            "duration": "9:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Федоров",
            "filename": "videos/graphic-design-typography.mp4"
        },
        {
            "title": "Брендинг",
            "description": "Как создать и развивать бренд.",
            "duration": "11:00",
            "timestamp": "06.01.2025",
            "author": "Елена Соколова",
            "filename": "videos/graphic-design-branding.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-graphic-design.html', 
                           page_title="Основы<br>графического дизайна", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


@app.route('/course/digital-marketing')
def course_digital_marketing():
    if 'username' not in session:
        flash('Вы должны быть авторизованы для просмотра видео.', 'error')
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из URL, по умолчанию 1
    per_page = 6  # Количество видео на странице

    # Получаем видео из базы данных
    videos_from_db = Video.query.filter_by(course="Основы цифрового маркетинга").all()

    # Вручную добавленные видео
    manual_videos = [
        {
            "title": "Введение в цифровой маркетинг",
            "description": "Изучите стратегии и инструменты цифрового маркетинга.",
            "duration": "10:00",
            "timestamp": "01.01.2025",
            "author": "Алексей Смирнов",
            "filename": "videos/digital-marketing-intro.mp4"
        },
        {
            "title": "SEO основы",
            "description": "Научитесь оптимизировать сайты для поисковых систем.",
            "duration": "12:00",
            "timestamp": "02.01.2025",
            "author": "Мария Петрова",
            "filename": "videos/digital-marketing-seo.mp4"
        },
        {
            "title": "Контент-маркетинг",
            "description": "Создание и продвижение контента для привлечения клиентов.",
            "duration": "15:00",
            "timestamp": "03.01.2025",
            "author": "Сергей Кузнецов",
            "filename": "videos/digital-marketing-content.mp4"
        },
        {
            "title": "Социальные сети",
            "description": "Как использовать социальные сети для бизнеса.",
            "duration": "10:00",
            "timestamp": "04.01.2025",
            "author": "Анна Иванова",
            "filename": "videos/digital-marketing-social-media.mp4"
        },
        {
            "title": "Email-маркетинг",
            "description": "Создание эффективных email-кампаний.",
            "duration": "8:00",
            "timestamp": "05.01.2025",
            "author": "Дмитрий Федоров",
            "filename": "videos/digital-marketing-email.mp4"
        },
        {
            "title": "Аналитика в цифровом маркетинге",
            "description": "Как использовать аналитику для улучшения маркетинговых стратегий.",
            "duration": "14:00",
            "timestamp": "06.01.2025",
            "author": "Ирина Сидорова",
            "filename": "videos/digital-marketing-analytics.mp4"
        }
    ]

    # Объединяем видео из базы данных и вручную добавленные видео
    all_videos = videos_from_db + manual_videos

    # Реализация пагинации
    total_videos = len(all_videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_videos = all_videos[start:end]

    return render_template('course-digital-marketing.html', 
                           page_title="Основы<br>цифрового маркетинга", 
                           videos=paginated_videos, 
                           pagination={'page': page, 'total_pages': total_pages}, 
                           ROLE_TRANSLATIONS=ROLE_TRANSLATIONS)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov', 'mkv'}

if __name__ == '__main__':
    app.run(debug=True)